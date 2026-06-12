import psycopg2
import requests
from bs4 import BeautifulSoup
import time
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
from scraper.src.database import fetch_pending_ads, update_records

def normalize_fields(scraped_data):
    """Map Bulgarian HTML field names to database column names"""
    mapping = {
        '???? ?? ?2/EUR/:': 'price_m2_eur',
        '???? ?? ?2/BGN/:': 'price_m2_bgn',
        '?????????? /?2/:': 'size_m2',
        '???? :': 'floor',
        '??? 16:': 'akt16',
        '???????? ????:': 'energy_class',
        '???????????:': 'potreblenie',
        '????? ?? ???????? ?? ???????': 'broker_commision',
        '???????': 'additional_notes',
        '???? EUR/:': 'total_price_eur',
    }

    normalized = {}
    for bg_key, value in scraped_data.items():
        if bg_key in mapping:
            normalized[mapping[bg_key]] = value
        else:
            normalized[bg_key] = value

    return normalized

def run_worker(batch_size=20):
    while True:
        # 1. Connect to DB for reading
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        pending_ads = fetch_pending_ads(conn, batch_size=batch_size)
        cursor.close()
        conn.close()  # Close connection completely after reading

        if not pending_ads:
            break

        updates = []
        # fetch all additional info
        for ad_item in pending_ads:
            print(10*"=" + f"Fetching the html for item {ad_item["hash_id"]}..." + 10*"=")
            item_response = requests.get(ad_item['link'])
            item_response.encoding = item_response.apparent_encoding
            item_soup = BeautifulSoup(item_response.text, "html.parser")
            
            # grab the sidebar with descrtiptions (single element)
            try:
                aside_info = item_soup.find("aside", class_="info-sidebar")
                # print(aside_info)

                # find simple-table divs and filter by whether they contain td or p
                simple_tables = aside_info.find_all("div", class_="simple-table") if aside_info else []
                tables_with_td = [tbl for tbl in simple_tables if tbl.find("td")]
                tables_with_p = [tbl for tbl in simple_tables if tbl.find("p")]

                # if you want the first matching table only
                table_with_td_info = tables_with_td[0] if tables_with_td else None
                table_with_p_info = tables_with_p[0] if tables_with_p else None

                # description lives on the specific page
                description = item_soup.find("div", class_="text")
                description_text = description.get_text(" ", strip=True) if description else ""
                ad_item["description"] = description_text
                # print(description_text)

                price_container = item_soup.find("div", class_="big-price")
                price_tag = price_container.find("strong") if price_container else None
                if price_tag:
                    ad_item["total_price_eur"] = (
                        price_tag.get_text(" ", strip=True)
                        .replace("€", "")
                        .replace("EUR", "")
                        .strip()
                    )
                
                for row in table_with_td_info.find_all("tr") if table_with_td_info else []:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        key = cols[0].get_text(strip=True)
                        value = cols[1].get_text(strip=True)
                        ad_item[key] = value

                # extract text from <p> tags inside the simple-table
                p_texts = [p.get_text(" ", strip=True) for p in table_with_p_info.find_all("p")] if table_with_p_info else []
                p_texts

                # optional: split "key: value" style lines into a dict
                for text in p_texts:
                    if ":" in text:
                        key, value = text.split(":", 1)
                        ad_item[key.strip()] = value.strip()

                # print(10*"=" + f"Finished with item {id}" + 10*"=")
                ad_item = normalize_fields(ad_item)  # Convert field names

                # Scrape img_url
                img_tag = item_soup.find("img", {"itemprop": "image"})
                src = img_tag.get("src") if img_tag else None
                ad_item["img_url"] = "https://www.imoti.net" + src if src else None

                # Scrape extras
                extras_ul = item_soup.find("ul", class_="extras")
                li_items = extras_ul.find_all("li") if extras_ul else []
                ad_item["extras"] = "; ".join([li.get_text(strip=True) for li in li_items]) if li_items else None

                update = {
                    "hash_id": ad_item["hash_id"],
                    "description": ad_item.get("description", ""),
                    "price_m2_eur": ad_item.get("price_m2_eur", ""),
                    "price_m2_bgn": ad_item.get("price_m2_bgn", ""),
                    "size_m2": ad_item.get("size_m2", ""),
                    "floor": ad_item.get("floor", ""),
                    "akt16": ad_item.get("akt16", ""),
                    "energy_class": ad_item.get("energy_class", ""),
                    "potreblenie": ad_item.get("potreblenie", ""),
                    "broker_commision": ad_item.get("broker_commision", ""),
                    "additional_notes": ad_item.get("additional_notes", ""),
                    "img_url": ad_item.get("img_url"),
                    "extras": ad_item.get("extras"),
                    "total_price_eur": ad_item.get("total_price_eur", ""),
                }
                updates.append(update)
            except Exception as e:
                print(f"error when processing html of page {ad_item.get('hash_id')}: {e}")
        
        # print("Updated list: \n", updates)

        # Batch update all records once - open NEW connection for writing
        if updates:
            write_conn = psycopg2.connect(DATABASE_URL)
            update_records(write_conn, updates)
            write_conn.close()
        
        print(f"updated new batch of {batch_size} records")
    return None


