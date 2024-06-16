import os
import logging
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import urlparse
import mysql.connector
import fetchers.plaid_transactions as fetch_transactions
import fetchers.plaid_liabilities as fetch_liabilities
import importers.insert_transactions as insert_transactions
import importers.insert_liabilities as insert_liabilities

# Load environment variables from .env file
load_dotenv()

# Set up logging
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

today = datetime.now().strftime('%Y-%m-%d')
logging.basicConfig(
    filename=os.path.join(log_dir, f'main_{today}.log'),
    level=logging.INFO,
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

def get_access_tokens_from_db():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT access_token, bank_name FROM plaid_accounts")
    tokens = cursor.fetchall()
    cursor.close()
    conn.close()
    return tokens

if __name__ == "__main__":
    print("Starting fetch and import process...")
    logging.info("Starting fetch and import process...")
    tokens = get_access_tokens_from_db()
    for token in tokens:
        access_token = token['access_token']
        bank_name = token['bank_name']

        # Fetch transactions
        transactions_file = fetch_transactions.fetch_transactions(access_token, bank_name)
        # Fetch liabilities
        liabilities_file = fetch_liabilities.fetch_liabilities(access_token, bank_name)

        # Import transactions
        if transactions_file:
            insert_transactions.insert_transactions(transactions_file, bank_name, transactions_file)
        # Import liabilities
        if liabilities_file:
            insert_liabilities.insert_liabilities(liabilities_file, bank_name, liabilities_file)

    print("Fetch and import process completed.")
    logging.info("Fetch and import process completed.")
