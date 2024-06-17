import os
import json
import logging
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.model.accounts_get_request import AccountsGetRequest
from datetime import datetime
from urllib.parse import urlparse
import mysql.connector

# Load environment variables from .env file
load_dotenv()

# Fetch access tokens for multiple accounts from environment variables
access_tokens = {
    "CIBC": os.getenv("ACCESS_TOKEN_CIBC"),
    "Tangerine": os.getenv("ACCESS_TOKEN_TANGERINE"),
    # "Triangle": os.getenv("ACCESS_TOKEN_TRIANGLE"),
    # "MBNA": os.getenv("ACCESS_TOKEN_MBNA")
}

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

# Set up logging
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

today = datetime.now().strftime('%Y-%m-%d')
logging.basicConfig(
    filename=os.path.join(log_dir, f'plaid_accounts_{today}.log'),
    level=logging.INFO,  # Change to INFO level for normal output
    format='%(asctime)s %(levelname)s:%(message)s'
)

def get_db_connection():
    MYSQL_URL = os.getenv("MYSQL_URL")
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")

    url = urlparse(MYSQL_URL)
    return mysql.connector.connect(
        host=url.hostname,
        port=url.port if url.port else 3306,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=url.path.lstrip('/')
    )

def fetch_account_info(access_token):
    try:
        request = AccountsGetRequest(
            access_token=access_token
        )
        response = client.accounts_get(request)
        return response['accounts']
    except Exception as e:
        message = f"Error fetching account information: {e}"
        print(message)
        logging.error(message)
        return []

def store_accounts_in_db(accounts, access_token, bank_name):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        for account in accounts:
            # Sanitize account data
            account_id = account['account_id']
            name = account['name']
            official_name = account.get('official_name', '')
            type_ = str(account['type'])  # Convert to string
            subtype = str(account['subtype'])  # Convert to string
            last_fetch_date = None  # Initialize last_fetch_date as None

            cursor.execute("""
                INSERT INTO plaid_accounts (account_id, name, official_name, type, subtype, bank_name, access_token, last_fetch_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE name=VALUES(name), official_name=VALUES(official_name), type=VALUES(type), subtype=VALUES(subtype), bank_name=VALUES(bank_name), last_fetch_date=VALUES(last_fetch_date)
            """, (
                account_id, name, official_name, 
                type_, subtype, bank_name, access_token, last_fetch_date
            ))

        conn.commit()
        cursor.close()
        conn.close()

        # Convert account data to JSON serializable format
        accounts_json_serializable = []
        for account in accounts:
            account_dict = {
                'account_id': account['account_id'],
                'name': account['name'],
                'official_name': account.get('official_name', ''),
                'type': str(account['type']),
                'subtype': str(account['subtype']),
                'bank_name': bank_name,
                'access_token': access_token,
                'last_fetch_date': last_fetch_date
            }
            accounts_json_serializable.append(account_dict)

        # Save accounts to JSON file
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f'data/fetched-files/plaid_accounts_{timestamp}.json'
        with open(filename, 'w') as file:
            json.dump(accounts_json_serializable, file, indent=4)

        message = f"Successfully stored account information in the database and saved as {filename}."
        print(message)
        logging.info(message)
    except Exception as e:
        message = f"Error storing account information in the database: {e}"
        print(message)
        logging.error(message)

if __name__ == "__main__":
    print(f"Starting accounts fetch process...")
    logging.info(f"Starting accounts fetch process...")
    for bank_name, access_token in access_tokens.items():
        if access_token:
            accounts = fetch_account_info(access_token)
            store_accounts_in_db(accounts, access_token, bank_name)
        else:
            message = f"Access token for {bank_name} is missing."
            print(message)
            logging.error(message)
    print("Accounts fetch process completed.")
    logging.info("Accounts fetch process completed.")
