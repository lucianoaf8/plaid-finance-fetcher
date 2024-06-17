import os
import json
import logging
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.model.transactions_sync_request import TransactionsSyncRequest

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
    elif isinstance(obj, (datetime, timedelta)):
        obj = obj.isoformat()
    elif isinstance(obj, date):
        obj = obj.isoformat()
    return obj

def fetch_transactions(access_token, bank_name, cursor=""):
    all_transactions = []
    has_more = True

    while has_more:
        try:
            request = TransactionsSyncRequest(
                access_token=access_token,
                cursor=cursor,
                count=500
            )
            response = client.transactions_sync(request)
            transactions = response['added']
            all_transactions.extend(transactions)
            cursor = response['next_cursor']
            has_more = response['has_more']
        except Exception as e:
            message = f"Error fetching transactions for {bank_name}: {e}"
            print(message)
            logging.error(message)
            break

    transactions_dicts = [convert_dates_to_strings(transaction.to_dict()) for transaction in all_transactions]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f'data/fetched-files/plaid_transactions_{bank_name}_{timestamp}.json'
    with open(filename, 'w') as file:
        json.dump(transactions_dicts, file, indent=4)

    message = f"Transactions for {bank_name} fetched and saved successfully as {filename}."
    print(message)
    logging.info(message)
    return filename

if __name__ == "__main__":
    access_token = os.getenv("PLAID_ACCESS_TOKEN")
    bank_name = 'default_bank'
    last_fetch_date = os.getenv("LAST_FETCH_DATE", (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    start_date = last_fetch_date
    end_date = datetime.now().strftime('%Y-%m-%d')
    print(f"Starting transactions fetch process for {bank_name} from {start_date} to {end_date}...")
    logging.info(f"Starting transactions fetch process for {bank_name} from {start_date} to {end_date}...")
    if access_token:
        fetch_transactions(access_token, bank_name)
    else:
        message = "Access token is required."
        print(message)
        logging.error(message)
    print("Transactions fetch process completed.")
    logging.info("Transactions fetch process completed.")
