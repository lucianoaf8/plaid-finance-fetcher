import os
import logging
import mysql.connector
from mysql.connector import pooling
from urllib.parse import urlparse
from datetime import datetime
from dotenv import load_dotenv
import csv

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
    filename=os.path.join(log_dir, f'insert_triangle_{today}.log'),
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
    return connection_pool.get_connection()

def is_file_imported(file_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM file_import_tracker WHERE file_name = %s", (file_name,))
    result = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return result > 0

def insert_triangle_data(file_path, file_name):
    if is_file_imported(file_name):
        message = f"File {file_name} has already been imported. Skipping..."
        print(message)
        logging.info(message)
        return
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        description = f"Triangle card data fetched at {timestamp}"

        # Insert record in file_import_tracker
        cursor.execute("""
            INSERT INTO file_import_tracker (file_name, description) 
            VALUES (%s, %s)
        """, (file_name, description))

        tracker_id = cursor.lastrowid

        # Read the CSV file
        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            
            # Skip header rows
            next(reader)  # Skip 'MY ACCOUNT TRANSACTIONS'
            next(reader)  # Skip summary headers
            summary_row = next(reader)  # Read summary row
            next(reader)  # Skip transaction headers

            # Extract summary data
            start_date, end_date, current_balance, available_credit = summary_row

            cursor.execute("""
                INSERT INTO triangle_card_statements (
                    start_date, end_date, current_balance, available_credit, file_import_id
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                start_date, end_date, current_balance, available_credit, tracker_id
            ))

            statement_id = cursor.lastrowid

            # Process transactions
            for transaction_row in reader:
                if len(transaction_row) < 7:
                    continue

                ref, transaction_date, posted_date, type_, description, category, amount = transaction_row

                cursor.execute("""
                    INSERT INTO triangle_card_transactions (
                        ref, transaction_date, posted_date, type, description, category, amount, 
                        statement_id, file_import_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    ref, transaction_date, posted_date, type_, description, category, amount, 
                    statement_id, tracker_id
                ))

        conn.commit()
        message = f"Successfully inserted Triangle card data from {file_name}"
        print(message)
        logging.info(message)
    except Exception as e:
        conn.rollback()
        message = f"Error inserting Triangle card data from {file_name}: {e}"
        print(message)
        logging.error(message)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    fetched_files_dir = 'data/triangle-files'
    for file_name in os.listdir(fetched_files_dir):
        if file_name.endswith('.csv'):
            file_path = os.path.join(fetched_files_dir, file_name)
            insert_triangle_data(file_path, file_name)
