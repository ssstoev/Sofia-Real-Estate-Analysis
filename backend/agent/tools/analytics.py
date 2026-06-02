# tools/analytics.py
import os
import sqlite3

_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'scraper', 'data', 'ads_storage.db')

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

async def get_stats(metric: str, neighborhood: str = None):
    query_map = {
        "avg_price": "SELECT AVG(total_price_eur) as value FROM ads_cleaned",
        "median_price": "SELECT AVG(total_price_eur) as value FROM (SELECT total_price_eur FROM ads_cleaned ORDER BY total_price_eur LIMIT 2 - (SELECT COUNT(*) FROM ads_cleaned) % 2 OFFSET (SELECT (COUNT(*) - 1) / 2 FROM ads_cleaned))",
        "avg_price_sqm": "SELECT AVG(price_m2_eur) as value FROM ads_cleaned",
        "listing_count": "SELECT COUNT(*) as value FROM ads_cleaned",
    }
    
    if metric not in query_map:
        return {"error": f"Unknown metric: {metric}"}
    
    query = query_map[metric]
    
    # Append neighborhood filter if provided
    if neighborhood:
        query += " WHERE neighbourhood = :neighborhood"
    
    conn = get_connection()
    try:
        result = conn.execute(query, {"neighborhood": neighborhood} if neighborhood else {})
        value = result.fetchone()["value"]
    finally:
        conn.close()

    if value is None:
        return {"error": f"No data found for the given filters."}

    return {
        "metric": metric,
        "neighborhood": neighborhood or "all",
        "value": round(value, 2)
    }

