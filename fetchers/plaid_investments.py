# plaid_investments.py
import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.api_client import ApiException
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.investments_transactions_get_request import InvestmentsTransactionsGetRequest

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
    filename=os.path.join(log_dir, f'plaid_investments_{today}.log'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

def save_response_to_file(response, filename):
    with open(filename, 'w') as file:
        json.dump(response, file, indent=4)

def fetch_investment_holdings(access_token, bank_name):
    try:
        request = InvestmentsHoldingsGetRequest(access_token=access_token)
        response = client.investments_holdings_get(request).to_dict()
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f'data/fetched-files/plaid_investments_holdings_{bank_name}_{timestamp}.json'
        save_response_to_file(response, filename)

        message = f"Holdings for {bank_name} fetched and saved successfully as {filename}."
        print(message)
        logging.info(message)
        return filename

    except ApiException as e:
        error_response = json.loads(e.body)
        message = f"Error fetching holdings for {bank_name}: {e}"
        print(message)
        logging.error(message)
        return None

def fetch_investment_transactions(access_token, bank_name, start_date=None, end_date=None):
    if start_date is None:
        start_date = datetime.now() - timedelta(days=365*5)  # 5 years ago by default
    if end_date is None:
        end_date = datetime.now()

    start_date = start_date.date()
    end_date = end_date.date()

    try:
        request = InvestmentsTransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date
        )
        response = client.investments_transactions_get(request).to_dict()
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f'data/fetched-files/plaid_investments_transactions_{bank_name}_{timestamp}.json'
        save_response_to_file(response, filename)

        message = f"Investment transactions for {bank_name} fetched and saved successfully as {filename}."
        print(message)
        logging.info(message)
        return filename

    except ApiException as e:
        error_response = json.loads(e.body)
        message = f"Error fetching transactions for {bank_name}: {e}"
        print(message)
        logging.error(message)
        return None

if __name__ == "__main__":
    tokens = get_access_tokens_from_db()
    
    for token in tokens:
        access_token = token['access_token']
        bank_name = token['bank_name']
        
        print(f"Starting investment data fetch process for {bank_name}...")
        logging.info(f"Starting investment data fetch process for {bank_name}...")

        if access_token:
            fetch_investment_holdings(access_token, bank_name)
            fetch_investment_transactions(access_token, bank_name)
        else:
            message = "Access token is required."
            print(message)
            logging.error(message)
    print("Investment data fetch process completed.")
    logging.info("Investment data fetch process completed.")
