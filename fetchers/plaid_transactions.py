import os
import json
import logging
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.model.transactions_get_request import TransactionsGetRequest
from datetime import datetime, timedelta, date

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
    elif isinstance(obj, (datetime, date)):
        obj = obj.isoformat()
    return obj

def fetch_transactions(access_token, bank_name):
    try:
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date.date(),
            end_date=end_date.date()
        )
        response = client.transactions_get(request)
        transactions = response['transactions']
        
        transactions_dicts = [convert_dates_to_strings(transaction.to_dict()) for transaction in transactions]

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f'data/fetched-files/plaid_transactions_{bank_name}_{timestamp}.json'
        with open(filename, 'w') as file:
            json.dump(transactions_dicts, file, indent=4)

        message = f"Transactions for {bank_name} fetched and saved successfully as {filename}."
        print(message)
        logging.info(message)
    except Exception as e:
        message = f"Error fetching transactions for {bank_name}: {e}"
        print(message)
        logging.error(message)

if __name__ == "__main__":
    access_token = os.getenv("PLAID_ACCESS_TOKEN")
    bank_name = 'default_bank'
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
