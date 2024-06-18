import os
import json
import logging
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.api_client import ApiException
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
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

def check_institution(institution_id):
    try:
        request = InstitutionsGetByIdRequest(
            institution_id=institution_id,
            country_codes=[CountryCode('CA')]
        )
        response = client.institutions_get_by_id(request)
        institution_details = response.to_dict()
        print(json.dumps(institution_details, indent=4))
        logging.info(f"Institution details: {json.dumps(institution_details, indent=4)}")
        return institution_details
    except ApiException as e:
        error_response = json.loads(e.body)
        print(f"Error fetching institution details: {error_response}")
        logging.error(f"Error fetching institution details: {error_response}")
        return None

# Example usage
if __name__ == "__main__":
    institution_id = "ins_117195"  # Correct institution ID for Canadian Tire Bank
    print(f"Checking institution details for ID: {institution_id}")
    institution_details = check_institution(institution_id)
    if institution_details:
        print("Institution details fetched successfully.")
    else:
        print("Failed to fetch institution details.")
