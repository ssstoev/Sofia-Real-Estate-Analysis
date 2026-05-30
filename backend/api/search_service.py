from data_transformation.ads_cleaned_transformation.database import fetch_metadata_from_rdbms
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import traceback

from retrieval.hard_constraints import extract_hard_constraints_v1, build_sql_query
from vector_db.search_embeddings import search_vector_db
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Without this your browser will throw a CORS error before the request even reaches your backend.
# Need to add it because fasAPI & Vite are on different ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Vite's default port
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- Request / Response Models ---
# create pydantic model for the search request; for a single listing  & for a list of listings
class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 100  # how many results to return

class Listing(BaseModel):
    hash_id: str
    title: Optional[str] = None
    link: Optional[str] = None
    img_url: Optional[str] = None
    total_price_eur: Optional[float] = None
    size_m2: Optional[str] = None
    neighbourhood: Optional[str] = None
    score: float # similarity score from Qdrant

class SearchResponse(BaseModel):
    results: list[Listing]
    total: int

# --- POST Endpoint ---
@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    try:
        # Step 1: Extract hard constraints from the query
        constraints = extract_hard_constraints_v1(request.query)
        print(f"Extracted hard constraints: \n {constraints} \n")

        # Step 2: Filter RDBMS using hard constraints to get candidate IDs
        candidate_ids = build_sql_query(constraints)
        print(f"Found {len(candidate_ids)} results that match the constraints \n")

        # WIP: If no candidate_ids are found, return e.g. the most recent ads or some other ones
        if not candidate_ids:
            return SearchResponse(results=[], total=0)
        
        # Step 3: Search the vector DB and return results
        raw_qdrant_results = search_vector_db(request.query, candidate_ids)
        print(f"Successfully searched the vector DB! Found {len(raw_qdrant_results)} points \n")

        # Step 4: extract hash_ids from the raw qdrant result & 
        # join data b/w vectorDB & rdbms
        result_hash_ids = [point.payload["Hash_id"] for point in raw_qdrant_results]
        # print(result_hash_ids)
        sql_data = fetch_metadata_from_rdbms(result_hash_ids)
   
        final_results = []
        for point in raw_qdrant_results:
            hid = point.payload["Hash_id"]
            try:
                merged = {
                    "hash_id": hid,
                    "score": point.score,
                    **point.payload,          # from Qdrant
                    **sql_data.get(hid, {})    # from SQLite
                }

                final_results.append(merged)
            except Exception as e:
                print(e)

        print("final results are fetched")
        # print(final_results[0])
        # Step 6: Shape into response
        listings = [
            Listing(
                hash_id = r.get("hash_id", ""),
                title = r.get("Title", ""),
                link = r.get("link", ""),
                img_url = r.get("img_url", ""),
                total_price_eur = r.get("Price (EUR)") or None,
                size_m2 = r.get("Size", ""),
                neighbourhood = r.get("Neighbourhood", ""),
                score = r.get("score", 0.0),
            )
            for r in final_results
        ]
        print(f"Final result contains {len(listings)} points!")
        return SearchResponse(results=listings, total=len(listings))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))