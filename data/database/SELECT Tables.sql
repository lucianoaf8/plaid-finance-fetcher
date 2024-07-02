USE plaid;

# Plaid tables
SELECT * FROM plaid_access_tokens
SELECT * FROM plaid_accounts
SELECT * FROM file_import_tracker
SELECT * FROM plaid_liabilities_credit
SELECT * FROM plaid_liabilities_credit_apr
SELECT * FROM plaid_transactions LIMIT 5
SELECT * FROM plaid_transaction_counterparties LIMIT 5
SELECT * FROM categories LIMIT 5
SELECT * FROM asset_report LIMIT 1
SELECT * FROM asset_item
SELECT * FROM asset_account LIMIT 2
SELECT * FROM asset_transaction LIMIT 3
SELECT * FROM asset_historical_balance LIMIT 3
SELECT * FROM inflow_streams LIMIT 3
SELECT * FROM outflow_streams  LIMIT 3
SELECT * FROM inflow_transactions LIMIT 3
SELECT * FROM outflow_transactions LIMIT 3
