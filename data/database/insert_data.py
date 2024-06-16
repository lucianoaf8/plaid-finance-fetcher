import mysql.connector
import json

def insert_liabilities(data, bank_name):
    conn = mysql.connector.connect(
        host="localhost",
        user="yourusername",
        password="yourpassword",
        database="yourdatabase"
    )
    cursor = conn.cursor()

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
            INSERT INTO plaid_liabilities (account_id, is_overdue, last_payment_amount, last_payment_date, last_statement_issue_date, last_statement_balance, minimum_payment_amount, next_payment_due_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (account_id, is_overdue, last_payment_amount, last_payment_date, last_statement_issue_date, last_statement_balance, minimum_payment_amount, next_payment_due_date))

        for apr in credit['aprs']:
            apr_percentage = apr['apr_percentage']
            apr_type = apr['apr_type']
            balance_subject_to_apr = apr['balance_subject_to_apr']
            interest_charge_amount = apr['interest_charge_amount']

            cursor.execute("""
                INSERT INTO plaid_liabilities_apr (account_id, apr_percentage, apr_type, balance_subject_to_apr, interest_charge_amount)
                VALUES (%s, %s, %s, %s, %s)
            """, (account_id, apr_percentage, apr_type, balance_subject_to_apr, interest_charge_amount))

    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    with open('data/fetched-files/plaid_liabilities_Tangerine.json') as file:
        data = json.load(file)
        insert_liabilities(data, 'Tangerine')
