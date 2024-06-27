import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.api_client import ApiException
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions

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
    filename=os.path.join(log_dir, f'plaid_transactions_{today}.log'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

def convert_dates_to_strings(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            obj[key] = convert_dates_to_strings(value)
    elif isinstance(obj, list):
        obj = [convert_dates_to_strings(item) for item in obj]
    elif isinstance(obj, (datetime, timedelta)):
        obj = obj.isoformat()
    elif isinstance(obj, date):
        obj = obj.isoformat()
    return obj

def fetch_transactions(access_token, bank_name, start_date=None, end_date=None):
    all_transactions = []
    total_transactions = 0

    if start_date is None:
        start_date = datetime.now() - timedelta(days=365*5)  # 5 years ago by default
    if end_date is None:
        end_date = datetime.now()

    start_date = start_date.date()
    end_date = end_date.date()

    options = TransactionsGetRequestOptions()
    options.count = 500  # Adjust the count as needed
    options.offset = 0

    while True:
        try:
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date,
                options=options
            )
            response = client.transactions_get(request)
            transactions = response['transactions']
            all_transactions.extend(transactions)
            total_transactions += len(transactions)
            
            print(f"Fetched {len(transactions)} transactions in this batch. Total so far: {total_transactions}")
            
            # Check if we need to paginate
            if len(transactions) == 0 or total_transactions >= response['total_transactions']:
                break

            options.offset += len(transactions)

        except ApiException as e:
            error_response = json.loads(e.body)
            error_code = error_response.get('error_code')
            if error_code == 'RATE_LIMIT_EXCEEDED':
                print("Rate limit exceeded, sleeping for 60 seconds...")
                logging.info("Rate limit exceeded, sleeping for 60 seconds...")
                time.sleep(60)
                continue
            else:
                message = f"Error fetching transactions for {bank_name}: {e}"
                print(message)
                logging.error(message)
                break

    transactions_dicts = [convert_dates_to_strings(transaction.to_dict()) for transaction in all_transactions]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f'data/fetched-files/plaid_transactions_{bank_name}_{timestamp}.json'
    with open(filename, 'w') as file:
        json.dump(transactions_dicts, file, indent=4)

    message = f"Transactions for {bank_name} fetched and saved successfully as {filename}. Total transactions: {total_transactions}"
    print(message)
    logging.info(message)
    return filename

if __name__ == "__main__":
    
    tokens = get_access_tokens_from_db()
    
    for token in tokens:
        access_token = token['access_token']
        bank_name = token['bank_name']
        bank_id = token['bank_id']
        
        print(f"Starting transactions fetch process for {bank_name}...")
        logging.info(f"Starting transactions fetch process for {bank_name}...")

        if access_token:
            fetch_transactions(access_token, bank_name)
        else:
            message = "Access token is required."
            print(message)
            logging.error(message)
    print("Transactions fetch process completed.")
    logging.info("Transactions fetch process completed.")
