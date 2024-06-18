import os
import json
import logging
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.api_client import ApiException
from plaid.model.institutions_search_request import InstitutionsSearchRequest
from plaid.model.country_code import CountryCode

# Load environment variables
load_dotenv()

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")

PLAID_ENV_URLS = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com"
}
PLAID_HOST = PLAID_ENV_URLS.get(PLAID_ENV, "https://sandbox.plaid.com")

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
logging.basicConfig(level=logging.INFO)

def search_institution(query):
    try:
        request = InstitutionsSearchRequest(
            query=query,
            country_codes=[CountryCode('CA')]
        )
        response = client.institutions_search(request)
        institutions = response['institutions']
        if institutions:
            institution_details = institutions[0].to_dict()
            print(json.dumps(institution_details, indent=4))
            logging.info(f"Institution details: {json.dumps(institution_details, indent=4)}")
            return institution_details
        else:
            print("No institutions found.")
            logging.info("No institutions found.")
            return None
    except ApiException as e:
        error_response = json.loads(e.body)
        print(f"Error searching for institution: {error_response}")
        logging.error(f"Error searching for institution: {error_response}")
        return None

# Example usage
if __name__ == "__main__":
    institution_name = "CIBC"
    print(f"Searching institution details for: {institution_name}")
    institution_details = search_institution(institution_name)
    if institution_details:
        print("Institution details fetched successfully.")
    else:
        print("Failed to fetch institution details.")
