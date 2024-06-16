DROP TABLE IF EXISTS finance.plaid_liabilities_credit;
-- Create the plaid_liabilities_credit table with a unique constraint on account_id
CREATE TABLE finance.plaid_liabilities_credit (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id VARCHAR(255) NOT NULL UNIQUE,
    is_overdue BOOLEAN NOT NULL,
    last_payment_amount DECIMAL(10, 2),
    last_payment_date DATE,
    last_statement_issue_date DATE,
    last_statement_balance DECIMAL(10, 2),
    minimum_payment_amount DECIMAL(10, 2),
    next_payment_due_date DATE
);

DROP TABLE IF EXISTS finance.plaid_liabilities_credit_apr;
-- Create the plaid_liabilities_credit_apr table
CREATE TABLE finance.plaid_liabilities_credit_apr (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id VARCHAR(255) NOT NULL,
    apr_percentage DECIMAL(5, 2),
    apr_type VARCHAR(255),
    balance_subject_to_apr DECIMAL(10, 2),
    interest_charge_amount DECIMAL(10, 2),
    FOREIGN KEY (account_id) REFERENCES plaid_liabilities_credit(account_id)
);
