import requests
from bs4 import BeautifulSoup
import chardet # for the encoding
import re
import pandas as pd

# Function to fetch and decode webpage content
def fetch_webpage(url):
    # Fetch the webpage
    response = requests.get(url)

    # Detect the encoding of the content
    detected_encoding = chardet.detect(response.content)['encoding']
    
    # Decode the content using the detected encoding
    if detected_encoding:
        content = response.content.decode(detected_encoding)
    else:
        # Fallback to UTF-8 if encoding detection fails
        content = response.content.decode('utf-8', errors='ignore')

    # html_content = response.text
    soup = BeautifulSoup(content, 'html.parser')

    # here each real estate post is stored
    title_wrappers = soup.find_all('div', class_ = 'real-estate-text')
    real_estate_dict = {}

    for real_estate in title_wrappers:
        offer_type = real_estate.find("h3").find("span", class_="re-offer-type").get_text(strip=True)
        estate_type = real_estate.find("h3").get_text(strip=True).replace(offer_type, '').strip()
        location = real_estate.find("span", class_="location").get_text(strip=True)
        price = real_estate.find("strong", class_="price").get_text(strip=True).replace("EUR", " EUR").strip()
        
        # Extract size from the estate_type using regex
        size_match = re.search(r'(\d+\s)', str(real_estate.find("h3")))
        size = size_match.group(1) if size_match else "N/A"

        real_estate_dict[estate_type] = {'Location': location, 'Price (EUR)': price, 'Size (m2)': size}

        # for key, value in real_estate_dict.items():
            # print(f"Size: {estate['Size (m2)']}")
            # print(f"Price: {estate['Price (EUR)']}")
            # print(f"Location: {estate['Location']}")
            # print()
            # print(f"{key}: {value}")
            # print()

    # print(real_estate_dict)
    return real_estate_dict

# URL of the webpage you want to scrape
base_url = 'https://www.imoti.net/bg/obiavi/r/prodava/sofia/?page=1&sid=gSoWpd'  # Replace with the actual URL

total_pages = 357

real_estate_data = {} # here we are going to store the books information from each page

for page_number in range(1, total_pages + 1):
    the_url = f'https://www.imoti.net/bg/obiavi/r/prodava/sofia/?page={page_number}&sid=gSoWpd'# + str(page_number)
    current_page_real_estate_data = fetch_webpage(the_url)
    real_estate_data.update(current_page_real_estate_data)
    print(real_estate_data)

#we create a df from the bpage_real_estate_data dictionary 
df = pd.DataFrame.from_dict(real_estate_data, orient='index')
df.index.name = 'Real Estate Name'
df.reset_index(inplace=True)
df.to_excel(f'real_estate_sofia_{total_pages}_pages.xlsx', index=False)

print(f'Done. Real estate information from all {total_pages} pages are downloaded')


