import os
from utils import setup
from dotenv import load_dotenv
from fetchers import plaid_transactions
from fetchers import plaid_liabilities
from importers import insert_data

# Run the setup script to verify and create the project structure
setup.verify_and_create_structure()

# Load environment variables from .env file
load_dotenv()

# Fetch access tokens for multiple accounts from environment variables
access_tokens = {
    # "CIBC": os.getenv("ACCESS_TOKEN_CIBC"),
    "Tangerine": os.getenv("ACCESS_TOKEN_TANGERINE"),
    # "Triangle": os.getenv("ACCESS_TOKEN_TRIANGLE"),
    # "MBNA": os.getenv("ACCESS_TOKEN_MBNA")
}

def main():
    for bank, token in access_tokens.items():
        if token:
            print(f"Fetching data for {bank}...")
            print("Fetching transactions...")
            plaid_transactions.fetch_transactions(token, bank)
            print("Fetching liabilities...")
            plaid_liabilities.fetch_liabilities(token, bank)
        else:
            print(f"Access token for {bank} is not set.")
    
    print("Starting data import process...")
    insert_data.import_files()
    print("Data import process completed.")

if __name__ == "__main__":
    main()
