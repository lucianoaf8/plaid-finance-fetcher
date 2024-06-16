DROP TABLE IF EXISTS finance.file_import_tracker;
CREATE TABLE finance.file_import_tracker (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

DROP TABLE IF EXISTS finance.plaid_liabilities_credit;
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


DROP TABLE IF EXISTS finance.plaid_liabilities_credit_apr;
CREATE TABLE finance.plaid_liabilities_credit_apr (
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
