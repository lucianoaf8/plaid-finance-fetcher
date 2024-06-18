import os
import json
import logging
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.api_client import ApiException
from plaid.model.liabilities_get_request import LiabilitiesGetRequest
from datetime import datetime, date
import time
import time


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
PLAID_HOST = PLAID_ENV_URLS.get(PLAID_ENV, "https://development.plaid.com")

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
    filename=os.path.join(log_dir, f'plaid_liabilities_{today}.log'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

def convert_dates_to_strings(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            obj[key] = convert_dates_to_strings(value)
    elif isinstance(obj, list):
        obj = [convert_dates_to_strings(item) for item in obj]
    elif isinstance(obj, (datetime, date)):
        obj = obj.isoformat()
    return obj

def fetch_liabilities(access_token, bank_name):
    logging.info(f"Fetching liabilities for {bank_name}...")
    try:
        request = LiabilitiesGetRequest(access_token=access_token)
        response = client.liabilities_get(request)
        liabilities = response['liabilities']
        
        liabilities_dict = convert_dates_to_strings(liabilities.to_dict())

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f'data/fetched-files/plaid_liabilities_{bank_name}_{timestamp}.json'
        with open(filename, 'w') as file:
            json.dump(liabilities_dict, file, indent=4)

        message = f"Liabilities for {bank_name} fetched and saved successfully as {filename}."
        print(message)
        logging.info(message)

        return filename
    except ApiException as e:
        error_response = json.loads(e.body)
        error_code = error_response.get('error_code')
        if error_code == 'RATE_LIMIT_EXCEEDED':
            print("Rate limit exceeded, sleeping for 60 seconds...")
            logging.info("Rate limit exceeded, sleeping for 60 seconds...")
            time.sleep(60)
            return fetch_liabilities(access_token, bank_name)
        else:
            message = f"Error fetching liabilities for {bank_name}: {e}"
            print(message)
            logging.error(message)
            return None
    except Exception as e:
        message = f"Error fetching liabilities for {bank_name}: {e}"
        print(message)
        logging.error(message)
        return None

if __name__ == "__main__": 
    access_token = os.getenv("ACCESS_TOKEN_TANGERINE")
    bank_name = 'Tangerine'
    print(f"Starting liabilities fetch process for {bank_name}...")
    logging.info(f"Starting liabilities fetch process for {bank_name}...")
    if access_token:
        fetch_liabilities(access_token, bank_name)
    else:
        message = "Access token is required."
        print(message)
        logging.error(message)
    print("Liabilities fetch process completed.")
    logging.info("Liabilities fetch process completed.")
