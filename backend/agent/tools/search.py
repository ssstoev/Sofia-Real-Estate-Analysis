# tools/search.py
from retrieval.hard_constraints import extract_hard_constraints, filter_db_on_hard_constraints
from vector_db.search_embeddings import search_vector_db
from backend.data_transformation.ads_cleaned.src.database import fetch_metadata_from_rdbms

async def search_listings(query: str, top_k: int = 5) -> list[dict]:
    constraints = extract_hard_constraints(query)
    candidate_ids = filter_db_on_hard_constraints(constraints)

    if not candidate_ids:
        return []

    raw_results = search_vector_db(query, candidate_ids, top_k=top_k)

    result_hash_ids = [point.payload["Hash_id"] for point in raw_results]
    sql_data = fetch_metadata_from_rdbms(result_hash_ids)

    listings = []
    for point in raw_results:
        hid = point.payload["Hash_id"]
        merged = {
            "hash_id": hid,
            "score": round(point.score, 3),
            **sql_data.get(hid, {})
        }
        listings.append(merged)

    return listings
