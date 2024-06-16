import os
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.model.liabilities_get_request import LiabilitiesGetRequest
from datetime import datetime, date
import json

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
    request = LiabilitiesGetRequest(access_token=access_token)
    response = client.liabilities_get(request)
    liabilities = response['liabilities']
    
    liabilities_dict = convert_dates_to_strings(liabilities.to_dict())

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f'data/fetched-files/plaid_liabilities_{bank_name}_{timestamp}.json'
    with open(filename, 'w') as file:
        json.dump(liabilities_dict, file, indent=4)

    print(f"Liabilities for {bank_name} fetched and saved successfully as {filename}.")

if __name__ == "__main__":
    access_token = os.getenv("PLAID_ACCESS_TOKEN")
    if access_token:
        fetch_liabilities(access_token, 'default_bank')
    else:
        print("Access token is required.")
