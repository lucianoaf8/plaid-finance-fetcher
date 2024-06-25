import os
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.link_token_create_request_user_address import LinkTokenCreateRequestUserAddress
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from plaid.exceptions import ApiException


# Load environment variables from .env file
load_dotenv()

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = os.getenv("PLAID_ENV", "production")

# Determine the Plaid environment URL
PLAID_ENV_URLS = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com"
}
PLAID_HOST = PLAID_ENV_URLS.get(PLAID_ENV, "https://production.plaid.com")  # Default to development

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

def create_link_token():
    request = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id='tangerine'),
        client_name='plaid-finance-fetcher',
        products=[Products('transactions'), Products('liabilities'), Products('assets')],
        country_codes=[CountryCode('CA')],
        language='en',
    )

    # print(request)
    response = client.link_token_create(request)
    return response['link_token']


if __name__ == "__main__":
    try:
        link_token = create_link_token()
        print(f"Link Token: {link_token}")
    except ApiException as e:
        print(f"An error occurred: {e}")

