import sys
from pathlib import Path


# rents/ads_appartments_rent/ -> rents -> data_transformation -> backend
BACKEND_DIR = Path(__file__).resolve().parents[3]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from data_transformation.rents.ads_appartments_rent.src.database import (
    get_connection,
    init_ads_appartments_rent_db,
    populate_ads_appartments_rent,
)


def main():
    conn = get_connection()
    try:
        init_ads_appartments_rent_db(conn)
        populate_ads_appartments_rent(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
