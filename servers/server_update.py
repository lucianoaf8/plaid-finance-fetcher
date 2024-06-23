import os
from flask import Flask, request, jsonify, send_from_directory
import plaid
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.api_client import ApiException
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.country_code import CountryCode
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = os.getenv("PLAID_ENV", "production")

# Determine the Plaid environment URL
PLAID_ENV_URLS = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com"
}
PLAID_HOST = PLAID_ENV_URLS.get(PLAID_ENV, "https://production.plaid.com")  # Default to development

# Configure Plaid client
configuration = configuration.Configuration(
    host=PLAID_HOST,
    api_key={
        'clientId': PLAID_CLIENT_ID,
        'secret': PLAID_SECRET
    }
)
api_client = api_client.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

app = Flask(__name__, static_folder='static', static_url_path='')

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/create_link_token', methods=['POST'])
def create_link_token():
    try:
        request_data = request.get_json()
        request = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(
                client_user_id='user_unique_id'  # Replace with actual user ID
            ),
            client_name='Your App Name',
            products=['transactions'],
            country_codes=[CountryCode('CA')],
            language='en',
            access_token=request_data['access_token']  # Add the access token for the item to update
        )
        response = client.link_token_create(request)
        return jsonify(response.to_dict())
    except ApiException as e:
        return jsonify(error=str(e)), 400

@app.route('/exchange_public_token', methods=['POST'])
def exchange_public_token():
    try:
        public_token = request.json['public_token']
        exchange_request = ItemPublicTokenExchangeRequest(
            public_token=public_token
        )
        response = client.item_public_token_exchange(exchange_request)
        return jsonify(response.to_dict())
    except ApiException as e:
        return jsonify(error=str(e)), 400

@app.route('/webhook', methods=['POST'])
def plaid_webhook():
    request_data = request.get_json()

    if request_data['webhook_type'] == 'ITEM':
        if request_data['webhook_code'] == 'LOGIN_REPAIRED':
            item_id = request_data['item_id']
            # Handle login repaired event
        elif request_data['webhook_code'] == 'PENDING_EXPIRATION':
            item_id = request_data['item_id']
            # Prompt the user to re-authenticate before the item expires
    return 'Webhook received', 200

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8000)
