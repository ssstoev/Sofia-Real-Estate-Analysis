import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


# rents/ads_appartments_rent/src/ -> ads_appartments_rent -> rents -> data_transformation -> backend
BACKEND_DIR = Path(__file__).resolve().parents[4]
load_dotenv(BACKEND_DIR / ".env")
DATABASE_URL = os.getenv("DATABASE_URL")

EXCLUDE_TERMS = ["Земеделски имот", "Сграда", "Склад", "Промишлен имот", "Офис", "Парцел", "Гараж", "Паркомясто", "Магазин", "Къща"]


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set. Add it to backend/.env.")
    return psycopg2.connect(DATABASE_URL)


def init_ads_appartments_rent_db(conn):
    cursor = conn.cursor()
    cursor.execute("SET search_path TO public")
    cursor.execute("DROP TABLE IF EXISTS public.ads_appartments_rent")
    cursor.execute("""
        CREATE TABLE public.ads_appartments_rent (
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
            building_total_floors SMALLINT,
            is_first_floor BOOL,
            is_last_floor BOOL,
            akt16 BOOL,
            energy_class VARCHAR(255),
            potreblenie VARCHAR(255),
            broker_commision BOOL,
            additional_notes VARCHAR(1000),
            is_furnished BOOL,
            near_public_transport BOOL,
            extras VARCHAR(500)
        )
    """)
    conn.commit()
    print("Prepared ads_appartments_rent table!")


def populate_ads_appartments_rent(conn) -> int:
    """Copy rows from ads_cleaned_rents into ads_appartments_rent, excluding non-apartment types."""
    pattern = "|".join(EXCLUDE_TERMS)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO public.ads_appartments_rent
        SELECT * FROM public.ads_cleaned_rents
        WHERE title !~* %s
        """,
        (pattern,),
    )
    count = cursor.rowcount
    conn.commit()
    print(f"Loaded {count} rows into ads_appartments_rent!")
    return count
