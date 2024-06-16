import os
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid import configuration, api_client
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.country_code import CountryCode
from plaid.model.products import Products

app = Flask(__name__)
load_dotenv()

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = os.getenv("PLAID_ENV", "development")

PLAID_ENV_URLS = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com"
}
PLAID_HOST = PLAID_ENV_URLS.get(PLAID_ENV, "https://development.plaid.com")

configuration = configuration.Configuration(
    host=PLAID_HOST,
    api_key={
        'clientId': PLAID_CLIENT_ID,
        'secret': PLAID_SECRET
    }
)
api_client = api_client.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

# Generate link token on startup
@app.before_first_request
def generate_link_token():
    try:
        request = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(client_user_id='unique_static_user_id'),
            client_name='Your App',
            products=[Products('transactions'), Products('liabilities')],
            country_codes=[CountryCode('CA')],
            language='en'
        )
        response = client.link_token_create(request)
        global link_token
        link_token = response['link_token']
    except plaid.ApiException as e:
        print(f"Error generating link token: {e}")

@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>Plaid Link</title>
      <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
      <script>
        document.addEventListener('DOMContentLoaded', (event) => {
          var linkHandler = Plaid.create({
            token: "{{ link_token }}",
            onSuccess: function(public_token, metadata) {
              fetch('/exchange_public_token', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({ public_token: public_token }),
              })
              .then(response => response.json())
              .then(data => {
                console.log('Access Token:', data.access_token);
              })
              .catch(error => {
                console.error('Error:', error);
              });
            },
            onExit: function(err, metadata) {
              if (err != null) {
                console.error('Exit with error:', err);
              }
            },
          });

          document.getElementById('linkButton').onclick = function() {
            linkHandler.open();
          };
        });
      </script>
    </head>
    <body>
      <button id="linkButton">Link Bank Account</button>
    </body>
    </html>
    """, link_token=link_token)

@app.route('/exchange_public_token', methods=['POST'])
def exchange_public_token():
    public_token = request.json.get('public_token')
    if not public_token:
        return jsonify({'error': 'public_token is required'}), 400

    try:
        request = ItemPublicTokenExchangeRequest(
            client_id=PLAID_CLIENT_ID,
            secret=PLAID_SECRET,
            public_token=public_token
        )
        response = client.item_public_token_exchange(request)
        access_token = response['access_token']
        return jsonify({'access_token': access_token})
    except plaid.ApiException as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
