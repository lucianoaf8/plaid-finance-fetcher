import os
import json
import logging
import mysql.connector
from mysql.connector import pooling
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
    filename=os.path.join(log_dir, f'insert_transactions_{today}.log'),
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
            transaction_id = transaction['transaction_id']

            # Check if transaction exists
            cursor.execute("SELECT COUNT(*) FROM plaid_transactions WHERE transaction_id = %s", (transaction_id,))
            transaction_exists = cursor.fetchone()[0] > 0

            if transaction_exists:
                # Move existing data to history table
                cursor.execute("""
                    INSERT INTO plaid_transactions_history (
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
                    )
                    SELECT 
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
                        payment_meta_reason, website, check_number, %s 
                    FROM plaid_transactions WHERE transaction_id = %s
                """, (tracker_id, transaction_id))

                cursor.execute("""
                    INSERT INTO plaid_transaction_counterparties_history (
                        transaction_id, name, type, website, logo_url, 
                        confidence_level, entity_id, phone_number, file_import_id
                    )
                    SELECT 
                        transaction_id, name, type, website, logo_url, 
                        confidence_level, entity_id, phone_number, %s 
                    FROM plaid_transaction_counterparties WHERE transaction_id = %s
                """, (tracker_id, transaction_id))

                # Delete existing data
                cursor.execute("DELETE FROM plaid_transaction_counterparties WHERE transaction_id = %s", (transaction_id,))
                cursor.execute("DELETE FROM plaid_transactions WHERE transaction_id = %s", (transaction_id,))

            params = {
                'account_id': transaction['account_id'], 
                'transaction_id': transaction['transaction_id'], 
                'account_owner': transaction.get('account_owner', None), 
                'amount': transaction['amount'],
                'authorized_date': transaction.get('authorized_date', None), 
                'authorized_datetime': transaction.get('authorized_datetime', None), 
                'date': transaction['date'], 
                'datetime': transaction.get('datetime', None),
                'iso_currency_code': transaction['iso_currency_code'], 
                'logo_url': transaction.get('logo_url', None), 
                'merchant_entity_id': transaction.get('merchant_entity_id', None), 
                'merchant_name': transaction.get('merchant_name', None),
                'name': transaction['name'], 
                'payment_channel': transaction['payment_channel'], 
                'pending': transaction['pending'], 
                'pending_transaction_id': transaction.get('pending_transaction_id', None),
                'transaction_code': transaction.get('transaction_code', None), 
                'transaction_type': transaction['transaction_type'], 
                'unofficial_currency_code': transaction.get('unofficial_currency_code', None),
                'category': ", ".join(transaction['category']), 
                'category_id': transaction['category_id'], 
                'personal_finance_category_confidence_level': transaction.get('personal_finance_category', {}).get('confidence_level', None),
                'personal_finance_category_detailed': transaction.get('personal_finance_category', {}).get('detailed', None), 
                'personal_finance_category_primary': transaction.get('personal_finance_category', {}).get('primary', None),
                'personal_finance_category_icon_url': transaction.get('personal_finance_category_icon_url', None), 
                'location_address': transaction['location'].get('address', None), 
                'location_city': transaction['location'].get('city', None),
                'location_region': transaction['location'].get('region', None), 
                'location_postal_code': transaction['location'].get('postal_code', None), 
                'location_country': transaction['location'].get('country', None),
                'location_lat': transaction['location'].get('lat', None), 
                'location_lon': transaction['location'].get('lon', None), 
                'location_store_number': transaction['location'].get('store_number', None),
                'payment_meta_reference_number': transaction['payment_meta'].get('reference_number', None), 
                'payment_meta_ppd_id': transaction['payment_meta'].get('ppd_id', None),
                'payment_meta_payee': transaction['payment_meta'].get('payee', None), 
                'payment_meta_by_order_of': transaction['payment_meta'].get('by_order_of', None), 
                'payment_meta_payer': transaction['payment_meta'].get('payer', None),
                'payment_meta_payment_method': transaction['payment_meta'].get('payment_method', None), 
                'payment_meta_payment_processor': transaction['payment_meta'].get('payment_processor', None),
                'payment_meta_reason': transaction['payment_meta'].get('reason', None), 
                'website': transaction.get('website', None), 
                'check_number': transaction.get('check_number', None), 
                'file_import_id': tracker_id
            }

            sql = """
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
                ) VALUES (
                    %(account_id)s, %(transaction_id)s, %(account_owner)s, %(amount)s, 
                    %(authorized_date)s, %(authorized_datetime)s, %(date)s, %(datetime)s, 
                    %(iso_currency_code)s, %(logo_url)s, %(merchant_entity_id)s, %(merchant_name)s, 
                    %(name)s, %(payment_channel)s, %(pending)s, %(pending_transaction_id)s, 
                    %(transaction_code)s, %(transaction_type)s, %(unofficial_currency_code)s, 
                    %(category)s, %(category_id)s, %(personal_finance_category_confidence_level)s, 
                    %(personal_finance_category_detailed)s, %(personal_finance_category_primary)s, 
                    %(personal_finance_category_icon_url)s, %(location_address)s, 
                    %(location_city)s, %(location_region)s, %(location_postal_code)s, 
                    %(location_country)s, %(location_lat)s, %(location_lon)s, %(location_store_number)s, 
                    %(payment_meta_reference_number)s, %(payment_meta_ppd_id)s, 
                    %(payment_meta_payee)s, %(payment_meta_by_order_of)s, %(payment_meta_payer)s, 
                    %(payment_meta_payment_method)s, %(payment_meta_payment_processor)s, 
                    %(payment_meta_reason)s, %(website)s, %(check_number)s, %(file_import_id)s
                )
            """

            cursor.execute(sql, params)

            for counterparty in transaction.get('counterparties', []):
                counterparty_params = {
                    'transaction_id': transaction['transaction_id'],
                    'name': counterparty.get('name', None),
                    'type': counterparty.get('type', None),
                    'website': counterparty.get('website', None),
                    'logo_url': counterparty.get('logo_url', None),
                    'confidence_level': counterparty.get('confidence_level', None),
                    'entity_id': counterparty.get('entity_id', None),
                    'phone_number': counterparty.get('phone_number', None),
                    'file_import_id': tracker_id
                }

                counterparty_sql = """
                    INSERT INTO plaid_transaction_counterparties (
                        transaction_id, name, type, website, logo_url, 
                        confidence_level, entity_id, phone_number, file_import_id
                    ) VALUES (
                        %(transaction_id)s, %(name)s, %(type)s, %(website)s, %(logo_url)s, 
                        %(confidence_level)s, %(entity_id)s, %(phone_number)s, %(file_import_id)s
                    )
                """

                cursor.execute(counterparty_sql, counterparty_params)

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
        if file_name.startswith('plaid_transactions_') and file_name.endswith('.json'):
            bank_name = file_name.split('_')[2]  # Assuming the file name format is consistent
            with open(os.path.join(fetched_files_dir, file_name), 'r') as file:
                try:
                    transactions_data = json.load(file)
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding JSON from file {file_name}: {e}")
                    print(f"Error decoding JSON from file {file_name}: {e}")
                    continue
            insert_transactions(transactions_data, bank_name, file_name)
