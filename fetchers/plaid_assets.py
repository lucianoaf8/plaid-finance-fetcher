import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.api_client import ApiException
from plaid.model.asset_report_get_request import AssetReportGetRequest
from plaid.model.asset_report_create_request import AssetReportCreateRequest
from plaid.model.asset_report_create_request_options import AssetReportCreateRequestOptions

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.plaid_accounts import get_access_tokens_from_db

# Load environment variables from .env file
load_dotenv()

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = os.getenv("PLAID_ENV", "development")
ASSET_REPORT_TOKEN = os.getenv("ASSET_REPORT_TOKEN")

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
    filename=os.path.join(log_dir, f'plaid_assets_{today}.log'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

def convert_datetimes(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            obj[key] = convert_datetimes(value)
    elif isinstance(obj, list):
        obj = [convert_datetimes(item) for item in obj]
    elif isinstance(obj, (datetime, date)):
        obj = obj.isoformat()
    return obj

def create_asset_report(access_tokens, days_requested=731):
    try:
        options = AssetReportCreateRequestOptions()
        request = AssetReportCreateRequest(
            access_tokens=access_tokens,
            days_requested=days_requested,
            options=options
        )
        response = client.asset_report_create(request)
        asset_report_token = response['asset_report_token']
        logging.info(f"Asset report created with token: {asset_report_token}")
        print(f"Asset report created with token: {asset_report_token}")
        return asset_report_token
    except ApiException as e:
        error_response = json.loads(e.body)
        logging.error(f"Error creating asset report: {error_response}")
        print(f"Error creating asset report: {error_response}")
        return None

def fetch_asset_report(asset_report_token):
    try:
        request = AssetReportGetRequest(asset_report_token=asset_report_token)
        response = client.asset_report_get(request)
        report = response.to_dict()  # Convert to dict for JSON serialization
        logging.info(f"Asset report fetched: {report}")
        print(f"Asset report fetched: {report}")
        return report
    except ApiException as e:
        error_response = json.loads(e.body)
        if error_response.get('error_code') == 'PRODUCT_NOT_READY':
            logging.info("Asset report not ready. Retrying in 60 seconds...")
            print("Asset report not ready. Retrying in 60 seconds...")
            time.sleep(60)
            return fetch_asset_report(asset_report_token)
        else:
            logging.error(f"Error fetching asset report: {error_response}")
            print(f"Error fetching asset report: {error_response}")
            return None

if __name__ == "__main__":
    if ASSET_REPORT_TOKEN:
        print(f"Using existing asset report token: {ASSET_REPORT_TOKEN}")
        logging.info(f"Using existing asset report token: {ASSET_REPORT_TOKEN}")
        report = fetch_asset_report(ASSET_REPORT_TOKEN)
    else:
        tokens = get_access_tokens_from_db()
        access_tokens = [token['access_token'] for token in tokens]

        if not access_tokens:
            print("No access tokens found.")
            logging.error("No access tokens found.")
            sys.exit(1)

        asset_report_token = create_asset_report(access_tokens)
        if asset_report_token:
            # Wait for the asset report to be ready
            print("Waiting for the asset report to be ready...")
            logging.info("Waiting for the asset report to be ready...")
            time.sleep(60)  # Adjust as needed based on webhook or expected readiness time

            report = fetch_asset_report(asset_report_token)
        else:
            logging.error("Failed to create the asset report.")
            print("Failed to create the asset report.")
            sys.exit(1)

    if report:
        report = convert_datetimes(report)  # Convert datetime objects to ISO format before saving to JSON
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f'data/fetched-files/plaid_asset_report_{timestamp}.json'
        with open(filename, 'w') as file:
            json.dump(report, file, indent=4)
        logging.info(f"Asset report fetched and saved successfully as {filename}")
        print(f"Asset report fetched and saved successfully as {filename}")