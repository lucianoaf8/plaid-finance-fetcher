import os
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.api_client import ApiException
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
import logging

app = Flask(__name__)
load_dotenv()

# Setup logging
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    filename=os.path.join(log_dir, 'server.log'),
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s:%(message)s'
)

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

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

@app.route('/exchange_public_token', methods=['POST'])
def exchange_public_token_endpoint():
    try:
        logging.info("Starting public token exchange process.")
        public_token = request.json.get('public_token')
        logging.debug(f'Received public token: {public_token}')
        
        if not public_token:
            logging.error("Public token is required but not provided.")
            return jsonify({'error': 'public_token is required'}), 400

        exchange_request = ItemPublicTokenExchangeRequest(
            client_id=PLAID_CLIENT_ID,
            secret=PLAID_SECRET,
            public_token=public_token
        )
        response = client.item_public_token_exchange(exchange_request)
        access_token = response['access_token']
        logging.debug(f'Exchange successful. Access token: {access_token}')
        return jsonify({'access_token': access_token})
    except ApiException as e:
        logging.error(f'API Exception: {str(e)} - {e.body}')
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logging.error(f'Unexpected Exception: {str(e)}')
        logging.debug('Exception details:', exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/create_update_token', methods=['POST'])
def create_update_token():
    try:
        logging.info("Starting update token creation process.")
        access_token = request.json.get('access_token')
        
        if not access_token:
            logging.error("Access token is required but not provided.")
            return jsonify({'error': 'access_token is required'}), 400

        update_request_data = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(client_user_id='unique_static_user_id'),
            client_name='finance-fetcher',
            products=[Products('transactions'), Products('assets'), Products('liabilities')],
            country_codes=[CountryCode('CA')],
            language='en',
            access_token=access_token
        )
        response = client.link_token_create(update_request_data)
        update_token = response['link_token']
        logging.debug(f'Generated update token: {update_token}')
        return jsonify({'update_token': update_token})
    except ApiException as e:
        logging.error(f'API Exception: {str(e)} - {e.body}')
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logging.error(f'Unexpected Exception: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    logging.info("Serving the main HTML page.")
    return send_from_directory('../static', 'plaid_link.html')

if __name__ == '__main__':
    logging.info("Starting Flask server.")
    app.run(port=5000, debug=False)
