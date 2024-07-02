-- Create the database
CREATE DATABASE IF NOT EXISTS plaid;
USE plaid;

# plaid_access_tokens
CREATE TABLE plaid_access_tokens (
    token_id INT AUTO_INCREMENT PRIMARY KEY, -- Unique identifier for the token
    access_token VARCHAR(255) NOT NULL, -- Plaid access token
    bank_name VARCHAR(255) NOT NULL, -- Name of the bank
    bank_id VARCHAR(255), -- Plaid bank identifier
    products VARCHAR(255), -- Products associated with the token
    accounts VARCHAR(255) -- Accounts associated with the token
);

# plaid_accounts
CREATE TABLE plaid_accounts (
    account_id VARCHAR(255) NOT NULL PRIMARY KEY, -- Unique identifier for the account
    bank_name VARCHAR(255), -- Name of the bank
    available_balance DECIMAL(15, 2), -- Available balance
    current_balance DECIMAL(15, 2), -- Current balance
    balance_limit DECIMAL(15, 2), -- Credit limit, if applicable
    iso_currency_code VARCHAR(3), -- ISO currency code (e.g., 'USD')
    unofficial_currency_code VARCHAR(10), -- Unofficial currency code, if any
    mask VARCHAR(10), -- Masked account number
    name VARCHAR(255), -- Name of the account
    official_name VARCHAR(255), -- Official name of the account
    type VARCHAR(50), -- Type of account (e.g., 'depository')
    subtype VARCHAR(50), -- Subtype of account (e.g., 'checking')
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the record was created
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP -- Timestamp when the record was last updated
);

# file_import_tracker
CREATE TABLE file_import_tracker (
    id INT AUTO_INCREMENT PRIMARY KEY, -- Unique identifier for the import record
    file_name VARCHAR(255) NOT NULL, -- Name of the imported file
    description TEXT, -- Description of the import
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the record was created
    INDEX (file_name) -- Index on the file_name column
);

# plaid_liabilities_credit
CREATE TABLE plaid_liabilities_credit (
    id INT AUTO_INCREMENT PRIMARY KEY, -- Unique identifier for the liability record
    account_id VARCHAR(255) NOT NULL UNIQUE, -- Identifier for the associated account
    is_overdue BOOLEAN NOT NULL, -- Whether the accmount is overdue
    last_payment_amount DECIMAL(10, 2), -- Amount of the last payment
    last_payment_date DATE, -- Date of the last payment
    last_statement_issue_date DATE, -- Date of the last statement issue
    last_statement_balance DECIMAL(10, 2), -- Balance on the last statement
    minimum_payment_amount DECIMAL(10, 2), -- Minimum payment amount
    next_payment_due_date DATE, -- Due date for the next payment
    file_import_id INT, -- Identifier for the associated file import
    FOREIGN KEY (file_import_id) REFERENCES file_import_tracker(id) ON DELETE CASCADE -- Foreign key constraint
);

# plaid_liabilities_credit_apr
CREATE TABLE plaid_liabilities_credit_apr (
    id INT AUTO_INCREMENT PRIMARY KEY, -- Unique identifier for the APR record
    account_id VARCHAR(255) NOT NULL, -- Identifier for the associated account
    apr_percentage DECIMAL(5, 2), -- APR percentage
    apr_type VARCHAR(255), -- Type of APR (e.g., 'variable')
    balance_subject_to_apr DECIMAL(10, 2), -- Balance subject to APR
    interest_charge_amount DECIMAL(10, 2), -- Interest charge amount
    file_import_id INT, -- Identifier for the associated file import
    FOREIGN KEY (file_import_id) REFERENCES file_import_tracker(id) ON DELETE CASCADE, -- Foreign key constraint
    FOREIGN KEY (account_id) REFERENCES plaid_liabilities_credit(account_id) -- Foreign key constraint
);

