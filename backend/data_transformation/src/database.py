import os
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql
from psycopg2.extras import execute_values


BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")
DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set. Add it to backend/.env.")

    return psycopg2.connect(DATABASE_URL)


def init_ads_cleaned_db(conn):
    cursor = conn.cursor()
    cursor.execute("SET search_path TO public")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.ads_cleaned (
            hash_id VARCHAR(64) PRIMARY KEY,
            title VARCHAR(500),
            img_url VARCHAR(1000),
            link VARCHAR(1000),
            neighbourhood VARCHAR(255),
            type_of_estate VARCHAR(100),
            total_price_eur DECIMAL(10, 2),
            price_m2_eur DECIMAL(10, 2),
            price_m2_bgn DECIMAL(10, 2),
            size_m2 DECIMAL(10, 2),
            nr_of_rooms SMALLINT,
            description TEXT,
            floor SMALLINT,
            akt16 BOOL,
            energy_class VARCHAR(255),
            potreblenie VARCHAR(255),
            broker_commision BOOL,
            additional_notes VARCHAR(1000),
            extras VARCHAR(500)
        )
    """)
    cursor.execute("TRUNCATE TABLE public.ads_cleaned")
    conn.commit()
    print("Prepared ads_cleaned table!")


def load_data_into_ads_cleaned(cleaned_dict, conn):
    print("Loading data into ads_cleaned...\n")
    rows = [
        (
            clean_value(item.get("hash_id")),
            clean_value(item.get("title")),
            clean_value(item.get("img_url")),
            clean_value(item.get("link")),
            clean_value(item.get("neighbourhood")),
            clean_value(item.get("type_of_estate")),
            clean_value(item.get("total_price_eur")),
            clean_value(item.get("price_m2_eur")),
            clean_value(item.get("price_m2_bgn")),
            clean_value(item.get("size_m2")),
            clean_value(item.get("nr_of_rooms")),
            clean_value(item.get("description")),
            clean_value(item.get("floor")),
            clean_value(item.get("akt16")),
            clean_value(item.get("energy_class")),
            clean_value(item.get("potreblenie")),
            clean_value(item.get("broker_commision")),
            clean_value(item.get("additional_notes")),
            clean_value(item.get("extras")),
        )
        for item in cleaned_dict
    ]

    if not rows:
        print("No rows to load into ads_cleaned.\n")
        return

    query = """
        INSERT INTO public.ads_cleaned (
            hash_id,
            title,
            img_url,
            link,
            neighbourhood,
            type_of_estate,
            total_price_eur,
            price_m2_eur,
            price_m2_bgn,
            size_m2,
            nr_of_rooms,
            description,
            floor,
            akt16,
            energy_class,
            potreblenie,
            broker_commision,
            additional_notes,
            extras
        ) VALUES %s
    """

    cursor = conn.cursor()
    execute_values(cursor, query, rows, page_size=1000)
    conn.commit()
    print("Finished loading data into ads_cleaned!\n")


def query_entire_database_table(table_name: str, conn) -> list[dict]:
    cursor = conn.cursor()
    cursor.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier(table_name)))
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()

    return [dict(zip(columns, row)) for row in rows]


def fetch_metadata_from_rdbms(candidate_ids: list):
    if not candidate_ids:
        return {}

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT hash_id, link, img_url
        FROM ads_cleaned
        WHERE hash_id = ANY(%s)
        """,
        (candidate_ids,),
    )
    rows = cursor.fetchall()
    conn.close()

    return {
        row[0]: {
            "link": row[1],
            "img_url": row[2],
        }
        for row in rows
    }


def clean_value(value):
    if value is pd.NA or value is None:
        return None

    if isinstance(value, (np.generic,)):
        value = value.item()

    if pd.isna(value):
        return None

    if isinstance(value, float) and not np.isfinite(value):
        return None

    return value
