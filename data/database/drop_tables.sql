USE plaid;

DROP TABLE IF EXISTS inflow_transactions;
DROP TABLE IF EXISTS outflow_transactions;
DROP TABLE IF EXISTS inflow_streams;
DROP TABLE IF EXISTS outflow_streams;

DROP TABLE IF EXISTS plaid_liabilities_credit_apr;
DROP TABLE IF EXISTS plaid_liabilities_credit;
DROP TABLE IF EXISTS plaid_transaction_counterparties;
DROP TABLE IF EXISTS plaid_transactions;
DROP TABLE IF EXISTS plaid_transaction_counterparties_history;
DROP TABLE IF EXISTS plaid_transactions_history;
DROP TABLE IF EXISTS plaid_liabilities_credit_apr_history;
DROP TABLE IF EXISTS plaid_liabilities_credit_history;
DROP TABLE IF EXISTS file_import_tracker;
DROP TABLE IF EXISTS plaid_accounts;
DROP TABLE IF EXISTS plaid_access_tokens;

DROP TABLE IF EXISTS asset_historical_balance;
DROP TABLE IF EXISTS asset_transaction;
DROP TABLE IF EXISTS asset_item;
DROP TABLE IF EXISTS asset_account;
DROP TABLE IF EXISTS asset_report;
