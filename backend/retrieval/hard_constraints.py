import re
# from data_transformation.ads_cleaned.src.database import get_connection
import json
from openai import OpenAI
from dotenv import load_dotenv
import os
from pathlib import Path

from data_transformation.ads_appartments.src.database import get_connection

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

PROPERTY_TYPE_ROOMS = {
    'гарсониера': 1,
    'едностаен': 1,
    'едностайни': 1,
    'двустаен': 2,
    'двустайни': 2,
    'тристаен': 3,
    'тристайни': 3,
    'многостаен': 4,
    'многостайни':4
}

EXTRACT_HARD_CONSTRAINTS_PROMPT = '''
    You are a precise real estate query parser for the Bulgarian property market.

    Your task is to extract hard constraints from a user query and return two valid PostgreSQL SELECT queries against the table `ads_cleaned`, returned as a JSON object.

    COLUMN NAMES:
    - type_of_estate (varchar)
    - nr_of_rooms (integer)
    - price_m2_eur (float)
    - total_price_eur (float)
    - size_m2 (float)
    - neighbourhood (text, in Bulgarian Cyrillic)
    - is_furnished (boolean)
    - near_public_transport (boolean)
    - is_first_floor (boolean)
    - is_last_floor (boolean)

    EXTRACTION RULES:

    **Type of estate:**
    - default is type_of_estate == "жилище"
    - Also possible to search for "къща", "офис", "парцел", "магазин", "гараж"

    **Rooms:**
    - "двустаен" → 2, "тристаен" → 3, "четиристаен" → 4, "едностаен/студио" → 1
    - Also handle numeric mentions: "3 стаи", "три стаи"

    **Price per m²** (price_m2_eur):
    - Phrases like "до X евро на квадрат", "X €/кв.м", "X евро/м2", "на квадратен метър"
    - "до" / "под" → <=
    - "над" / "поне" → >=
    - Exact value → =

    **Total price** (total_price_eur):
    - Phrases like "до X евро", "на цена до X", "бюджет X евро"
    - "до" / "под" → <=
    - "над" / "поне" → >=
    - Exact value → =

    **Size** (size_m2):
    - "X кв.м", "X м2", "X квадрата", "X квадратни метра"
    - "поне X" / "над X" → >=
    - "до X" / "под X" → <=
    - Exact value → =

    **Neighbourhood:**
    - Must be inserted in Bulgarian Cyrillic exactly as commonly written
    - Normalize aliases: "Студентски град" → 'Студентски', etc.
    - If multiple neighbourhoods mentioned, use: neighbourhood IN ('X', 'Y')
    - Careful with neighbourhoods which have multiple sub-regions, e.g. "Люлин 1, 2, ... 10", "Младост 1, 2...", "Дружба 1, 2". 
    - In cases where the number is not mentioned search for all results which contain "Люлин"/"Младост"/"Дружба" in neighbourhood

    **Booleans:**
    - is_furnished: "обзаведен", "с обзавеждане" → true
    - near_public_transport: "до метро", "до спирка", "близо до метро" → true
    - is_first_floor: "първи етаж", "на първия етаж" → true
    - is_last_floor: "последен етаж", "таван" → true
    - Only add boolean conditions if explicitly mentioned — never assume

    QUERY RULES:
    - Always start with: SELECT * FROM ads_cleaned
    - Only add WHERE clauses for fields explicitly mentioned in the query
    - Chain conditions with AND
    - Never use OR unless the user mentions multiple acceptable values for the same field
    - Never add LIMIT unless the user specifies a number of results
    - Booleans, nr_of_rooms, and neighbourhood are never buffered

    BUFFER RULES (expanded_query only):
    - Apply a 10% tolerance buffer exclusively to numeric upper bounds (<=) on price_m2, total_price, and size_m2
    - "до 1000 евро на квадрат" → exact: price_m2 <= 1000 / expanded: price_m2 <= 1100
    - "до 100000 евро" → exact: total_price <= 100000 / expanded: total_price <= 110000
    - "до 40 кв.м" → exact: size_m2 <= 40 / expanded: size_m2 <= 44
    - Do NOT buffer >= constraints — if the user wants at least X, do not lower that threshold
    - Do NOT buffer exact = constraints on numeric fields
    - If no bufferable constraints exist, expanded_query must be identical to exact_query

    OUTPUT FORMAT:
    Return only a raw JSON object, no explanation, no markdown, no backticks.

    {
        "exact_query": "SELECT * FROM ads_cleaned WHERE ...",
        "expanded_query": "SELECT * FROM ads_cleaned WHERE ..."
    }

    Examples:

    Input: "Покажи ми тристайни жилища в Лозенец до 3000 евро на квадрат, обзаведени и близо до метро."
    Output:
    {
        "exact_query": "SELECT * FROM ads_cleaned WHERE type_of_estate = 'жилище' AND nr_of_rooms = 3 AND price_m2_eur <= 3000 AND neighbourhood = 'Лозенец' AND is_furnished = true AND near_public_transport = true;",
        "expanded_query": "SELECT * FROM ads_cleaned WHERE type_of_estate = 'жилище' AND nr_of_rooms = 3 AND price_m2_eur <= 3300 AND neighbourhood = 'Лозенец' AND is_furnished = true AND near_public_transport = true;"
    }

    Input: "Искам апартамент над 80 кв.м. в Младост до 150000 евро."
    Output:
    {
        "exact_query": "SELECT * FROM ads_cleaned WHERE type_of_estate = 'жилище' AND size_m2 >= 80 AND neighbourhood = 'Младост' AND total_price <= 150000;",
        "expanded_query": "SELECT * FROM ads_cleaned WHERE type_of_estate = 'жилище' AND size_m2 >= 80 AND neighbourhood = 'Младост' AND total_price <= 165000;"
    }
    '''

