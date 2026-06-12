import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from data_transformation.src.clean import clean_data
from data_transformation.src.database import (
    get_connection,
    init_ads_cleaned_db,
    load_data_into_ads_cleaned,
)
from data_transformation.src.transform import transform_data


def main():
    conn = get_connection()
    try:
        init_ads_cleaned_db(conn)
        df = clean_data(conn)
        transformed_data = transform_data(df)
        load_data_into_ads_cleaned(transformed_data, conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
