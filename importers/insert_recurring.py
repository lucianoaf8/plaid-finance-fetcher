import os
import json
import logging
import mysql.connector
from mysql.connector import pooling
from urllib.parse import urlparse
from datetime import datetime
from dotenv import load_dotenv
import time

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
    filename=os.path.join(log_dir, f'insert_recurring_transactions_{today}.log'),
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s:%(message)s'
)

dbconfig = {
    "host": urlparse(MYSQL_URL).hostname,
    "port": urlparse(MYSQL_URL).port if urlparse(MYSQL_URL).port else 3306,
    "user": MYSQL_USER,
    "password": MYSQL_PASSWORD,
    "database": urlparse(MYSQL_URL).path.lstrip('/')
}

connection_pool = pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **dbconfig)

def get_db_connection():
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    cursor.execute("SET innodb_lock_wait_timeout = 120;")
    cursor.close()
    return conn

def is_file_imported(file_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM file_import_tracker WHERE file_name = %s", (file_name,))
    result = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return result > 0

def execute_with_retry(cursor, sql, params, max_retries=3, delay=5):
    for attempt in range(max_retries):
        try:
            cursor.execute(sql, params)
            return
        except mysql.connector.Error as e:
            if e.errno == 1205:  # Lock wait timeout exceeded
                if attempt < max_retries - 1:
                    logging.warning(f"Lock wait timeout exceeded, retrying in {delay} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                else:
                    raise
            else:
                raise

def insert_inflow_streams(cursor, stream, tracker_id):
    logging.info(f"About to insert inflow stream {stream['stream_id']}")
    print(f"About to insert inflow stream {stream['stream_id']}")
    
    # Check if the stream_id already exists in the inflow_streams table
    cursor.execute("SELECT COUNT(*) FROM inflow_streams WHERE stream_id = %s", (stream['stream_id'],))
    if cursor.fetchone()[0] == 0:
        execute_with_retry(cursor, """
            INSERT INTO inflow_streams (
                stream_id, account_id, category_id, description, merchant_name,
                first_date, last_date, frequency, average_amount, last_amount,
                is_active, status, is_user_modified, last_user_modified_datetime,
                pers_fin_primary_category, pers_fin_detailed_category, pers_fin_confidence_level, file_import_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            stream['stream_id'], stream['account_id'], stream['category_id'], stream['description'], stream['merchant_name'],
            stream['first_date'], stream['last_date'], stream['frequency'], stream['average_amount']['amount'], stream['last_amount']['amount'],
            stream['is_active'], stream['status'], stream['is_user_modified'], stream['last_user_modified_datetime'],
            stream['personal_finance_category']['primary'], stream['personal_finance_category']['detailed'], stream['personal_finance_category']['confidence_level'], tracker_id
        ))

        for transaction_id in stream['transaction_ids']:
            # Check if the transaction_id already exists in the inflow_transactions table
            cursor.execute("SELECT COUNT(*) FROM inflow_transactions WHERE transaction_id = %s", (transaction_id,))
            if cursor.fetchone()[0] == 0:
                execute_with_retry(cursor, """
                    INSERT INTO inflow_transactions (transaction_id, stream_id) VALUES (%s, %s)
                """, (transaction_id, stream['stream_id']))

def insert_outflow_streams(cursor, stream, tracker_id):
    logging.info(f"About to insert outflow stream {stream['stream_id']}")
    print(f"About to insert outflow stream {stream['stream_id']}")
    
    # Check if the stream_id already exists in the outflow_streams table
    cursor.execute("SELECT COUNT(*) FROM outflow_streams WHERE stream_id = %s", (stream['stream_id'],))
    if cursor.fetchone()[0] == 0:
        execute_with_retry(cursor, """
            INSERT INTO outflow_streams (
                stream_id, account_id, category_id, description, merchant_name,
                first_date, last_date, frequency, average_amount, last_amount,
                is_active, status, is_user_modified, last_user_modified_datetime,
                pers_fin_primary_category, pers_fin_detailed_category, pers_fin_confidence_level, file_import_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            stream['stream_id'], stream['account_id'], stream['category_id'], stream['description'], stream['merchant_name'],
            stream['first_date'], stream['last_date'], stream['frequency'], stream['average_amount']['amount'], stream['last_amount']['amount'],
            stream['is_active'], stream['status'], stream['is_user_modified'], stream['last_user_modified_datetime'],
            stream['personal_finance_category']['primary'], stream['personal_finance_category']['detailed'], stream['personal_finance_category']['confidence_level'], tracker_id
        ))

        for transaction_id in stream['transaction_ids']:
            # Check if the transaction_id already exists in the outflow_transactions table
            cursor.execute("SELECT COUNT(*) FROM outflow_transactions WHERE transaction_id = %s", (transaction_id,))
            if cursor.fetchone()[0] == 0:
                execute_with_retry(cursor, """
                    INSERT INTO outflow_transactions (transaction_id, stream_id) VALUES (%s, %s)
                """, (transaction_id, stream['stream_id']))

def insert_transactions(data, bank_name, file_name):
    logging.info(f"Loading file {file_name}")
    print(f"Loading file {file_name}")
    
    if is_file_imported(file_name):
        message = f"File {file_name} has already been imported. Skipping..."
        print(message)
        logging.info(message)
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        description = f"Transactions data for {bank_name} fetched at {timestamp}"

        logging.info(f"Inserting record into file_import_tracker for file {file_name}")
        print(f"Inserting record into file_import_tracker for file {file_name}")

        # Insert record in file_import_tracker
        execute_with_retry(cursor, """
            INSERT INTO file_import_tracker (file_name, description) 
            VALUES (%s, %s)
        """, (file_name, description))

        tracker_id = cursor.lastrowid

        logging.info(f"Processing inflow streams for {file_name}")
        print(f"Processing inflow streams for {file_name}")

        for stream in data['inflow_streams']:
            insert_inflow_streams(cursor, stream, tracker_id)

        logging.info(f"Processing outflow streams for {file_name}")
        print(f"Processing outflow streams for {file_name}")

        for stream in data['outflow_streams']:
            insert_outflow_streams(cursor, stream, tracker_id)

        conn.commit()
        message = f"Successfully inserted transactions for {bank_name} from {file_name}"
        print(message)
        logging.info(message)
    except Exception as e:
        conn.rollback()
        message = f"Error inserting transactions for {bank_name} from {file_name}: {e}"
        print(message)
        logging.error(message)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    fetched_files_dir = 'data/fetched-files'
    for file_name in os.listdir(fetched_files_dir):
        if file_name.startswith('plaid_recurring_transactions_') and file_name.endswith('.json'):
            bank_name = file_name.split('_')[2]  # Assuming the file name format is consistent
            with open(os.path.join(fetched_files_dir, file_name), 'r') as file:
                try:
                    transactions_data = json.load(file)
                    logging.info(f"Successfully loaded file {file_name}")
                    print(f"Successfully loaded file {file_name}")
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding JSON from file {file_name}: {e}")
                    print(f"Error decoding JSON from file {file_name}: {e}")
                    continue
            insert_transactions(transactions_data, bank_name, file_name)
