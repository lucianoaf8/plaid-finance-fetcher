USE finance;

# Main tables
CREATE TABLE plaid_accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id VARCHAR(255) UNIQUE NOT NULL,
    access_token VARCHAR(255) NOT NULL,
    institution_id VARCHAR(255),
    institution_name VARCHAR(255),
    account_name VARCHAR(255),
    official_name VARCHAR(255),
    account_type VARCHAR(50),
    account_subtype VARCHAR(50),
    balances JSON,
    mask VARCHAR(10),
    verification_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE `file_import_tracker` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `file_name` VARCHAR(255) NOT NULL,
    `description` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (`file_name`)
);

CREATE TABLE finance.plaid_liabilities_credit (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id VARCHAR(255) NOT NULL UNIQUE,
    is_overdue BOOLEAN NOT NULL,
    last_payment_amount DECIMAL(10, 2),
    last_payment_date DATE,
    last_statement_issue_date DATE,
    last_statement_balance DECIMAL(10, 2),
    minimum_payment_amount DECIMAL(10, 2),
    next_payment_due_date DATE,
    file_import_id INT,
    FOREIGN KEY (file_import_id) REFERENCES file_import_tracker(id) ON DELETE CASCADE
);

CREATE TABLE plaid_liabilities_credit_apr (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id VARCHAR(255) NOT NULL,
    apr_percentage DECIMAL(5, 2),
    apr_type VARCHAR(255),
    balance_subject_to_apr DECIMAL(10, 2),
    interest_charge_amount DECIMAL(10, 2),
    file_import_id INT,
    FOREIGN KEY (file_import_id) REFERENCES file_import_tracker(id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES plaid_liabilities_credit(account_id)
);

CREATE TABLE plaid_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id VARCHAR(255) NOT NULL,
    transaction_id VARCHAR(255) NOT NULL UNIQUE,
    account_owner VARCHAR(255),
    amount DECIMAL(10, 2),
    authorized_date DATE,
    authorized_datetime DATETIME,
    date DATE,
    datetime DATETIME,
    iso_currency_code VARCHAR(10),
    logo_url VARCHAR(255),
    merchant_entity_id VARCHAR(255),
    merchant_name VARCHAR(255),
    name VARCHAR(255),
    payment_channel VARCHAR(50),
    pending BOOLEAN,
    pending_transaction_id VARCHAR(255),
    transaction_code VARCHAR(255),
    transaction_type VARCHAR(50),
    unofficial_currency_code VARCHAR(10),
    category VARCHAR(255),
    category_id VARCHAR(255),
    personal_finance_category_confidence_level VARCHAR(50),
    personal_finance_category_detailed VARCHAR(255),
    personal_finance_category_primary VARCHAR(255),
    personal_finance_category_icon_url VARCHAR(255),
    location_address VARCHAR(255),
    location_city VARCHAR(255),
    location_region VARCHAR(50),
    location_postal_code VARCHAR(20),
    location_country VARCHAR(50),
    location_lat DECIMAL(10, 7),
    location_lon DECIMAL(10, 7),
    location_store_number VARCHAR(50),
    payment_meta_reference_number VARCHAR(255),
    payment_meta_ppd_id VARCHAR(255),
    payment_meta_payee VARCHAR(255),
    payment_meta_by_order_of VARCHAR(255),
    payment_meta_payer VARCHAR(255),
    payment_meta_payment_method VARCHAR(255),
    payment_meta_payment_processor VARCHAR(255),
    payment_meta_reason VARCHAR(255),
    website VARCHAR(255),
    check_number VARCHAR(255),
    file_import_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX (transaction_id),
    INDEX (account_id),
    FOREIGN KEY (file_import_id) REFERENCES file_import_tracker (id) ON DELETE CASCADE
);