# plaid_transactions
CREATE TABLE plaid_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY, -- Unique identifier for the transaction
    account_id VARCHAR(255) NOT NULL, -- Identifier for the associated account
    transaction_id VARCHAR(255) NOT NULL UNIQUE, -- Unique identifier for the transaction
    account_owner VARCHAR(255), -- Owner of the account
    amount DECIMAL(10, 2), -- Transaction amount
    authorized_date DATE, -- Date the transaction was authorized
    authorized_datetime DATETIME, -- DateTime the transaction was authorized
    date DATE, -- Date of the transaction
    datetime DATETIME, -- DateTime of the transaction
    iso_currency_code VARCHAR(10), -- ISO currency code (e.g., 'USD')
    logo_url VARCHAR(255), -- URL of the merchant's logo
    merchant_entity_id VARCHAR(255), -- Identifier for the merchant entity
    merchant_name VARCHAR(255), -- Name of the merchant
    name VARCHAR(255), -- Name of the transaction
    payment_channel VARCHAR(50), -- Payment channel (e.g., 'online')
    pending BOOLEAN, -- Whether the transaction is pending
    pending_transaction_id VARCHAR(255), -- Identifier for the pending transaction
    transaction_code VARCHAR(255), -- Transaction code
    transaction_type VARCHAR(50), -- Type of transaction (e.g., 'debit')
    unofficial_currency_code VARCHAR(10), -- Unofficial currency code, if any
    category VARCHAR(255), -- Transaction category
    category_id VARCHAR(255), -- Identifier for the transaction category
    personal_finance_category_confidence_level VARCHAR(50), -- Confidence level of the personal finance category
    personal_finance_category_detailed VARCHAR(255), -- Detailed personal finance category
    personal_finance_category_primary VARCHAR(255), -- Primary personal finance category
    personal_finance_category_icon_url VARCHAR(255), -- URL of the personal finance category icon
    location_address VARCHAR(255), -- Address of the transaction location
    location_city VARCHAR(255), -- City of the transaction location
    location_region VARCHAR(50), -- Region/State of the transaction location
    location_postal_code VARCHAR(20), -- Postal code of the transaction location
    location_country VARCHAR(50), -- Country of the transaction location
    location_lat DECIMAL(10, 7), -- Latitude of the transaction location
    location_lon DECIMAL(10, 7), -- Longitude of the transaction location
    location_store_number VARCHAR(50), -- Store number of the transaction location
    payment_meta_reference_number VARCHAR(255), -- Reference number of the payment
    payment_meta_ppd_id VARCHAR(255), -- PPD ID of the payment
    payment_meta_payee VARCHAR(255), -- Payee of the payment
    payment_meta_by_order_of VARCHAR(255), -- By order of the payment
    payment_meta_payer VARCHAR(255), -- Payer of the payment
    payment_meta_payment_method VARCHAR(255), -- Payment method
    payment_meta_payment_processor VARCHAR(255), -- Payment processor
    payment_meta_reason VARCHAR(255), -- Reason for the payment
    website VARCHAR(255), -- Website of the merchant
    check_number VARCHAR(255), -- Check number, if applicable
    file_import_id INT, -- Identifier for the associated file import
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the record was created
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, -- Timestamp when the record was last updated
    INDEX (transaction_id), -- Index on the transaction_id column
    INDEX (account_id), -- Index on the account_id column
    FOREIGN KEY (file_import_id) REFERENCES file_import_tracker(id) ON DELETE CASCADE -- Foreign key constraint
);

# plaid_transaction_counterparties
CREATE TABLE plaid_transaction_counterparties (
    id INT AUTO_INCREMENT PRIMARY KEY, -- Unique identifier for the counterparty
    transaction_id VARCHAR(255), -- Identifier for the associated transaction
    name VARCHAR(255), -- Name of the counterparty
    type VARCHAR(50), -- Type of counterparty (e.g., 'merchant')
    website VARCHAR(255), -- Website of the counterparty
    logo_url VARCHAR(255), -- URL of the counterparty's logo
    confidence_level VARCHAR(50), -- Confidence level of the counterparty data
    entity_id VARCHAR(255), -- Identifier for the counterparty entity
    phone_number VARCHAR(50), -- Phone number of the counterparty
    file_import_id INT, -- Identifier for the associated file import
    FOREIGN KEY (file_import_id) REFERENCES file_import_tracker(id) ON DELETE CASCADE, -- Foreign key constraint
    FOREIGN KEY (transaction_id) REFERENCES plaid_transactions(transaction_id) ON DELETE CASCADE -- Foreign key constraint
);

# plaid_liabilities_credit_history
CREATE TABLE plaid_liabilities_credit_history (
    id INT AUTO_INCREMENT PRIMARY KEY, -- Unique identifier for the liability record
    account_id VARCHAR(255) NOT NULL, -- Identifier for the associated account
    is_overdue BOOLEAN NOT NULL, -- Whether the account is overdue
    last_payment_amount DECIMAL(10, 2), -- Amount of the last payment
    last_payment_date DATE, -- Date of the last payment
    last_statement_issue_date DATE, -- Date of the last statement issue
    last_statement_balance DECIMAL(10, 2), -- Balance on the last statement
    minimum_payment_amount DECIMAL(10, 2), -- Minimum payment amount
    next_payment_due_date DATE, -- Due date for the next payment
    file_import_id INT, -- Identifier for the associated file import
    FOREIGN KEY (file_import_id) REFERENCES file_import_tracker(id) ON DELETE CASCADE -- Foreign key constraint
);

