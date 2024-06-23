import os
import logging
from flask import Flask, request, jsonify, send_from_directory
import plaid
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.api_client import ApiException
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.country_code import CountryCode
from dotenv import load_dotenv

# Load environment variables from .env file
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

# Plaid configuration
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

# Flask app setup
app = Flask(__name__, static_folder='../static', static_url_path='')

@app.route('/')
def serve_index():
    logging.info('Serving index.html')
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/create_link_token', methods=['POST'])
def create_link_token():
    logging.info('Received request to create link token')
    try:
        request_data = request.get_json()
        logging.debug(f'Request data: {request_data}')
        link_token_request = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(
                client_user_id='user_unique_id'  # Replace with actual user ID
            ),
            client_name='Your App Name',
            products=[Products('transactions')],
            country_codes=[CountryCode('CA')],
            language='en',
            access_token=request_data['access_token']  # Ensure update mode
        )
        response = client.link_token_create(link_token_request)
        logging.info('Link token created successfully')
        logging.debug(f'Link token response: {response.to_dict()}')
        return jsonify(response.to_dict())
    except ApiException as e:
        logging.error(f'Error creating link token: {str(e)}')
        logging.debug(f'Error details: {e.body}')
        return jsonify(error=str(e)), 400
    except Exception as e:
        logging.error(f'Unexpected error: {str(e)}')
        return jsonify(error='Unexpected error occurred'), 500

@app.route('/exchange_public_token', methods=['POST'])
def exchange_public_token():
    logging.info('Received request to exchange public token')
    try:
        request_data = request.get_json()
        logging.debug(f'Request data: {request_data}')
        public_token = request_data['public_token']
        exchange_request = ItemPublicTokenExchangeRequest(
            public_token=public_token
        )
        response = client.item_public_token_exchange(exchange_request)
        logging.info('Public token exchanged successfully')
        logging.debug(f'Public token exchange response: {response.to_dict()}')
        return jsonify(response.to_dict())
    except ApiException as e:
        logging.error(f'Error exchanging public token: {str(e)}')
        logging.debug(f'Error details: {e.body}')
        return jsonify(error=str(e)), 400
    except Exception as e:
        logging.error(f'Unexpected error: {str(e)}')
        return jsonify(error='Unexpected error occurred'), 500

@app.route('/webhook', methods=['POST'])
def plaid_webhook():
    request_data = request.get_json()
    logging.info(f'Received webhook: {request_data}')

    if request_data['webhook_type'] == 'ITEM':
        if request_data['webhook_code'] == 'LOGIN_REPAIRED':
            item_id = request_data['item_id']
            logging.info(f'Login repaired for item_id: {item_id}')
            # Handle login repaired event
        elif request_data['webhook_code'] == 'PENDING_EXPIRATION':
            item_id = request_data['item_id']
            logging.info(f'Pending expiration for item_id: {item_id}')
            # Prompt the user to re-authenticate before the item expires
    return 'Webhook received', 200

if __name__ == '__main__':
    logging.info("Starting Flask server.")
    app.run(debug=True, host='0.0.0.0', port=8000)
