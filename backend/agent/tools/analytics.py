# tools/analytics.py
import json

from psycopg2.extras import RealDictCursor
from data_transformation.src.database import get_connection

async def get_stats(metric: str, filters: dict = None):
    if isinstance(filters, str):
        try:
            filters = json.loads(filters)
        except (json.JSONDecodeError, ValueError):
            filters = None

    query_map = {
        "avg_price": "SELECT AVG(total_price_eur) as value FROM ads_cleaned",
        "median_price": "SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_price_eur) as value FROM ads_cleaned",
        "avg_price_sqm": "SELECT AVG(price_m2_eur) as value FROM ads_cleaned",
        "listing_count": "SELECT COUNT(*) as value FROM ads_cleaned",
        "min_price": "SELECT MIN(total_price_eur) as value from ads_cleaned",
        "max_price": "SELECT MAX(total_price_eur) as value from ads_cleaned",
        "min_price_sqm": "SELECT MIN(price_m2_eur) as value from ads_cleaned",
        "max_price_sqm": "SELECT MAX(price_m2_eur) as value from ads_cleaned"
    }
    
    if metric not in query_map:
        return {"error": f"Unknown metric: {metric}"}
    
    query = query_map[metric]
    
    conditions = []
    params = {}

    if filters:
        allowed = {"neighbourhood", "nr_of_rooms", "akt16", "broker_commision", "type_of_estate", "energy_class"}
        for key, value in filters.items():
            if key in allowed:
                conditions.append(f"{key} = %({key})s")
                params[key] = value

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        print(f"[QUERY] {query}")
    conn = get_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params if params else {})
        value = cursor.fetchone()["value"]
    finally:
        conn.close()

    if value is None:
        return {"error": f"No data found for the given filters."}

    return {
        "metric": metric,
        "filters": filters or "all",
        "value": round(value, 2)
    }