client = OpenAI()

def generate_sql_query(user_query):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": EXTRACT_HARD_CONSTRAINTS_PROMPT},
            {"role": "user", "content": user_query}
        ]
    )
    result = json.loads(response.choices[0].message.content)
    print(f"[EXACT QUERY]: {result['exact_query']}")
    print(f"[EXPANDED QUERY]: {result['expanded_query']}")

    return result

def filter_db_on_hard_constraints(user_query: str, threshold: int = 5) -> dict:
    '''Receives a user query, generates SQL, queries the db and returns matching results.
    Falls back to expanded query if exact results are below threshold.'''

    queries = generate_sql_query(user_query)  
    
    conn = get_connection()
    cursor = conn.cursor() 
    
    cursor.execute(queries["exact_query"])
    column_names = [desc[0] for desc in cursor.description]
    exact_results = [dict(zip(column_names, row)) for row in cursor.fetchall()]
    
    if len(exact_results) >= threshold:
        conn.close()
        return {"results": exact_results, "expanded": False}
    
    cursor.execute(queries["expanded_query"])
    column_names = [desc[0] for desc in cursor.description]
    expanded_results = [dict(zip(column_names, row)) for row in cursor.fetchall()]
    
    conn.close()
    return {"results": expanded_results, "expanded": True}

# def extract_hard_constraints(query: str) -> dict:
#     '''Extract the following hard constraints from a user query:
#        1. Price
#        2. Price p/m2
#        3. Area of the estate
#        4. The type of appartment (room numbers)
#     '''
#     query = query.lower()

#     # Price: match 5-7 digit totals followed by optional currency, but NOT followed by /m2
#     price_regex = r'(\d{5,7})\s*(€|eur|лв|bgn)?(?!\s*/?\s*(?:m2|м2))'
#     price_m2_regex = r'(\d{3,5})\s*(€|eur|лв|bgn|евро)?\s*/\s*(m2|м2|кв/м|кв./м)'
#     floor_regex = r'(\d+)(?:-?(?:ви|ри|ти|и))?\s*(?:(?:от|/)\s*(\d+))?\s*(етаж|floor)'
#     size_regex = r'(\d+(?:[\.,]\d+)?)\s*(кв\.?м?|m2|sqm)'
#     property_type_regex = r'(едностаен|двустаен|тристаен|многостаен|гарсониера|едностайни|двустайни|тристайни|многостайни)'

#     price_match = re.search(price_regex, query)
#     price_m2_match = re.search(price_m2_regex, query)
#     floor_match = re.search(floor_regex, query)
#     size_match = re.search(size_regex, query)
#     property_type_match = re.search(property_type_regex, query)

#     constraints_dict = {
#         'nr_of_rooms': PROPERTY_TYPE_ROOMS.get(property_type_match.group(1)) if property_type_match else None,
#         'total_price_eur': int(price_match.group(1).replace(' ', '').replace(',', '')) if price_match else None,
#         'price_m2_eur': int(price_m2_match.group(1)) if price_m2_match else None,
#         'floor': int(floor_match.group(1)) if floor_match else None,
#         'size_m2': float(size_match.group(1).replace(',', '.')) if size_match else None,
#     }

#     return constraints_dict

# # WIP: build upper & lower bounds for fields like price/size etc. and add a +10% range for prices/sizes
# # WIP: E.g. a query for a 40 m2 place should include up to 45 m2
# # WIP: create classes for types for constraints_dict & the hahs_ids list
# # WIP: Add neighbourhood to hard constraints
# def filter_db_on_hard_constraints(constraints_dict: dict) -> list:
#     '''Receives a constraints dictionary and returns results which match the criteria'''

#     conn = get_connection()
#     base_query  = "SELECT hash_id, title, link, img_url, total_price_eur, size_m2, neighbourhood FROM ads_appartments"
#     cursor = conn.cursor()
#     # build a dynamic query
#     where_clauses = []
#     params = {}

#     # Exact match fields
#     exact_fields = ["nr_of_rooms", "floor"]

#     for field in exact_fields:
#         if constraints_dict.get(field) is not None:
#             where_clauses.append(f"{field} = %({field})s")
#             params[field] = constraints_dict[field]

#     # Upper bound fields — user wants at most this value
#     lte_fields = ["total_price_eur", "size_m2", "price_m2_eur"]
#     for field in lte_fields:
#         if constraints_dict.get(field) is not None:
#             where_clauses.append(f"{field} <= %({field})s")
#             params[field] = constraints_dict[field]

#     if not where_clauses:
#         return []
    
#     # print(where_clauses)
#     full_query = f"{base_query} WHERE {' AND '.join(where_clauses)}"
#     print(full_query)
#     cursor.execute(full_query, params)
#     column_names = [desc[0] for desc in cursor.description]
#     results = cursor.fetchall()
#     print(results)
#     conn.close()
#     return [dict(zip(column_names, row)) for row in results]
