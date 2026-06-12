import psycopg2
import datetime as dt
import os
from dotenv import load_dotenv

load_dotenv()

# _DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ads_storage.db')
DATABASE_URL = os.getenv("DATABASE_URL")

def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Create the table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ads_raw (
            hash_id TEXT PRIMARY KEY,
            title TEXT,
            link TEXT,
            img_url TEXT,
            total_price_eur TEXT,
            price_m2_eur TEXT,
            price_m2_bgn TEXT,
            size_m2 TEXT,
            description TEXT,
            floor TEXT,
            akt16 TEXT,
            energy_class TEXT,
            potreblenie TEXT,
            broker_commision TEXT,
            additional_notes TEXT,
            status TEXT DEFAULT 'pending',
            extras TEXT,
            scraped_at TIMESTAMP,
            last_updated TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def insert_ad(cursor, ad_data):
    '''Initial insert of ad into the database'''
    for hash_id, info in ad_data.items():
        # 1. Prepare the Query
        time = dt.datetime.now()
        query = """
            INSERT INTO ads_raw (
                hash_id, title, link, status, scraped_at, last_updated
            ) VALUES (%s, %s, %s, 'pending', %s, %s)
            ON CONFLICT (hash_id) DO NOTHING
        """
        
        # 2. Execute
        cursor.execute(query, (
            hash_id,
            info.get('ad_title'),
            info.get('link_to_ad'),
            time, 
            time
        ))

        # print(f"Successfully inserted item {hash_id}")

def fetch_pending_ads(conn, batch_size=100):
    cursor = conn.cursor()
    query = '''
    SELECT * FROM ads_raw WHERE status IN ('pending', 'processing') LIMIT %s
    '''
    cursor.execute(query, (batch_size,))

    pending = cursor.fetchall()
    pending_list = [{"hash_id": row[0], "link": row[1]} for row in pending]

    # Or if you want column names from cursor.description
    columns = [desc[0] for desc in cursor.description]
    pending_list = [dict(zip(columns, row)) for row in pending]
    
    cursor.executemany("""
        UPDATE ads_raw
        SET status = 'processing'
        WHERE hash_id = %s
    """, [(ad["hash_id"],) for ad in pending_list])

    conn.commit()
    return pending_list

def update_records(conn, updates):
    cursor = conn.cursor()

    for update in updates:
        cursor.execute("""
            UPDATE ads_raw 
            SET description = %s, price_m2_eur = %s, price_m2_bgn = %s,
                       size_m2 = %s, floor = %s, akt16 = %s, energy_class = %s,
                       potreblenie = %s, broker_commision = %s, additional_notes = %s,
                       img_url = %s, extras = %s, total_price_eur = %s,
                       status = 'done', last_updated = %s
            WHERE hash_id = %s
        """, 
            (update["description"], update["price_m2_eur"], update["price_m2_bgn"],
              update["size_m2"], update["floor"], update["akt16"], update["energy_class"],
               update["potreblenie"], update["broker_commision"], update["additional_notes"],
               update["img_url"], update["extras"], update["total_price_eur"],
               dt.datetime.now(), update["hash_id"])
        )
    conn.commit()
    return None

# We missed extracting data for 1 column so we will backfill it without scraping everything again from scratch

def create_missing_col(table_name: str, new_db_col_name: str, dtype: str = "TEXT", db_path=DATABASE_URL): 
    '''Add new column to a table in the RDBMS'''
    conn = psycopg2.connect(db_path)
    cursor = conn.cursor()
    query_create_col = f'''
        ALTER TABLE {table_name} ADD COLUMN {new_db_col_name} {dtype}
    '''
    cursor.execute(query_create_col)
    conn.commit()
    conn.close()

def fetch_missing_rows(conn, col_to_check: str, batch_size=20):
    '''This funciton fetches the rows where the a specified column is NULL'''

    cursor = conn.cursor()
    query = f'''
    SELECT hash_id, link FROM ads_raw WHERE {col_to_check} IS NULL LIMIT %s
    '''
    cursor.execute(query, (batch_size,))

    result = cursor.fetchall()
    result_list = [{"hash_id": row[0], "link": row[1]} for row in result]

    return result_list

def add_missing_col_information(conn, 
                                db_col_to_update: str, 
                                updates: dict, 
                                values_to_update_with: str):
    
    '''Add the additional scraped info to the col'''
    cursor = conn.cursor()

    query_update_col = f'''
        UPDATE ads_raw
        SET {db_col_to_update} = %s
        WHERE hash_id = %s    
    '''

    for update in updates:
        cursor.execute(query_update_col, 
                       (update[f"{values_to_update_with}"], update["hash_id"]))
    
    conn.commit()
    conn.close()