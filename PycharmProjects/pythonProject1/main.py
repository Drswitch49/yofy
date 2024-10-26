from pytrends.request import TrendReq
import requests
import json
import re
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets setup
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1-jiMn9Ba7VX_T_BTz2ybK55EUNF8wa_GNAvjAPyMQKo"  # Google Sheets ID
SHEET_NAME = "Shopify stores data"  # Specific sheet name
CREDENTIALS_FILE = "/Users/ayodejioyesanya/PycharmProjects/pythonProject1/venv/credentials.json"  # Updated path to credentials.json file

# Initialize Google Sheets client and get the sheet, creating it if necessary
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key(SPREADSHEET_ID)

try:
    sheet = spreadsheet.worksheet(SHEET_NAME)
except gspread.exceptions.WorksheetNotFound:
    # Create the worksheet if it doesn't exist
    sheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows="100", cols="20")
    print(f"Created new worksheet: {SHEET_NAME}")

# Initialize pytrends
pytrends = TrendReq(hl='en-US', tz=360)

# Predefined categories
predefined_categories = [
    "fitness", "skincare", "organic products", "handmade jewelry", "pet supplies",
    "baby products", "vegan clothing", "home decor", "outdoor gear", "electronics accessories",
    "sustainable fashion", "sports equipment", "digital products", "men’s grooming", "yoga products",
    "bestselling products", "limited edition", "eco-friendly", "new arrivals", "custom orders"
]

# Function to fetch trending topics
def get_trending_topics():
    trending_df = pytrends.trending_searches(pn='united_states')
    trending_topics = trending_df[0].tolist()
    return trending_topics

# Google Custom Search to find Shopify URLs
def google_search(query, api_key, search_engine_id):
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={api_key}&cx={search_engine_id}"
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json()
        store_urls = [item['link'] for item in results.get('items', [])]
        return store_urls
    else:
        print(f"Error: {response.status_code}")
        return []

# Scrape email and phone number
def extract_contact_info(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        emails = set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", soup.text))
        phones = set(re.findall(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", soup.text))
        return {
            "url": url,
            "emails": ", ".join(emails),
            "phones": ", ".join(phones)
        }
    except Exception as e:
        print(f"Error fetching contact info for {url}: {e}")
        return {"url": url, "emails": "", "phones": ""}

# Update Google Sheets
def update_google_sheets(data):
    # Prepare data rows for Google Sheets
    rows = [["URL", "Email", "Phone"]]  # Header row
    for entry in data:
        rows.append([entry["url"], entry["emails"], entry["phones"]])

    # Clear existing data and add new data to Google Sheets
    sheet.clear()
    sheet.append_rows(rows)
    print("Data updated in Google Sheets.")

# Main function
def main():
    # Step 1: Fetch trending topics
    trending_topics = get_trending_topics()

    # Step 2: Combine predefined categories with trending topics
    search_topics = predefined_categories + trending_topics

    # Step 3: Search Shopify stores for each topic
    all_data = []
    API_KEY = "AIzaSyBKq0Vg9el3BFafiWu9kWXFoeNZq5SSSuY"  # Replace with your actual API Key
    SEARCH_ENGINE_ID = "751d470c5c6f040ed"  # Replace with your Search Engine ID

    for topic in search_topics:
        query = f"{topic} site:myshopify.com"
        print(f"Searching for: {query}")

        shopify_urls = google_search(query, API_KEY, SEARCH_ENGINE_ID)

        # Step 4: Extract contact information for each Shopify store
        for url in shopify_urls:
            contact_info = extract_contact_info(url)
            all_data.append(contact_info)

    # Step 5: Update Google Sheets with the gathered data
    update_google_sheets(all_data)

if __name__ == "__main__":
    main()
