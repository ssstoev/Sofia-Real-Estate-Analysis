'''Orchestrate the embedding of the ads data'''
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import sqlite3

import qdrant_client

from data_transformation.ads_cleaned.src.database import query_entire_database_table
from vector_db.embeddings import embed_ads_data

def main():
    print("Begin embedding of ads...")
    conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scraper', 'data', 'ads_storage.db'))
    listings_data = query_entire_database_table('ads_cleaned', conn)
    conn.close()
    embed_ads_data(listings_data)
    # print(qdrant_client.get_collections())
    print("Finished embedding the ads!")

if __name__ == "__main__":
    main()
