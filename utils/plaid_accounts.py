import os
import json
import logging
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.api_client import ApiException
from plaid.model.accounts_get_request import AccountsGetRequest
from datetime import datetime
from urllib.parse import urlparse
from mysql.connector import pooling

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

def store_accounts_in_db(accounts, access_token, institution_name, institution_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        for account in accounts:
            account_id = account['account_id']
            name = account['name']
            official_name = account.get('official_name', '')
            type_ = str(account['type'])
            subtype = str(account['subtype'])
            balances = json.dumps(account['balances'].to_dict())
            mask = account['mask']
            verification_status = account.get('verification_status', '')

            cursor.execute("""
                INSERT INTO plaid_accounts (
                    account_id, access_token, institution_id, institution_name, 
                    account_name, official_name, account_type, account_subtype, 
                    balances, mask, verification_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    access_token=VALUES(access_token),
                    institution_id=VALUES(institution_id),
                    institution_name=VALUES(institution_name),
                    account_name=VALUES(account_name),
                    official_name=VALUES(official_name),
                    account_type=VALUES(account_type),
                    account_subtype=VALUES(account_subtype),
                    balances=VALUES(balances),
                    mask=VALUES(mask),
                    verification_status=VALUES(verification_status),
                    updated_at=VALUES(updated_at)
            """, (
                account_id, access_token, institution_id, institution_name,
                name, official_name, type_, subtype, balances, mask, verification_status
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
        cursor.execute("SELECT DISTINCT access_token, institution_name, institution_id FROM plaid_accounts")
        tokens = cursor.fetchall()
        cursor.close()
        conn.close()
        return tokens
    except Exception as e:
        print(f"Error fetching access tokens from database: {e}")
        logging.error(f"Error fetching access tokens from database: {e}")
        return []

if __name__ == "__main__":
    new_account_token = os.getenv("NEW_ACCOUNT_TOKEN")
    new_institution_name = os.getenv("NEW_BANK_NAME")
    new_institution_id = os.getenv("NEW_BANK_ID")
    
    print(f"Starting accounts fetch process...")
    logging.info(f"Starting accounts fetch process...")

    tokens = get_access_tokens_from_db()
    
    for token in tokens:
        access_token = token['access_token']
        institution_name = token['institution_name']
        institution_id = token['institution_id']
        
        if access_token:
            accounts = fetch_account_info(access_token)
            if accounts:
                store_accounts_in_db(accounts, access_token, institution_name, institution_id)
        else:
            message = f"Access token for {institution_name} is missing."
            print(message)
            logging.error(message)
    
    if new_account_token:
        accounts = fetch_account_info(new_account_token)
        if accounts:
            store_accounts_in_db(accounts, new_account_token, new_institution_name,new_institution_id)
    
    print("Accounts fetch process completed.")
    logging.info("Accounts fetch process completed.")
