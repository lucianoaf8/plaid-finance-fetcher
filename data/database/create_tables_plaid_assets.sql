-- Create the database
CREATE DATABASE IF NOT EXISTS plaid_assets;
USE plaid_assets;

-- Table to store the asset report metadata
-- Example: asset_report_id='a04fa14e-03dc-4311-b3b3-0205d10dcf7d', client_report_id=NULL, date_generated='2024-06-27 02:03:08', days_requested=60
CREATE TABLE asset_report (
    asset_report_id VARCHAR(50) PRIMARY KEY, -- Unique identifier for the asset report
    client_report_id VARCHAR(50), -- Client-provided identifier for the report
    date_generated DATETIME, -- Date and time when the report was generated
    days_requested INT -- Number of days the report covers
);

-- Table to store items associated with the report
-- Example: item_id='AL6LmqjboJCLwoMqxyajT93O31b1eLc6mMLQr', asset_report_id='a04fa14e-03dc-4311-b3b3-0205d10dcf7d', institution_name='Tangerine - Personal', institution_id='ins_40', date_last_updated='2024-06-27 02:03:08'
CREATE TABLE item (
    item_id VARCHAR(50) PRIMARY KEY, -- Unique identifier for the item
    asset_report_id VARCHAR(50), -- Identifier for the associated asset report
    institution_name VARCHAR(100), -- Name of the financial institution
    institution_id VARCHAR(50), -- Identifier for the financial institution
    date_last_updated DATETIME, -- Date and time when the item was last updated
    FOREIGN KEY (asset_report_id) REFERENCES asset_report(asset_report_id) ON DELETE CASCADE
);

-- Table to store account details
-- Example: account_id='4OYOERLAkwIQdknYq7rMCXrRx5B0PpUJ9pj4m', item_id='AL6LmqjboJCLwoMqxyajT93O31b1eLc6mMLQr', available=100.53, current=100.53, limit=NULL, margin_loan_amount=NULL, iso_currency_code='CAD', unofficial_currency_code=NULL, mask='5661', name='Brazil', official_name='Tangerine Savings Account', type='depository', subtype='savings', days_available=60, ownership_type=NULL
CREATE TABLE account (
    account_id VARCHAR(50) PRIMARY KEY, -- Unique identifier for the account
    item_id VARCHAR(50), -- Identifier for the associated item
    available DECIMAL(10,2), -- Available balance
    current DECIMAL(10,2), -- Current balance
    `limit` DECIMAL(10,2), -- Credit limit, if applicable
    margin_loan_amount DECIMAL(10,2), -- Margin loan amount, if applicable
    iso_currency_code VARCHAR(10), -- ISO currency code (e.g., 'CAD')
    unofficial_currency_code VARCHAR(10), -- Unofficial currency code, if any
    mask VARCHAR(10), -- Masked account number
    name VARCHAR(50), -- Name of the account
    official_name VARCHAR(100), -- Official name of the account
    type VARCHAR(50), -- Type of account (e.g., 'depository')
    subtype VARCHAR(50), -- Subtype of account (e.g., 'savings')
    days_available INT, -- Number of days the account data is available
    asset_report_id VARCHAR(50), -- Identifier for the associated asset report
    FOREIGN KEY (item_id) REFERENCES item(item_id),
    FOREIGN KEY (asset_report_id) REFERENCES asset_report(asset_report_id) ON DELETE CASCADE
);

-- Table to store transaction details for each account
-- Example: transaction_id='bkykKdNx7bCLXmZBO81qTAxxY3NEDLuDwaaqX', account_id='4OYOERLAkwIQdknYq7rMCXrRx5B0PpUJ9pj4m', amount=-0.11, iso_currency_code='CAD', unofficial_currency_code=NULL, original_description='Interest Paid', date='2024-04-30', pending=FALSE
CREATE TABLE transaction (
    transaction_id VARCHAR(50) PRIMARY KEY, -- Unique identifier for the transaction
    account_id VARCHAR(50), -- Identifier for the associated account
    amount DECIMAL(10,2), -- Transaction amount
    iso_currency_code VARCHAR(10), -- ISO currency code (e.g., 'CAD')
    unofficial_currency_code VARCHAR(10), -- Unofficial currency code, if any
    original_description VARCHAR(255), -- Original description of the transaction
    date DATE, -- Date of the transaction
    pending BOOLEAN, -- Whether the transaction is pending
    asset_report_id VARCHAR(50),  -- Identifier for the associated asset report
    FOREIGN KEY (account_id) REFERENCES account(account_id),
    FOREIGN KEY (asset_report_id) REFERENCES asset_report(asset_report_id) ON DELETE CASCADE
);

-- Table to store historical balance details for each account
-- Example: balance_id=1, account_id='4OYOERLAkwIQdknYq7rMCXrRx5B0PpUJ9pj4m', date='2024-06-26', current=100.53, iso_currency_code='CAD', unofficial_currency_code=NULL
CREATE TABLE historical_balance (
    balance_id INT AUTO_INCREMENT PRIMARY KEY, -- Unique identifier for the balance record
    account_id VARCHAR(50), -- Identifier for the associated account
    date DATE, -- Date of the balance record
    current DECIMAL(10,2), -- Current balance
    iso_currency_code VARCHAR(10), -- ISO currency code (e.g., 'CAD')
    unofficial_currency_code VARCHAR(10), -- Unofficial currency code, if any
    asset_report_id VARCHAR(50),  -- Identifier for the associated asset report
    FOREIGN KEY (account_id) REFERENCES account(account_id),
    FOREIGN KEY (asset_report_id) REFERENCES asset_report(asset_report_id) ON DELETE CASCADE
);
