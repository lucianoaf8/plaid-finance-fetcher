import plaid_transactions
import plaid_liabilities

def main():
    print("Fetching transactions...")
    plaid_transactions.fetch_transactions()
    print("Fetching liabilities...")
    plaid_liabilities.fetch_liabilities()

if __name__ == "__main__":
    main()
