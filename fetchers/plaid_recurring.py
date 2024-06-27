import os
import sys
import json
import logging
import time
from datetime import datetime, date
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.api_client import ApiException
from plaid.model.transactions_recurring_get_request import TransactionsRecurringGetRequest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.plaid_accounts import get_access_tokens_from_db

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
    filename=os.path.join(log_dir, f'plaid_recurring_transactions_{today}.log'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

def convert_dates_to_strings(obj):
    if isinstance(obj, dict):
        return {key: convert_dates_to_strings(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_dates_to_strings(item) for item in obj]
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    else:
        return obj

def fetch_recurring_transactions(access_token, bank_name):
    try:
        request = TransactionsRecurringGetRequest(
            access_token=access_token
        )
        response = client.transactions_recurring_get(request)
        
        response_dict = convert_dates_to_strings(response.to_dict())
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f'data/fetched-files/plaid_recurring_transactions_{bank_name}_{timestamp}.json'
        
        with open(filename, 'w') as file:
            json.dump(response_dict, file, indent=4)
        
        message = f"Recurring transactions for {bank_name} fetched and saved successfully as {filename}."
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
            fetch_recurring_transactions(access_token, bank_name)
        else:
            message = f"Error fetching recurring transactions for {bank_name}: {e}"
            print(message)
            logging.error(message)

if __name__ == "__main__":
    
    tokens = get_access_tokens_from_db()
    
    for token in tokens:
        access_token = token['access_token']
        bank_name = token['bank_name']
        bank_id = token['bank_id']
        
        print(f"Starting recurring transactions fetch process for {bank_name}...")
        logging.info(f"Starting recurring transactions fetch process for {bank_name}...")

        if access_token:
            fetch_recurring_transactions(access_token, bank_name)
        else:
            message = "Access token is required."
            print(message)
            logging.error(message)
    print("Recurring transactions fetch process completed.")
    logging.info("Recurring transactions fetch process completed.")
