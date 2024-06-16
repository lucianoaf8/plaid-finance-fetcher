import os
import json
import logging
import mysql.connector
from urllib.parse import urlparse
from datetime import datetime
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
    filename=os.path.join(log_dir, f'insert_liabilities_{today}.log'),
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

def insert_liabilities(data, bank_name, file_name):
    if is_file_imported(file_name):
        message = f"File {file_name} has already been imported. Skipping..."
        print(message)
        logging.info(message)
        return
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        description = f"Liabilities data for {bank_name} fetched at {timestamp}"

        # Insert record in file_import_tracker
        cursor.execute("""
            INSERT INTO file_import_tracker (file_name, description) 
            VALUES (%s, %s)
        """, (file_name, description))

        tracker_id = cursor.lastrowid

        for credit in data['credit']:
            transaction_id = credit['account_id']  # Assuming transaction_id is mapped from account_id or similar
            
            # Check if transaction exists
            cursor.execute("SELECT COUNT(*) FROM plaid_liabilities_credit WHERE account_id = %s", (transaction_id,))
            transaction_exists = cursor.fetchone()[0] > 0

            if transaction_exists:
                # Move existing data to history table
                cursor.execute("""
                    INSERT INTO plaid_liabilities_credit_history (account_id, is_overdue, last_payment_amount, last_payment_date, 
                        last_statement_issue_date, last_statement_balance, minimum_payment_amount, next_payment_due_date, file_import_id)
                    SELECT account_id, is_overdue, last_payment_amount, last_payment_date, last_statement_issue_date, last_statement_balance, 
                        minimum_payment_amount, next_payment_due_date, %s 
                    FROM plaid_liabilities_credit WHERE account_id = %s
                """, (tracker_id, transaction_id))
                cursor.execute("""
                    INSERT INTO plaid_liabilities_credit_apr_history (account_id, apr_percentage, apr_type, balance_subject_to_apr, 
                        interest_charge_amount, file_import_id)
                    SELECT account_id, apr_percentage, apr_type, balance_subject_to_apr, interest_charge_amount, %s 
                    FROM plaid_liabilities_credit_apr WHERE account_id = %s
                """, (tracker_id, transaction_id))

                # Delete existing data
                cursor.execute("DELETE FROM plaid_liabilities_credit_apr WHERE account_id = %s", (transaction_id,))
                cursor.execute("DELETE FROM plaid_liabilities_credit WHERE account_id = %s", (transaction_id,))

            is_overdue = credit['is_overdue']
            last_payment_amount = credit['last_payment_amount']
            last_payment_date = credit['last_payment_date']
            last_statement_issue_date = credit['last_statement_issue_date']
            last_statement_balance = credit['last_statement_balance']
            minimum_payment_amount = credit['minimum_payment_amount']
            next_payment_due_date = credit['next_payment_due_date']

            cursor.execute("""
                INSERT INTO plaid_liabilities_credit (
                    account_id, is_overdue, last_payment_amount, last_payment_date, 
                    last_statement_issue_date, last_statement_balance, 
                    minimum_payment_amount, next_payment_due_date, file_import_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                transaction_id, is_overdue, last_payment_amount, last_payment_date,
                last_statement_issue_date, last_statement_balance, 
                minimum_payment_amount, next_payment_due_date, tracker_id
            ))

            for apr in credit['aprs']:
                apr_percentage = apr['apr_percentage']
                apr_type = apr['apr_type']
                balance_subject_to_apr = apr['balance_subject_to_apr']
                interest_charge_amount = apr['interest_charge_amount']

                cursor.execute("""
                    INSERT INTO plaid_liabilities_credit_apr (
                        account_id, apr_percentage, apr_type, 
                        balance_subject_to_apr, interest_charge_amount, file_import_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    transaction_id, apr_percentage, apr_type, 
                    balance_subject_to_apr, interest_charge_amount, tracker_id
                ))

        conn.commit()
        message = f"Successfully inserted liabilities for {bank_name} from {file_name}"
        print(message)
        logging.info(message)
    except Exception as e:
        message = f"Error inserting liabilities for {bank_name} from {file_name}: {e}"
        print(message)
        logging.error(message)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # This part allows the script to be run independently
    fetched_files_dir = 'data/fetched-files'
    for file_name in os.listdir(fetched_files_dir):
        if file_name.startswith('plaid_liabilities_') and file_name.endswith('.json'):
            bank_name = file_name.split('_')[2]  # Assuming the file name format is consistent
            with open(os.path.join(fetched_files_dir, file_name), 'r') as file:
                liabilities_data = json.load(file)
            insert_liabilities(liabilities_data, bank_name, file_name)