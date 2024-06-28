import os
import json
import logging
import pandas as pd
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.model.transactions_enrich_request import TransactionsEnrichRequest
from plaid.model.client_provided_transaction import ClientProvidedTransaction
from plaid.model.enrich_transaction_direction import EnrichTransactionDirection
from plaid.model.client_provided_transaction_location import ClientProvidedTransactionLocation
from datetime import datetime
from plaid.api_client import ApiException

# Load environment variables from .env file
load_dotenv()

# Set up logging
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

today = datetime.now().strftime('%Y-%m-%d')
logging.basicConfig(
    filename=os.path.join(log_dir, f'plaid_enrich_{today}.log'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

# Plaid configuration
PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")

PLAID_HOST = "https://sandbox.plaid.com"

configuration = configuration.Configuration(
    host=PLAID_HOST,
    api_key={
        'clientId': PLAID_CLIENT_ID,
        'secret': PLAID_SECRET
    }
)
api_client = api_client.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

def get_transactions_from_csv(file_path):
    df = pd.read_csv(file_path)
    transactions = df.to_dict(orient='records')
    return transactions

def enrich_transactions(transactions):
    enriched_data = []
    for transaction in transactions:
        if pd.notna(transaction["city"]) and pd.notna(transaction["region"]):
            location = ClientProvidedTransactionLocation(
                city=transaction["city"],
                region=transaction["region"]
            )
            transaction_data = ClientProvidedTransaction(
                id=str(transaction["id"]),
                description=transaction["description"],
                amount=abs(float(transaction["amount"])),  # Ensure amount is non-negative
                iso_currency_code=transaction["iso_currency_code"],
                direction=EnrichTransactionDirection(transaction["direction"]),  # Use enum
                location=location
            )
        else:
            transaction_data = ClientProvidedTransaction(
                id=str(transaction["id"]),
                description=transaction["description"],
                amount=abs(float(transaction["amount"])),  # Ensure amount is non-negative
                iso_currency_code=transaction["iso_currency_code"],
                direction=EnrichTransactionDirection(transaction["direction"])  # Use enum
            )
        enriched_data.append(transaction_data)
    
    batch_size = 100
    results = []

    for i in range(0, len(enriched_data), batch_size):
        batch = enriched_data[i:i+batch_size]
        request = TransactionsEnrichRequest(
            account_type="credit",  # Modify this as needed
            transactions=batch
        )
        
        try:
            response = client.transactions_enrich(request)
            results.append(response.to_dict())
        except ApiException as e:
            print(f"Exception when calling PlaidApi->transactions_enrich: {e}")
            logging.error(f"Exception when calling PlaidApi->transactions_enrich: {e}")
    
    return results

def save_enriched_data(data):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f'data/fetched-files/plaid_enriched_{timestamp}.json'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)
    print(f"Enriched data saved to {filename}")
    logging.info(f"Enriched data saved to {filename}")

def main():
    file_path = r'C:\Users\Luciano\Downloads\enrich_sandbox_preset_transactions.csv'
    transactions = get_transactions_from_csv(file_path)
    if transactions:
        enriched_data = enrich_transactions(transactions)
        if enriched_data:
            save_enriched_data(enriched_data)

if __name__ == "__main__":
    main()
