import os
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest

# Load environment variables from .env file
load_dotenv()

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = os.getenv("PLAID_ENV", "development")  # Set default to development

# Determine the Plaid environment URL
PLAID_ENV_URLS = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com"
}
PLAID_HOST = PLAID_ENV_URLS.get(PLAID_ENV, "https://development.plaid.com")  # Default to development

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

def exchange_public_token(public_token):
    request = ItemPublicTokenExchangeRequest(public_token=public_token)
    response = client.item_public_token_exchange(request)
    return response['access_token']

if __name__ == "__main__":
    public_token = input("Enter the public token obtained from Plaid Link: ")
    access_token = exchange_public_token(public_token)
    print(f"Access Token: {access_token}")
