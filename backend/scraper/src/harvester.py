import requests
from bs4 import BeautifulSoup
import chardet
import psycopg2
import time
import random
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

from src.database import insert_ad

import hashlib

def generate_ad_id(title, url):
    '''Generate unique customized ID of the ad based on stable fields.
    
    Parameters:
        title (str): ad title
        url (str): link to the ad
    
    Returns:
        str'''
    
    key = f"{title}|{url}"     # choose stable fields
    return hashlib.sha256(key.encode()).hexdigest()

def scrape_single_page(page_url: str):
    '''Scrape all ads from a single page
    Args:
        page_url (str): the url of the first page
    
    Returns:
        ads_dict (dict): Dicitonary with all the ads info from the page
    '''
    response = requests.get(page_url)
    # Detect the encoding of the content
    detected_encoding = chardet.detect(response.content)['encoding']
    # Decode the content using the detected encoding
    if detected_encoding:
        content = response.content.decode(detected_encoding)
    else:
        # Fallback to UTF-8 if encoding detection fails
        content = response.content.decode('utf-8', errors='ignore')

    soup = BeautifulSoup(content, "html.parser")
    box_items = soup.find_all('li', class_ = 'clearfix')

    ads_dict = {}
    prefix = "https://www.imoti.net"
    for real_estate in box_items:
        try:
            link_to_ad = real_estate.find('a').get('href')
            ad_title = real_estate.find('img').get('alt') if real_estate.find('img').get('alt') else None

            # generate unique ID of the ad based on the title & url
            ad_id = generate_ad_id(
                title=ad_title,
                url=link_to_ad
                )
            
            # add a new element to the dict
            ads_dict[ad_id] = {'ad_title': ad_title, 'link_to_ad': prefix + link_to_ad}
        
        except Exception as e:
            print(f"Error at page: {e}")
    
    return ads_dict

def run_harvester():
    '''Extract main ad info from all pages & insert into db'''
    # 1. Connect to DB
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor() # MUST define this
    
    page_number = 1
    has_next_page = True

    while has_next_page:
        # Construct URL
        current_page_url = f'https://www.imoti.net/bg/obiavi/r/prodava/sofia/?page={page_number}'
        print(50*"=" + f"Currently at page {page_number}" + 50*"=")
        try:
            single_page_ads = scrape_single_page(current_page_url)
            
            # If the function returns None or an empty list, stop
            if not single_page_ads:
                print(f"Finished: No more ads found at page {page_number}.")
                has_next_page = False
                break
            
            insert_ad(cursor, single_page_ads)
            
            # 3. Commit at the end of each page (The Batch)
            conn.commit()
            print(f"Page {page_number} synced to DB.")
            
            page_number += 1
            
            # Add a small delay so you don't get banned!
            time.sleep(random.uniform(1, 3))

        except Exception as e:
            print(f"Error on page {page_number}: {e}")
            # If one page fails, we might want to try the next one instead of stopping
            page_number += 1 
            continue
    
    conn.close()

