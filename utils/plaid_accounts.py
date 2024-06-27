import os
import json
import logging
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.model.accounts_get_request import AccountsGetRequest
from datetime import datetime
from urllib.parse import urlparse
from mysql.connector import pooling
from decimal import Decimal
from plaid.api_client import ApiException

# Load environment variables from .env file
load_dotenv()

# Set up logging
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

today = datetime.now().strftime('%Y-%m-%d')
logging.basicConfig(
    filename=os.path.join(log_dir, f'plaid_accounts_{today}.log'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

# Database connection pool
MYSQL_URL = os.getenv("MYSQL_URL")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")

url = urlparse(MYSQL_URL)
connection_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    host=url.hostname,
    port=url.port if url.port else 3306,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=url.path.lstrip('/')
)

def get_db_connection():
    return connection_pool.get_connection()

# Plaid configuration
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

def fetch_account_info(access_token):
    try:
        request = AccountsGetRequest(access_token=access_token)
        response = client.accounts_get(request)
        accounts = response['accounts']
        return accounts
    except ApiException as e:
        error_response = json.loads(e.body)
        print(f"Error fetching account information: {error_response}")
        logging.error(f"Error fetching account information: {error_response}")
        return None

def store_accounts_in_db(accounts, bank_name):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        for account in accounts:
            account_id = account['account_id']
            available_balance = Decimal(account['balances'].get('available', 0)) if account['balances'].get('available') is not None else None
            current_balance = Decimal(account['balances'].get('current', 0)) if account['balances'].get('current') is not None else None
            balance_limit = Decimal(account['balances'].get('limit', 0)) if account['balances'].get('limit') is not None else None
            iso_currency_code = account['balances'].get('iso_currency_code', None)
            unofficial_currency_code = account['balances'].get('unofficial_currency_code', None)
            mask = account.get('mask', None)
            name = account.get('name', '')
            official_name = account.get('official_name', '')
            type_ = str(account.get('type', ''))
            subtype = str(account.get('subtype', ''))

            cursor.execute("""
                INSERT INTO plaid_accounts (
                    account_id, bank_name, available_balance, current_balance, balance_limit,
                    iso_currency_code, unofficial_currency_code, mask, name, 
                    official_name, type, subtype
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    bank_name=VALUES(bank_name),
                    available_balance=VALUES(available_balance),
                    current_balance=VALUES(current_balance),
                    balance_limit=VALUES(balance_limit),
                    iso_currency_code=VALUES(iso_currency_code),
                    unofficial_currency_code=VALUES(unofficial_currency_code),
                    mask=VALUES(mask),
                    name=VALUES(name),
                    official_name=VALUES(official_name),
                    type=VALUES(type),
                    subtype=VALUES(subtype),
                    updated_at=VALUES(updated_at)
            """, (
                account_id, bank_name, available_balance, current_balance, balance_limit,
                iso_currency_code, unofficial_currency_code, mask, name, 
                official_name, type_, subtype
            ))

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error storing account information in the database: {e}")
        logging.error(f"Error storing account information in the database: {e}")

def get_access_tokens_from_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT access_token, bank_name, bank_id FROM finance.plaid_access_tokens WHERE bank_name LIKE '%Tangerine%'")
        tokens = cursor.fetchall()
        cursor.close()
        conn.close()
        return tokens
    except Exception as e:
        print(f"Error fetching access tokens from database: {e}")
        logging.error(f"Error fetching access tokens from database: {e}")
        return []

if __name__ == "__main__":
    print(f"Starting accounts fetch process...")
    logging.info(f"Starting accounts fetch process...")

    tokens = get_access_tokens_from_db()
    
    for token in tokens:
        access_token = token['access_token']
        bank_name = token['bank_name']
        bank_id = token['bank_id']
        
        if access_token:
            accounts = fetch_account_info(access_token)
            if accounts:
                store_accounts_in_db(accounts, bank_name)

                accounts_dict = [account.to_dict() for account in accounts]
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f'data/fetched-files/plaid_accounts_{bank_name}_{timestamp}.json'
                with open(filename, 'w') as file:
                    json.dump(accounts_dict, file)
        else:
            message = f"Access token for {bank_name} is missing."
            print(message)
            logging.error(message)
    
    print("Accounts fetch process completed.")
    logging.info("Accounts fetch process completed.")
