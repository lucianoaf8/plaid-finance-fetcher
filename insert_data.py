import os
import json
import logging
from datetime import datetime
from importers import insert_transactions
from importers import insert_liabilities
from urllib.parse import urlparse
import mysql.connector
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

MYSQL_URL = os.getenv("MYSQL_URL")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")

# Set up logging
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

today = datetime.now().strftime('%Y-%m-%d')
logging.basicConfig(
    filename=os.path.join(log_dir, f'insert_data_{today}.log'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

def get_db_connection():
    url = urlparse(MYSQL_URL)
    return mysql.connector.connect(
        host=url.hostname,
        port=url.port if url.port else 3306,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=url.path.lstrip('/'),
        use_pure=True
    )

def is_file_imported(file_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM file_import_tracker WHERE file_name = %s", (file_name,))
    result = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return result > 0

def import_files():
    fetched_files_dir = 'data/fetched-files/'
    for file_name in os.listdir(fetched_files_dir):
        if is_file_imported(file_name):
            message = f"File {file_name} has already been imported. Skipping..."
            print(message)
            logging.info(message)
            continue

        if file_name.startswith("plaid_liabilities_") and file_name.endswith(".json"):
            print(f"Processing file: {file_name}")
            logging.info(f"Processing file: {file_name}")
            try:
                with open(fetched_files_dir + file_name) as file:
                    data = json.load(file)
                    bank_name = file_name.split("_")[2].replace(".json", "")
                    insert_liabilities.insert_liabilities(data, bank_name, file_name)
            except json.JSONDecodeError as e:
                message = f"Error decoding JSON from file {file_name}: {e}"
                print(message)
                logging.error(message)
        elif file_name.startswith("plaid_transactions_") and file_name.endswith(".json"):
            print(f"Processing file: {file_name}")
            logging.info(f"Processing file: {file_name}")
            try:
                with open(fetched_files_dir + file_name) as file:
                    data = json.load(file)
                    bank_name = file_name.split("_")[2].replace(".json", "")
                    insert_transactions.insert_transactions(data, bank_name, file_name)
            except json.JSONDecodeError as e:
                message = f"Error decoding JSON from file {file_name}: {e}"
                print(message)
                logging.error(message)

if __name__ == "__main__":
    print("Starting import process...")
    logging.info("Starting import process...")
    import_files()
    print("Import process completed.")
    logging.info("Import process completed.")
