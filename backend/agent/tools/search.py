# tools/search.py
from retrieval.hard_constraints import filter_db_on_hard_constraints
from vector_db.search_embeddings import search_vector_db
from data_transformation.ads_cleaned.src.database import fetch_metadata_from_rdbms

async def search_listings(query: str, top_k: int = 5) -> list[dict]:
    result_listings = filter_db_on_hard_constraints(query)

    if not result_listings["results"]:
        return []

    return result_listings["results"]
