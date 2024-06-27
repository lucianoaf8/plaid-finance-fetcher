import os
import sys
import json
import logging
from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv
from mysql.connector import pooling
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.api_client import ApiException

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Load environment variables from .env file
load_dotenv()

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = os.getenv("PLAID_ENV", "development")

PLAID_ENV_URLS = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com"
}
PLAID_HOST = PLAID_ENV_URLS.get(PLAID_ENV, "https://production.plaid.com")

configuration = configuration.Configuration(
    host=PLAID_HOST,
    api_key={
        'clientId': PLAID_CLIENT_ID,
        'secret': PLAID_SECRET
    }
)
api_client = api_client.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

MYSQL_URL = os.getenv("MYSQL_URL")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")

url = urlparse(MYSQL_URL)
connection_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    host=url.hostname,
    port=url.port if url.port else 3306,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=url.path.lstrip('/')
)

def get_db_connection():
    return connection_pool.get_connection()

# Set up logging
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

today = datetime.now().strftime('%Y-%m-%d')
logging.basicConfig(
    filename=os.path.join(log_dir, f'plaid_categories_{today}.log'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

def fetch_categories():
    try:
        response = client.categories_get({})
        response_dict = response.to_dict()
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f'data/fetched-files/plaid_categories_{timestamp}.json'
        
        with open(filename, 'w') as file:
            json.dump(response_dict, file, indent=4)
        
        message = f"Categories fetched and saved successfully as {filename}."
        print(message)
        logging.info(message)
        
        return response_dict['categories']

    except ApiException as e:
        message = f"Error fetching categories: {e}"
        print(message)
        logging.error(message)
        return []

def store_categories_in_db(categories):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        for category in categories:
            category_id = category['category_id']
            category_group = category['group']
            hierarchy = category['hierarchy']

            hierarchy_level1 = hierarchy[0] if len(hierarchy) > 0 else None
            hierarchy_level2 = hierarchy[1] if len(hierarchy) > 1 else None
            hierarchy_level3 = hierarchy[2] if len(hierarchy) > 2 else None

            cursor.execute("""
                INSERT INTO categories (
                    category_id, category_group, hierarchy_level1, hierarchy_level2, hierarchy_level3
                ) VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    category_group=VALUES(category_group),
                    hierarchy_level1=VALUES(hierarchy_level1),
                    hierarchy_level2=VALUES(hierarchy_level2),
                    hierarchy_level3=VALUES(hierarchy_level3)
            """, (
                category_id, category_group, hierarchy_level1, hierarchy_level2, hierarchy_level3
            ))

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error storing categories in the database: {e}")
        logging.error(f"Error storing categories in the database: {e}")

if __name__ == "__main__":
    print("Starting categories fetch process...")
    logging.info("Starting categories fetch process...")

    categories = fetch_categories()
    if categories:
        store_categories_in_db(categories)

    print("Categories fetch process completed.")
    logging.info("Categories fetch process completed.")
