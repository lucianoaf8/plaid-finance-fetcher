# remove_asset.py
import os
import sys
import json
import logging
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import configuration, api_client
from datetime import datetime

from plaid.api_client import ApiException
from plaid.model.asset_report_remove_request import AssetReportRemoveRequest

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
    filename=os.path.join(log_dir, f'remove_asset_reports_{today}.log'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

def remove_asset_report(asset_report_token):
    try:
        request = AssetReportRemoveRequest(asset_report_token=asset_report_token)
        response = client.asset_report_remove(request)
        
        message = f"Asset report with token {asset_report_token} removed successfully."
        print(message)
        logging.info(message)
        return True
    except ApiException as e:
        error_response = json.loads(e.body)
        message = f"Error removing asset report with token {asset_report_token}: {e}"
        print(message)
        logging.error(message)
        return False

if __name__ == "__main__":
    # List of asset reports to remove
    asset_reports = [
        "c2c1373b-6c9e-41ad-9543-181a3ea1fa80",
        "7a5a62e0-2049-4248-913a-2c44cb326c36",
        "5aa3fe20-8c4c-4dee-8b41-52fd639ee340",
        "cf2fbe9a-158c-48eb-9941-6bebd0dae62c",
        "62ec176d-0f79-42f7-8f4d-bedb4293ece3",
        "397e5d22-30a9-440e-b764-0234f5de7142"
    ]
    
    for asset_report_token in asset_reports:
        remove_asset_report(asset_report_token)
    
    print("Asset report removal process completed.")
    logging.info("Asset report removal process completed.")
