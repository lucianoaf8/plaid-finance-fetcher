import os
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.model.transactions_get_request import TransactionsGetRequest
from datetime import datetime, timedelta, date
import json

load_dotenv()

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ACCESS_TOKEN = os.getenv("PLAID_ACCESS_TOKEN")
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

def convert_dates_to_strings(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            obj[key] = convert_dates_to_strings(value)
    elif isinstance(obj, list):
        obj = [convert_dates_to_strings(item) for item in obj]
    elif isinstance(obj, (datetime, date)):
        obj = obj.isoformat()
    return obj

def fetch_transactions():
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    request = TransactionsGetRequest(
        access_token=PLAID_ACCESS_TOKEN,
        start_date=start_date.date(),
        end_date=end_date.date()
    )
    response = client.transactions_get(request)
    transactions = response['transactions']
    
    transactions_dicts = [convert_dates_to_strings(transaction.to_dict()) for transaction in transactions]

    with open('fetched-files/transactions.json', 'w') as file:
        json.dump(transactions_dicts, file, indent=4)

    print("Transactions fetched and saved successfully.")

if __name__ == "__main__":
    fetch_transactions()