# plaid_liabilities_credit_apr_history
CREATE TABLE plaid_liabilities_credit_apr_history (
    id INT AUTO_INCREMENT PRIMARY KEY, -- Unique identifier for the APR record
    account_id VARCHAR(255) NOT NULL, -- Identifier for the associated account
    apr_percentage DECIMAL(5, 2), -- APR percentage
    apr_type VARCHAR(255), -- Type of APR (e.g., 'variable')
    balance_subject_to_apr DECIMAL(10, 2), -- Balance subject to APR
    interest_charge_amount DECIMAL(10, 2), -- Interest charge amount
    file_import_id INT, -- Identifier for the associated file import
    FOREIGN KEY (file_import_id) REFERENCES file_import_tracker(id) ON DELETE CASCADE -- Foreign key constraint
);

# plaid_transactions_history
CREATE TABLE plaid_transactions_history (
    id INT AUTO_INCREMENT PRIMARY KEY, -- Unique identifier for the transaction
    account_id VARCHAR(255) NOT NULL, -- Identifier for the associated account
    transaction_id VARCHAR(255) NOT NULL, -- Unique identifier for the transaction
    account_owner VARCHAR(255), -- Owner of the account
    amount DECIMAL(10, 2), -- Transaction amount
    authorized_date DATE, -- Date the transaction was authorized
    authorized_datetime DATETIME, -- DateTime the transaction was authorized
    date DATE, -- Date of the transaction
    datetime DATETIME, -- DateTime of the transaction
    iso_currency_code VARCHAR(10), -- ISO currency code (e.g., 'USD')
    logo_url VARCHAR(255), -- URL of the merchant's logo
    merchant_entity_id VARCHAR(255), -- Identifier for the merchant entity
    merchant_name VARCHAR(255), -- Name of the merchant
    name VARCHAR(255), -- Name of the transaction
    payment_channel VARCHAR(50), -- Payment channel (e.g., 'online')
    pending BOOLEAN, -- Whether the transaction is pending
    pending_transaction_id VARCHAR(255), -- Identifier for the pending transaction
    transaction_code VARCHAR(255), -- Transaction code
    transaction_type VARCHAR(50), -- Type of transaction (e.g., 'debit')
    unofficial_currency_code VARCHAR(10), -- Unofficial currency code, if any
    category VARCHAR(255), -- Transaction category
    category_id VARCHAR(255), -- Identifier for the transaction category
    personal_finance_category_confidence_level VARCHAR(50), -- Confidence level of the personal finance category
    personal_finance_category_detailed VARCHAR(255), -- Detailed personal finance category
    personal_finance_category_primary VARCHAR(255), -- Primary personal finance category
    personal_finance_category_icon_url VARCHAR(255), -- URL of the personal finance category icon
    location_address VARCHAR(255), -- Address of the transaction location
    location_city VARCHAR(255), -- City of the transaction location
    location_region VARCHAR(50), -- Region/State of the transaction location
    location_postal_code VARCHAR(20), -- Postal code of the transaction location
    location_country VARCHAR(50), -- Country of the transaction location
    location_lat DECIMAL(10, 7), -- Latitude of the transaction location
    location_lon DECIMAL(10, 7), -- Longitude of the transaction location
    location_store_number VARCHAR(50), -- Store number of the transaction location
    payment_meta_reference_number VARCHAR(255), -- Reference number of the payment
    payment_meta_ppd_id VARCHAR(255), -- PPD ID of the payment
    payment_meta_payee VARCHAR(255), -- Payee of the payment
    payment_meta_by_order_of VARCHAR(255), -- By order of the payment
    payment_meta_payer VARCHAR(255), -- Payer of the payment
    payment_meta_payment_method VARCHAR(255), -- Payment method
    payment_meta_payment_processor VARCHAR(255), -- Payment processor
    payment_meta_reason VARCHAR(255), -- Reason for the payment
    website VARCHAR(255), -- Website of the merchant
    check_number VARCHAR(255), -- Check number, if applicable
    file_import_id INT, -- Identifier for the associated file import
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the record was created
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, -- Timestamp when the record was last updated
    INDEX (transaction_id), -- Index on the transaction_id column
    INDEX (account_id), -- Index on the account_id column
    FOREIGN KEY (file_import_id) REFERENCES file_import_tracker(id) ON DELETE CASCADE -- Foreign key constraint
);

