import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.api_client import ApiException

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Load environment variables from .env file
load_dotenv()

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = os.getenv("PLAID_ENV", "development")

PLAID_ENV_URLS = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com"
}
PLAID_HOST = PLAID_ENV_URLS.get(PLAID_ENV, "https://production.plaid.com")

configuration = configuration.Configuration(
    host=PLAID_HOST,
    api_key={
        'clientId': PLAID_CLIENT_ID,
        'secret': PLAID_SECRET
    }
)
api_client = api_client.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

# Set up logging
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

today = datetime.now().strftime('%Y-%m-%d')
logging.basicConfig(
    filename=os.path.join(log_dir, f'plaid_categories_{today}.log'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

def fetch_categories():
    try:
        response = client.categories_get({})
        
        response_dict = response.to_dict()
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f'data/fetched-files/plaid_categories_{timestamp}.json'
        
        with open(filename, 'w') as file:
            json.dump(response_dict, file, indent=4)
        
        message = f"Categories fetched and saved successfully as {filename}."
        print(message)
        logging.info(message)
        return filename

    except ApiException as e:
        message = f"Error fetching categories: {e}"
        print(message)
        logging.error(message)

if __name__ == "__main__":
    print("Starting categories fetch process...")
    logging.info("Starting categories fetch process...")

    fetch_categories()

    print("Categories fetch process completed.")
    logging.info("Categories fetch process completed.")
