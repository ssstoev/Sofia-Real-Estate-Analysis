import sys
from pathlib import Path


# sales/ads_appartments/ -> sales -> data_transformation -> backend
BACKEND_DIR = Path(__file__).resolve().parents[3]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from data_transformation.sales.ads_appartments.src.database import (
    get_connection,
    init_ads_appartments_db,
    populate_ads_appartments,
)


def main():
    conn = get_connection()
    try:
        init_ads_appartments_db(conn)
        populate_ads_appartments(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