# plaid_transaction_counterparties_history
CREATE TABLE plaid_transaction_counterparties_history (
    id INT AUTO_INCREMENT PRIMARY KEY, -- Unique identifier for the counterparty
    transaction_id VARCHAR(255), -- Identifier for the associated transaction
    name VARCHAR(255), -- Name of the counterparty
    type VARCHAR(50), -- Type of counterparty (e.g., 'merchant')
    website VARCHAR(255), -- Website of the counterparty
    logo_url VARCHAR(255), -- URL of the counterparty's logo
    confidence_level VARCHAR(50), -- Confidence level of the counterparty data
    entity_id VARCHAR(255), -- Identifier for the counterparty entity
    phone_number VARCHAR(50), -- Phone number of the counterparty
    file_import_id INT, -- Identifier for the associated file import
    FOREIGN KEY (file_import_id) REFERENCES file_import_tracker(id) ON DELETE CASCADE -- Foreign key constraint
);

# categories
CREATE TABLE categories (
    category_id VARCHAR(8) NOT NULL PRIMARY KEY, -- Unique identifier for the category
    category_group VARCHAR(50) NOT NULL, -- Group name the category belongs to
    hierarchy_level1 VARCHAR(255), -- Level 1 hierarchy name
    hierarchy_level2 VARCHAR(255), -- Level 2 hierarchy name
    hierarchy_level3 VARCHAR(255) -- Level 3 hierarchy name
);

# asset_report
CREATE TABLE asset_report (
    asset_report_id VARCHAR(50) PRIMARY KEY, -- Unique identifier for the asset report
    client_report_id VARCHAR(50), -- Client-provided identifier for the report
    date_generated DATETIME, -- Date and time when the report was generated
    days_requested INT, -- Number of days the report covers
    file_path VARCHAR(255), -- Name of the imported file
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Timestamp when the record was created
);

# asset_item
CREATE TABLE asset_item (
    item_id VARCHAR(50) PRIMARY KEY, -- Unique identifier for the item
    institution_name VARCHAR(100), -- Name of the financial institution
    institution_id VARCHAR(50), -- Identifier for the financial institution
    date_last_updated DATETIME, -- Date and time when the item was last updated
    asset_report_id VARCHAR(50), -- Identifier for the associated asset report
    FOREIGN KEY (asset_report_id) REFERENCES asset_report(asset_report_id) ON DELETE CASCADE
);

# asset_account
CREATE TABLE asset_account (
    account_id VARCHAR(50) PRIMARY KEY, -- Unique identifier for the account
    name VARCHAR(50), -- Name of the account
    official_name VARCHAR(100), -- Official name of the account
    mask VARCHAR(10), -- Masked account number
    available DECIMAL(10,2), -- Available balance
    current DECIMAL(10,2), -- Current balance
    `limit` DECIMAL(10,2), -- Credit limit, if applicable
    margin_loan_amount DECIMAL(10,2), -- Margin loan amount, if applicable
    iso_currency_code VARCHAR(10), -- ISO currency code (e.g., 'CAD')
    unofficial_currency_code VARCHAR(10), -- Unofficial currency code, if any
    type VARCHAR(50), -- Type of account (e.g., 'depository')
    subtype VARCHAR(50), -- Subtype of account (e.g., 'savings')
    days_available INT, -- Number of days the account data is available
    item_id VARCHAR(50), -- Identifier for the associated item
    asset_report_id VARCHAR(50), -- Identifier for the associated asset report
    FOREIGN KEY (asset_report_id) REFERENCES asset_report(asset_report_id) ON DELETE CASCADE
);

# asset_transaction
CREATE TABLE asset_transaction (
    transaction_id VARCHAR(50) PRIMARY KEY, -- Unique identifier for the transaction
    account_id VARCHAR(50), -- Identifier for the associated account
    amount DECIMAL(10,2), -- Transaction amount
    iso_currency_code VARCHAR(10), -- ISO currency code (e.g., 'CAD')
    unofficial_currency_code VARCHAR(10), -- Unofficial currency code, if any
    original_description VARCHAR(255), -- Original description of the transaction
    date DATE, -- Date of the transaction
    pending BOOLEAN, -- Whether the transaction is pending
    asset_report_id VARCHAR(50),  -- Identifier for the associated asset report
    FOREIGN KEY (asset_report_id) REFERENCES asset_report(asset_report_id) ON DELETE CASCADE
);

