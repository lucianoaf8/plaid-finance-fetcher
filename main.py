import os
import logging
import json
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

dbconfig = {
    "host": urlparse(os.getenv("MYSQL_URL")).hostname,
    "port": urlparse(os.getenv("MYSQL_URL")).port if urlparse(os.getenv("MYSQL_URL")).port else 3306,
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": urlparse(os.getenv("MYSQL_URL")).path.lstrip('/')
}

def get_db_connection():
    return mysql.connector.connect(**dbconfig)

def get_access_tokens_from_db():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT access_token, bank_name FROM plaid_accounts where bank_name = 'CIBC'")
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
        if transactions_file:
            try:
                with open(transactions_file, 'r') as file:
                    transactions_data = json.load(file)
                insert_transactions.insert_transactions(transactions_data, bank_name, os.path.basename(transactions_file))
            except Exception as e:
                logging.error(f"Error inserting transactions for {bank_name} from {transactions_file}: {e}")
                print(f"Error inserting transactions for {bank_name} from {transactions_file}: {e}")

        # Fetch liabilities
        liabilities_file = fetch_liabilities.fetch_liabilities(access_token, bank_name)
        if liabilities_file:
            try:
                with open(liabilities_file, 'r') as file:
                    liabilities_data = json.load(file)
                insert_liabilities.insert_liabilities(liabilities_data, bank_name, os.path.basename(liabilities_file))
            except Exception as e:
                logging.error(f"Error inserting liabilities for {bank_name} from {liabilities_file}: {e}")
                print(f"Error inserting liabilities for {bank_name} from {liabilities_file}: {e}")

    print("Fetch and import process completed.")
    logging.info("Fetch and import process completed.")
