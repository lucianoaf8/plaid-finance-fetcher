import os
import json
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

MYSQL_URL = os.getenv("MYSQL_URL")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",  # Extract from MYSQL_URL if needed
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database="finance"
    )

def insert_liabilities(data, bank_name, file_name):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert record in file_import_tracker
    cursor.execute("""
        INSERT INTO file_import_tracker (file_name, description) 
        VALUES (%s, %s)
    """, (file_name, f"Liabilities data for {bank_name}"))

    tracker_id = cursor.lastrowid

    for credit in data['credit']:
        account_id = credit['account_id']
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
                minimum_payment_amount, next_payment_due_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            account_id, is_overdue, last_payment_amount, last_payment_date,
            last_statement_issue_date, last_statement_balance, 
            minimum_payment_amount, next_payment_due_date
        ))

        for apr in credit['aprs']:
            apr_percentage = apr['apr_percentage']
            apr_type = apr['apr_type']
            balance_subject_to_apr = apr['balance_subject_to_apr']
            interest_charge_amount = apr['interest_charge_amount']

            cursor.execute("""
                INSERT INTO plaid_liabilities_credit_apr (
                    account_id, apr_percentage, apr_type, 
                    balance_subject_to_apr, interest_charge_amount
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                account_id, apr_percentage, apr_type, 
                balance_subject_to_apr, interest_charge_amount
            ))

    conn.commit()
    cursor.close()
    conn.close()

def import_liabilities_files():
    fetched_files_dir = 'data/fetched-files/'
    for file_name in os.listdir(fetched_files_dir):
        if file_name.startswith("plaid_liabilities_") and file_name.endswith(".json"):
            with open(fetched_files_dir + file_name) as file:
                data = json.load(file)
                bank_name = file_name.split("_")[2].replace(".json", "")
                insert_liabilities(data, bank_name, file_name)

if __name__ == "__main__":
    import_liabilities_files()