# asset_historical_balance
CREATE TABLE asset_historical_balance (
    balance_id INT AUTO_INCREMENT PRIMARY KEY, -- Unique identifier for the balance record
    account_id VARCHAR(50), -- Identifier for the associated account
    date DATE, -- Date of the balance record
    current DECIMAL(10,2), -- Current balance
    iso_currency_code VARCHAR(10), -- ISO currency code (e.g., 'CAD')
    unofficial_currency_code VARCHAR(10), -- Unofficial currency code, if any
    asset_report_id VARCHAR(50),  -- Identifier for the associated asset report
    FOREIGN KEY (asset_report_id) REFERENCES asset_report(asset_report_id) ON DELETE CASCADE
);

# inflow_streams
CREATE TABLE inflow_streams (
    stream_id VARCHAR(255) PRIMARY KEY, -- Unique identifier for the inflow stream
    account_id VARCHAR(255), -- Account associated with the stream
    category_id VARCHAR(255), -- Category identifier
    description TEXT, -- Description of the transaction
    merchant_name VARCHAR(255), -- Name of the merchant
    first_date DATE, -- First date of the transaction
    last_date DATE, -- Last date of the transaction
    frequency VARCHAR(50), -- Frequency of the transaction
    average_amount DECIMAL(10, 2), -- Average amount of the transaction
    last_amount DECIMAL(10, 2), -- Last amount of the transaction
    is_active BOOLEAN, -- Whether the stream is active
    status VARCHAR(50), -- Status of the stream
    is_user_modified BOOLEAN, -- Whether the stream was modified by the user
    last_user_modified_datetime DATETIME, -- Last user modification datetime
    pers_fin_primary_category VARCHAR(255), -- Personal finance primary category
    pers_fin_detailed_category VARCHAR(255), -- Personal finance detailed category
    pers_fin_confidence_level VARCHAR(50), -- Personal finance confidence level
    file_import_id INT, -- ID of the file import record
    FOREIGN KEY (file_import_id) REFERENCES file_import_tracker(id) ON DELETE CASCADE -- Foreign key to file_import_tracker
);

# outflow_streams
CREATE TABLE outflow_streams (
    stream_id VARCHAR(255) PRIMARY KEY, -- Unique identifier for the outflow stream
    account_id VARCHAR(255), -- Account associated with the stream
    category_id VARCHAR(255), -- Category identifier
    description TEXT, -- Description of the transaction
    merchant_name VARCHAR(255), -- Name of the merchant
    first_date DATE, -- First date of the transaction
    last_date DATE, -- Last date of the transaction
    frequency VARCHAR(50), -- Frequency of the transaction
    average_amount DECIMAL(10, 2), -- Average amount of the transaction
    last_amount DECIMAL(10, 2), -- Last amount of the transaction
    is_active BOOLEAN, -- Whether the stream is active
    status VARCHAR(50), -- Status of the stream
    is_user_modified BOOLEAN, -- Whether the stream was modified by the user
    last_user_modified_datetime DATETIME, -- Last user modification datetime
    pers_fin_primary_category VARCHAR(255), -- Personal finance primary category
    pers_fin_detailed_category VARCHAR(255), -- Personal finance detailed category
    pers_fin_confidence_level VARCHAR(50), -- Personal finance confidence level
    file_import_id INT, -- ID of the file import record
    FOREIGN KEY (file_import_id) REFERENCES file_import_tracker(id) ON DELETE CASCADE -- Foreign key to file_import_tracker
);

# inflow_transactions
CREATE TABLE inflow_transactions (
    transaction_id VARCHAR(255) PRIMARY KEY, -- Unique identifier for the transaction
    stream_id VARCHAR(255), -- Associated inflow stream
    FOREIGN KEY (stream_id) REFERENCES inflow_streams(stream_id) ON DELETE CASCADE -- Foreign key to inflow_streams
);

# outflow_transactions
CREATE TABLE outflow_transactions (
    transaction_id VARCHAR(255) PRIMARY KEY, -- Unique identifier for the transaction
    stream_id VARCHAR(255), -- Associated outflow stream
    FOREIGN KEY (stream_id) REFERENCES outflow_streams(stream_id) ON DELETE CASCADE -- Foreign key to outflow_streams
);
