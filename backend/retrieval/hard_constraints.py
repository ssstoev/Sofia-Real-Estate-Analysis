import re

from data_transformation.src.database import get_connection

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

def extract_hard_constraints(query: str) -> dict:
    '''Extract the following hard constraints from a user query:
       1. Price
       2. Price p/m2
       3. Area of the estate
       4. The type of appartment (room numbers)
    '''
    query = query.lower()

    # Price: match 5-7 digit totals followed by optional currency, but NOT followed by /m2
    price_regex = r'(\d{5,7})\s*(€|eur|лв|bgn)?(?!\s*/?\s*(?:m2|м2))'
    price_m2_regex = r'(\d{3,5})\s*(€|eur|лв|bgn)?\s*/\s*(m2|м2)'
    floor_regex = r'(\d+)(?:-?(?:ви|ри|ти|и))?\s*(?:(?:от|/)\s*(\d+))?\s*(етаж|floor)'
    size_regex = r'(\d+(?:[\.,]\d+)?)\s*(кв\.?м?|m2|sqm)'
    property_type_regex = r'(едностаен|двустаен|тристаен|многостаен|гарсониера|едностайни|двустайни|тристайни|многостайни)'

    price_match = re.search(price_regex, query)
    price_m2_match = re.search(price_m2_regex, query)
    floor_match = re.search(floor_regex, query)
    size_match = re.search(size_regex, query)
    property_type_match = re.search(property_type_regex, query)

    constraints_dict = {
        'nr_of_rooms': PROPERTY_TYPE_ROOMS.get(property_type_match.group(1)) if property_type_match else None,
        'total_price_eur': int(price_match.group(1).replace(' ', '').replace(',', '')) if price_match else None,
        'price_m2_eur': int(price_m2_match.group(1)) if price_m2_match else None,
        'floor': int(floor_match.group(1)) if floor_match else None,
        'size_m2': float(size_match.group(1).replace(',', '.')) if size_match else None,
    }

    return constraints_dict

# WIP: build upper & lower bounds for fields like price/size etc. and add a +10% range for prices/sizes
# WIP: E.g. a query for a 40 m2 place should include up to 45 m2
# WIP: create classes for types for constraints_dict & the hahs_ids list
# WIP: Add neighbourhood to hard constraints
def filter_db_on_hard_constraints(constraints_dict: dict) -> list:
    '''Receives a constraints dictionary and returns all hash_ids which fall in the criteria'''

    conn = get_connection()
    base_query  = "SELECT hash_id FROM ads_cleaned"
    cursor = conn.cursor()
    # build a dynamic query
    where_clauses = []
    params = {}

    # Exact match fields
    exact_fields = ["nr_of_rooms", "floor"]

    for field in exact_fields:
        if constraints_dict.get(field) is not None:
            where_clauses.append(f"{field} = %({field})s")
            params[field] = constraints_dict[field]

    # Upper bound fields — user wants at most this value
    lte_fields = ["total_price_eur", "size_m2", "price_m2_eur"]
    for field in lte_fields:
        if constraints_dict.get(field) is not None:
            where_clauses.append(f"{field} <= %({field})s")
            params[field] = constraints_dict[field]

    if not where_clauses:
        return []
    
    print(where_clauses)
    full_query = f"{base_query} WHERE {' AND '.join(where_clauses)}"
    print(full_query)

    cursor.execute(full_query, params)
    results = cursor.fetchall()
    conn.close()
    return [row[0] for row in results]