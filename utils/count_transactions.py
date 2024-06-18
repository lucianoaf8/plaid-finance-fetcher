import json
import pandas as pd
import os

def analyze_transactions(file_path, output_file_path):
    # Load the JSON file
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Count the number of transactions
    num_transactions = len(data)

    # Extract unique account IDs
    account_ids = {transaction['account_id'] for transaction in data}
    num_accounts = len(account_ids)

    # Prepare the report data
    report_data = {
        'Metric': ['Number of Transactions', 'Number of Accounts'],
        'Count': [num_transactions, num_accounts]
    }

    # Create a DataFrame
    report_df = pd.DataFrame(report_data)

    # Save the report to an Excel file
    report_df.to_excel(output_file_path, index=False)

if __name__ == "__main__":
    # File paths
    input_file_path = r'data\fetched-files\plaid_transactions_CIBC_20240617194306.json'
    output_file_path = 'utils/file_report.xlsx'

    # Analyze transactions and generate the report
    analyze_transactions(input_file_path, output_file_path)
    print(f"Report generated and saved to {output_file_path}")
