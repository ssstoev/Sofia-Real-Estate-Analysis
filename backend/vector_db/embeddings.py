import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from qdrant_client.models import Distance, VectorParams, PointStruct, PayloadSchemaType
from qdrant_client import QdrantClient

from openai import OpenAI
import uuid
import qdrant_client
import sqlite3

from backend.data_transformation.ads_cleaned.src.database import query_entire_database_table

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# WIP: wrap embedding logic in a function
OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_CLUSTER_URL = os.getenv("QDRANT_CLUSTER_URL")

def build_text_for_embedding(listing: dict) -> str:
    '''Combine all of the fields into one string'''
    return (
        f"Hash_id: {listing['hash_id']}",
        f"Title: {listing['title']}. ",
        f"Neighbourhood: {listing['neighbourhood']}. ",
        f"Price: {listing['total_price_eur']}",
        f"Price per m2 (EUR): {listing['price_m2_eur']}"
        f"Size: {listing['size_m2']}",
        f"Floor: {listing['floor']}",
        f"Akt16: {"ДА" if listing['akt16'] == 1 else "НЕ"}"
        f"Description: {listing['description'], listing['extras']}"
    )

client = QdrantClient(
    url=QDRANT_CLUSTER_URL, 
    api_key=QDRANT_API_KEY,
)

openai = OpenAI(
    api_key=OPEN_AI_API_KEY
)

# create indices for the payload using the hash_ids
client.create_payload_index(
    collection_name="listings",
    field_name="Hash_id",
    field_schema=PayloadSchemaType.KEYWORD,
)

# Create collection — dimension must match your model (1536 for text-embedding-3-small)
if not client.collection_exists("listings"):
    client.create_collection(
        collection_name="listings",
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
    )

def embed(text: str) -> list[float]:
    response = openai.embeddings.create(input=text, model="text-embedding-3-small")
    return response.data[0].embedding

def embed_ads_data(data_to_embed: list[dict]):
    '''Embed the passed data into a vector and insert it in Qdrant collection'''
    # Ingest listings
    batch_count = 0
    total_count = 0
    points = []
    for listing in data_to_embed: # your list of dicts from the relational DB
        text = build_text_for_embedding(listing)
        print("built text for embedding")
        vector = embed(text)
        print("emebedded the text")
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={                  # store metadata for filtering + display
                "Hash_id": listing["hash_id"],
                "url": listing["url"],
                "Title": listing['title'],
                "Neighbourhood": listing['neighbourhood'],
                "Price (EUR)": listing['total_price_eur'],
                "Price per m2": f"{listing['price_m2_eur']}",
                "nr of rooms": listing["nr_of_rooms"],
                "Size": f"{listing['size_m2']}" ,
                "Floor": listing["floor"],
                "Akt16": listing["akt16"],
                "Description": f"{listing['description'], listing["extras"]}"
            }
        ))
        batch_count += 1
        total_count += 1
        print(f"Successfully embedded {total_count} data points")

        if batch_count % 20 == 0:
            client.upsert(collection_name="listings", points=points)
            print(f"Inserted a total of {total_count} vectors in the vectorDB!")
            batch_count = 0
            points = [] # empty the points list after upserting in the vector db
    

