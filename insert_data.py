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

def account_exists(account_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM plaid_liabilities_credit WHERE account_id = %s", (account_id,))
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
            account_id = credit['account_id']
            if account_exists(account_id):
                message = f"Account ID {account_id} already exists. Skipping insertion."
                print(message)
                logging.info(message)
                continue

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
                account_id, is_overdue, last_payment_amount, last_payment_date,
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
                    account_id, apr_percentage, apr_type, 
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

def insert_transactions(data, bank_name, file_name):
    if is_file_imported(file_name):
        message = f"File {file_name} has already been imported. Skipping..."
        print(message)
        logging.info(message)
        return

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        description = f"Transactions data for {bank_name} fetched at {timestamp}"

        # Insert record in file_import_tracker
        cursor.execute("""
            INSERT INTO file_import_tracker (file_name, description) 
            VALUES (%s, %s)
        """, (file_name, description))

        tracker_id = cursor.lastrowid

        for transaction in data:
            params = (
                transaction['account_id'], transaction['transaction_id'], transaction.get('account_owner'), transaction['amount'],
                transaction.get('authorized_date'), transaction.get('authorized_datetime'), transaction['date'], transaction.get('datetime'),
                transaction['iso_currency_code'], transaction.get('logo_url'), transaction.get('merchant_entity_id'), transaction.get('merchant_name'),
                transaction['name'], transaction['payment_channel'], transaction['pending'], transaction.get('pending_transaction_id'),
                transaction.get('transaction_code'), transaction['transaction_type'], transaction.get('unofficial_currency_code'),
                ", ".join(transaction['category']), transaction['category_id'], transaction['personal_finance_category'].get('confidence_level'),
                transaction['personal_finance_category'].get('detailed'), transaction['personal_finance_category'].get('primary'),
                transaction['personal_finance_category_icon_url'], transaction['location'].get('address'), transaction['location'].get('city'),
                transaction['location'].get('region'), transaction['location'].get('postal_code'), transaction['location'].get('country'),
                transaction['location'].get('lat'), transaction['location'].get('lon'), transaction['location'].get('store_number'),
                transaction['payment_meta'].get('reference_number'), transaction['payment_meta'].get('ppd_id'),
                transaction['payment_meta'].get('payee'), transaction['payment_meta'].get('by_order_of'), transaction['payment_meta'].get('payer'),
                transaction['payment_meta'].get('payment_method'), transaction['payment_meta'].get('payment_processor'),
                transaction['payment_meta'].get('reason'), transaction.get('website'), transaction.get('check_number'), tracker_id
            )
            
            cursor.execute("""
                INSERT INTO plaid_transactions (
                    account_id, transaction_id, account_owner, amount, 
                    authorized_date, authorized_datetime, date, datetime, 
                    iso_currency_code, logo_url, merchant_entity_id, merchant_name, 
                    name, payment_channel, pending, pending_transaction_id, 
                    transaction_code, transaction_type, unofficial_currency_code, 
                    category, category_id, personal_finance_category_confidence_level, 
                    personal_finance_category_detailed, personal_finance_category_primary, 
                    personal_finance_category_icon_url, location_address, 
                    location_city, location_region, location_postal_code, 
                    location_country, location_lat, location_lon, location_store_number, 
                    payment_meta_reference_number, payment_meta_ppd_id, 
                    payment_meta_payee, payment_meta_by_order_of, payment_meta_payer, 
                    payment_meta_payment_method, payment_meta_payment_processor, 
                    payment_meta_reason, website, check_number, file_import_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, params)

            for counterparty in transaction['counterparties']:
                cursor.execute("""
                    INSERT INTO plaid_transaction_counterparties (
                        transaction_id, name, type, website, logo_url, 
                        confidence_level, entity_id, phone_number
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    transaction['transaction_id'], counterparty.get('name'), counterparty.get('type'), counterparty.get('website'),
                    counterparty.get('logo_url'), counterparty.get('confidence_level'), counterparty.get('entity_id'), counterparty.get('phone_number')
                ))

        conn.commit()
        message = f"Successfully inserted transactions for {bank_name} from {file_name}"
        print(message)
        logging.info(message)
    except Exception as e:
        message = f"Error inserting transactions for {bank_name} from {file_name}: {e}"
        print(message)
        logging.error(message)
    finally:
        cursor.close()
        conn.close()

def import_files():
    fetched_files_dir = 'data/fetched-files/'
    for file_name in os.listdir(fetched_files_dir):
        if file_name.startswith("plaid_liabilities_") and file_name.endswith(".json"):
            print(f"Processing file: {file_name}")
            logging.info(f"Processing file: {file_name}")
            try:
                with open(fetched_files_dir + file_name) as file:
                    data = json.load(file)
                    bank_name = file_name.split("_")[2].replace(".json", "")
                    # insert_liabilities(data, bank_name, file_name)
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
                    insert_transactions(data, bank_name, file_name)
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