CREATE TABLE plaid_transaction_counterparties (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id VARCHAR(255),
    name VARCHAR(255),
    type VARCHAR(50),
    website VARCHAR(255),
    logo_url VARCHAR(255),
    confidence_level VARCHAR(50),
    entity_id VARCHAR(255),
    phone_number VARCHAR(50),
    file_import_id INT,
    FOREIGN KEY (file_import_id) REFERENCES file_import_tracker(id) ON DELETE CASCADE,
    FOREIGN KEY (transaction_id) REFERENCES plaid_transactions(transaction_id) ON DELETE CASCADE
);

# History tables
CREATE TABLE finance.plaid_liabilities_credit_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id VARCHAR(255) NOT NULL,
    is_overdue BOOLEAN NOT NULL,
    last_payment_amount DECIMAL(10, 2),
    last_payment_date DATE,
    last_statement_issue_date DATE,
    last_statement_balance DECIMAL(10, 2),
    minimum_payment_amount DECIMAL(10, 2),
    next_payment_due_date DATE,
    file_import_id INT,
    FOREIGN KEY (file_import_id) REFERENCES file_import_tracker(id) ON DELETE CASCADE
);

CREATE TABLE plaid_liabilities_credit_apr_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id VARCHAR(255) NOT NULL,
    apr_percentage DECIMAL(5, 2),
    apr_type VARCHAR(255),
    balance_subject_to_apr DECIMAL(10, 2),
    interest_charge_amount DECIMAL(10, 2),
    file_import_id INT,
    FOREIGN KEY (file_import_id) REFERENCES file_import_tracker(id) ON DELETE CASCADE
);

CREATE TABLE plaid_transactions_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id VARCHAR(255) NOT NULL,
    transaction_id VARCHAR(255) NOT NULL,
    account_owner VARCHAR(255),
    amount DECIMAL(10, 2),
    authorized_date DATE,
    authorized_datetime DATETIME,
    date DATE,
    datetime DATETIME,
    iso_currency_code VARCHAR(10),
    logo_url VARCHAR(255),
    merchant_entity_id VARCHAR(255),
    merchant_name VARCHAR(255),
    name VARCHAR(255),
    payment_channel VARCHAR(50),
    pending BOOLEAN,
    pending_transaction_id VARCHAR(255),
    transaction_code VARCHAR(255),
    transaction_type VARCHAR(50),
    unofficial_currency_code VARCHAR(10),
    category VARCHAR(255),
    category_id VARCHAR(255),
    personal_finance_category_confidence_level VARCHAR(50),
    personal_finance_category_detailed VARCHAR(255),
    personal_finance_category_primary VARCHAR(255),
    personal_finance_category_icon_url VARCHAR(255),
    location_address VARCHAR(255),
    location_city VARCHAR(255),
    location_region VARCHAR(50),
    location_postal_code VARCHAR(20),
    location_country VARCHAR(50),
    location_lat DECIMAL(10, 7),
    location_lon DECIMAL(10, 7),
    location_store_number VARCHAR(50),
    payment_meta_reference_number VARCHAR(255),
    payment_meta_ppd_id VARCHAR(255),
    payment_meta_payee VARCHAR(255),
    payment_meta_by_order_of VARCHAR(255),
    payment_meta_payer VARCHAR(255),
    payment_meta_payment_method VARCHAR(255),
    payment_meta_payment_processor VARCHAR(255),
    payment_meta_reason VARCHAR(255),
    website VARCHAR(255),
    check_number VARCHAR(255),
    file_import_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX (transaction_id),
    INDEX (account_id),
    FOREIGN KEY (file_import_id) REFERENCES file_import_tracker (id) ON DELETE CASCADE
);

CREATE TABLE plaid_transaction_counterparties_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id VARCHAR(255),
    name VARCHAR(255),
    type VARCHAR(50),
    website VARCHAR(255),
    logo_url VARCHAR(255),
    confidence_level VARCHAR(50),
    entity_id VARCHAR(255),
    phone_number VARCHAR(50),
    file_import_id INT,
    FOREIGN KEY (file_import_id) REFERENCES file_import_tracker(id) ON DELETE CASCADE
);
