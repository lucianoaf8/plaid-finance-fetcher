import os
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.liabilities_get_request import LiabilitiesGetRequest
from datetime import datetime, timedelta, date
import json
from plaid.model.item_remove_request import ItemRemoveRequest

# Load environment variables from .env file
load_dotenv()

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ACCESS_TOKEN = os.getenv("PLAID_ACCESS_TOKEN")  # Use the access token obtained
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")

# Determine the Plaid environment URL
PLAID_ENV_URLS = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com"
}
PLAID_HOST = PLAID_ENV_URLS.get(PLAID_ENV, "https://sandbox.plaid.com")

# Configure Plaid client
configuration = configuration.Configuration(
    host=PLAID_HOST,
    api_key={
        'clientId': PLAID_CLIENT_ID,
        'secret': PLAID_SECRET
    }
)
api_client = api_client.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

# Helper function to convert date objects to strings
def convert_dates_to_strings(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            obj[key] = convert_dates_to_strings(value)
    elif isinstance(obj, list):
        obj = [convert_dates_to_strings(item) for item in obj]
    elif isinstance(obj, (datetime, date)):
        obj = obj.isoformat()
    return obj

# Function to fetch transactions
def fetch_transactions(access_token):
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    request = TransactionsGetRequest(
        access_token=access_token,
        start_date=start_date.date(),
        end_date=end_date.date()
    )
    response = client.transactions_get(request)
    transactions = response['transactions']
    
    # Convert transactions to dictionaries and handle date serialization
    transactions_dicts = [convert_dates_to_strings(transaction.to_dict()) for transaction in transactions]

    return transactions_dicts

# Function to fetch liabilities
def fetch_liabilities(access_token):
    request = LiabilitiesGetRequest(access_token=access_token)
    response = client.liabilities_get(request)
    liabilities = response['liabilities']
    return convert_dates_to_strings(liabilities.to_dict())

# Main function to execute the workflow
def main():
    access_token = PLAID_ACCESS_TOKEN  # Use the access token directly

    transactions = fetch_transactions(access_token)
    liabilities = fetch_liabilities(access_token)

    # Save transactions and liabilities to JSON files
    with open('transactions.json', 'w') as transactions_file:
        json.dump(transactions, transactions_file, indent=4)

    with open('liabilities.json', 'w') as liabilities_file:
        json.dump(liabilities, liabilities_file, indent=4)

    print("Transactions and liabilities have been saved to 'transactions.json' and 'liabilities.json'.")

if __name__ == "__main__":
    main()
