from vector_db.embeddings import embed, client
from qdrant_client.models import Filter, FieldCondition, Range, MatchAny, MatchValue, HasIdCondition, NamedVector

def search_vector_db(query: str, hash_ids: list = None, top_k: int = 100):
    query_vector = embed(query)

    filters = None
    if hash_ids:
        # scroll doesn't require a payload index — use it to resolve internal point IDs
        scroll_filter = Filter(must=[
            FieldCondition(key="Hash_id", match=MatchAny(any=hash_ids))
        ])
        matched_points, _ = client.scroll(
            collection_name="listings",
            scroll_filter=scroll_filter,
            limit=len(hash_ids),
            with_payload=False,
            with_vectors=False,
        )
        point_ids = [p.id for p in matched_points]
        if not point_ids:
            return []
        filters = Filter(must=[HasIdCondition(has_id=point_ids)])
    
    results = client.query_points(
        collection_name="listings",
        query=query_vector,
        query_filter=filters,
        limit=top_k
    )
    return results.points

# Example
# results = search_vector_db("Необзаведен апартамент в квартал Надежда", top_k=5) #, ["93e00b28728005ffbece0fb975f1d38678910fb796a7fd28b40fc97826e2e124", 
#                                                                         #'f86956dd334888697e09f28acb103cf8c9dfa00f0bc5d6bec99a5fae51bc5751'])
# for r in results:
#     print(r.payload["Title"])
# print(results)