# Finance Fetcher

Finance Fetcher is a project designed to fetch financial data from various banks using the Plaid API and store this data in a MySQL database. The project includes functionality for fetching account information, transactions, and liabilities, and importing this data into a database for further analysis and use.

## Table of Contents

- [Installation](#installation)
- [Setup](#setup)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Installation

To get started with Finance Fetcher, clone the repository and install the necessary dependencies.

```bash
git clone https://github.com/lucianoaf8/finance-fetcher.git
cd finance-fetcher
pip install -r requirements.txt
```

## Setup

### Environment Variables

Create a `.env` file in the root directory of the project with the following variables:

```makefile
makefileCopy code
PLAID_CLIENT_ID=your_plaid_client_id
PLAID_SECRET=your_plaid_secret
PLAID_ENV=sandbox # or development or production
MYSQL_URL=mysql://user:password@host:port/database
ACCESS_TOKEN_CIBC=your_access_token_cibc
ACCESS_TOKEN_TANGERINE=your_access_token_tangerine
# Add other access tokens as needed

```

### Database Setup

Run the SQL scripts to create the necessary tables in your MySQL database.

```bash
bashCopy code
mysql -u your_username -p your_database < data/database/create_database.sql
mysql -u your_username -p your_database < data/database/create_tables.sql

```

## Usage

### Fetching Data

To fetch account information, transactions, and liabilities, run the corresponding scripts.

### Fetch Account Information

```bash
bashCopy code
python utils/plaid_accounts.py

```

### Fetch Transactions

```bash
bashCopy code
python fetchers/plaid_transactions.py

```

### Fetch Liabilities

```bash
bashCopy code
python fetchers/plaid_liabilities.py

```

### Importing Data

To import fetched data into the MySQL database, run the corresponding import scripts.

### Import Transactions

```bash
bashCopy code
python importers/insert_transactions.py

```

### Import Liabilities

```bash
bashCopy code
python importers/insert_liabilities.py

```

## Project Structure

```bash
bashCopy code
finance-fetcher/
├── data/
│   ├── database/
│   │   ├── create_database.sql
│   │   └── create_tables.sql
│   └── fetched-files/
├── fetchers/
│   ├── plaid_accounts.py
│   ├── plaid_liabilities.py
│   └── plaid_transactions.py
├── importers/
│   ├── insert_liabilities.py
│   └── insert_transactions.py
├── utils/
│   ├── count_transactions.py
│   ├── plaid_accounts.py
│   ├── server.py
│   └── plaid_link.html
├── .env
├── .gitignore
├── main.py
└── requirements.txt

```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or new features.

## License

This project is licensed under the MIT License. See the [LICENSE](notion://www.notion.so/LICENSE) file for details.

```sql

This `README.md` file provides an overview of the project, including instructions for insta

```
