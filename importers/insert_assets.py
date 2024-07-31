import os
import json
import logging
from mysql.connector import pooling, IntegrityError
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
    filename=os.path.join(log_dir, f'insert_assets_{today}.log'),
    level=logging.INFO,
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
    file_name = os.path.abspath(file_name)  # Convert to absolute path
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM asset_report WHERE file_path = %s", (file_name,))
    result = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return result > 0

# Function to insert data into asset_report table
def insert_asset_report(report, file_path):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
    INSERT INTO asset_report (asset_report_id, client_report_id, date_generated, days_requested, file_path)
    VALUES (%s, %s, %s, %s, %s)
    """
    # Read the entire JSON file content
    with open(file_path, 'r') as file:
        json_content = json.load(file)

    values = (
        report['asset_report_id'],
        report.get('client_report_id'),
        datetime.fromisoformat(report['date_generated'].replace('Z', '')),
        int(report['days_requested']),
        os.path.abspath(file_path),  # Use absolute path to store the full file path
    )
    try:
        cursor.execute(sql, values)
        conn.commit()
        logging.info(f"Asset report inserted successfully: {report['asset_report_id']} from file {file_path}")
        print("Asset report inserted successfully!")
    except IntegrityError as e:
        logging.error(f"Duplicate entry for asset report: {report['asset_report_id']} - {e}")
        print(f"Duplicate entry for asset report: {report['asset_report_id']} - {e}")
    finally:
        cursor.close()
        conn.close()

# Function to insert data into item table
def insert_item(item, asset_report_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
    INSERT INTO asset_item (item_id, asset_report_id, institution_name, institution_id, date_last_updated)
    VALUES (%s, %s, %s, %s, %s)
    """
    values = (
        item['item_id'],
        asset_report_id,
        item['institution_name'],
        item['institution_id'],
        datetime.fromisoformat(item['date_last_updated'].replace('Z', ''))
    )
    try:
        cursor.execute(sql, values)
        conn.commit()
        logging.info(f"Item inserted successfully: {item['item_id']} for asset report: {asset_report_id}")
        print("Item inserted successfully!")
    except IntegrityError as e:
        logging.error(f"Duplicate entry for item: {item['item_id']} - {e}")
        print(f"Duplicate entry for item: {item['item_id']} - {e}")
    finally:
        cursor.close()
        conn.close()

# Function to insert data into account table
def insert_account(account, item_id, asset_report_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    balances = account['balances']
    sql = """
    INSERT INTO asset_account (account_id, item_id, available, current, `limit`, margin_loan_amount, iso_currency_code,
                         unofficial_currency_code, mask, name, official_name, type, subtype, days_available, asset_report_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        account['account_id'],
        item_id,
        balances['available'],
        balances['current'],
        balances.get('limit'),
        balances.get('margin_loan_amount'),
        balances['iso_currency_code'],
        balances.get('unofficial_currency_code'),
        account['mask'],
        account['name'],
        account['official_name'],
        account['type'],
        account['subtype'],
        int(account['days_available']),
        asset_report_id
    )
    try:
        cursor.execute(sql, values)
        conn.commit()
        logging.info(f"Account inserted successfully: {account['account_id']} for item: {item_id}")
        print("Account inserted successfully!")
    except IntegrityError as e:
        logging.error(f"Duplicate entry for account: {account['account_id']} - {e}")
        print(f"Duplicate entry for account: {account['account_id']} - {e}")
    finally:
        cursor.close()
        conn.close()

# Function to insert data into transaction table
def insert_transaction(transaction, asset_report_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
    INSERT INTO asset_transaction (transaction_id, account_id, amount, iso_currency_code, unofficial_currency_code,
                             original_description, date, pending, asset_report_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        transaction['transaction_id'],
        transaction['account_id'],
        transaction['amount'],
        transaction['iso_currency_code'],
        transaction.get('unofficial_currency_code'),
        transaction['original_description'],
        transaction['date'],
        transaction['pending'],
        asset_report_id
    )
    try:
        cursor.execute(sql, values)
        conn.commit()
        print("Transaction inserted successfully!")
    except IntegrityError as e:
        logging.error(f"Duplicate entry for transaction: {transaction['transaction_id']} - {e}")
        print(f"Duplicate entry for transaction: {transaction['transaction_id']} - {e}")
    finally:
        cursor.close()
        conn.close()

# Function to insert data into historical_balance table
def insert_historical_balance(balance, account_id, asset_report_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
    INSERT INTO asset_historical_balance (account_id, date, current, iso_currency_code, unofficial_currency_code, asset_report_id)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    values = (
        account_id,
        balance['date'],
        balance['current'],
        balance['iso_currency_code'],
        balance.get('unofficial_currency_code'),
        asset_report_id
    )
    try:
        cursor.execute(sql, values)
        conn.commit()
        print("Historical balance inserted successfully!")
    except IntegrityError as e:
        logging.error(f"Duplicate entry for historical balance for account: {account_id} on date: {balance['date']} - {e}")
        print(f"Duplicate entry for historical balance for account: {account_id} on date: {balance['date']} - {e}")
    finally:
        cursor.close()
        conn.close()

# Function to process the JSON file and insert data into the database
def process_json_file(filepath):
    logging.info(f"Loading file: {filepath}")
    print(f"Loading file: {filepath}")
    
    if not os.path.exists(filepath):
        logging.error(f"File not found: {filepath}")
        print(f"File not found: {filepath}")
        return

    logging.info(f"Processing file: {os.path.abspath(filepath)}")
    print(f"Processing file: {os.path.abspath(filepath)}")

    if is_file_imported(filepath):
        logging.info(f"File already inserted. Skipping: {filepath}")
        print(f"File already inserted. Skipping: {filepath}")
        return

    with open(filepath, 'r') as file:
        data = json.load(file)
        report = data['report']

        logging.info("Inserting asset report")
        print("Inserting asset report")
        insert_asset_report(report, filepath)

        logging.info("Inserting items")
        print("Inserting items")
        for item in report['items']:
            insert_item(item, report['asset_report_id'])

            logging.info("Inserting accounts")
            print("Inserting accounts")
            for account in item['accounts']:
                insert_account(account, item['item_id'], report['asset_report_id'])

                logging.info("Inserting transactions")
                print("Inserting transactions")
                for transaction in account['transactions']:
                    insert_transaction(transaction, report['asset_report_id'])

                logging.info("Inserting historical balances")
                print("Inserting historical balances")
                for balance in account['historical_balances']:
                    insert_historical_balance(balance, account['account_id'], report['asset_report_id'])

# Main function to iterate through JSON files in the specified directory
def main():
    directory = 'data/fetched-files'

    for filename in os.listdir(directory):
        if filename.startswith('plaid_asset_report_') and filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            try:
                process_json_file(filepath)
                logging.info(f'Successfully processed file: {os.path.abspath(filepath)}')
                print(f'Successfully processed file: {os.path.abspath(filepath)}')
            except IntegrityError as e:
                logging.error(f"Duplicate entry found when processing file {os.path.abspath(filepath)}: {e}")
                print(f"Duplicate entry found when processing file {os.path.abspath(filepath)}: {e}")
            except Exception as e:
                logging.error(f'Error processing file {os.path.abspath(filepath)}: {e}')
                print(f'Error processing file {os.path.abspath(filepath)}: {e}')

if __name__ == "__main__":
    main()
