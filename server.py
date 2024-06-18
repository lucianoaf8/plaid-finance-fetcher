from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load environment variables
load_dotenv()

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = 'production'  # Use production environment

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

@app.route('/create_link_token', methods=['POST'])
def create_link_token():
    try:
        request = LinkTokenCreateRequest(
            products=[Products('auth'), Products('transactions'), Products('liabilities')],  # Add the products you need
            client_name='Your App Name',
            country_codes=[CountryCode('CA')],  # Canadian institutions
            language='en',
            user=LinkTokenCreateRequestUser(
                client_user_id='unique-user-id'  # Replace with a unique identifier for the user
            )
        )
        response = client.link_token_create(request)
        link_token = response['link_token']
        return jsonify({'link_token': link_token})
    except Exception as e:
        error_message = str(e)
        print(f"Error creating link token: {error_message}")  # Log the error message
        return jsonify({'error': error_message}), 400



@app.route('/get_access_token', methods=['POST'])
def get_access_token():
    public_token = request.json['public_token']
    try:
        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = client.item_public_token_exchange(exchange_request)
        access_token = exchange_response['access_token']
        return jsonify({'access_token': access_token})
    except Exception as e:
        error_message = str(e)
        print(f"Error exchanging public token: {error_message}")  # Log the error message
        return jsonify({'error': error_message}), 400

if __name__ == '__main__':
    app.run(port=5000)
