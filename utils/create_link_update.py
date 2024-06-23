import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser

client = plaid_api.PlaidApi(plaid.Configuration(
    host=plaid.Environment.Sandbox,
    api_key={
        'clientId': 'your_client_id',
        'secret': 'your_secret',
    }
))

request = LinkTokenCreateRequest(
    user=LinkTokenCreateRequestUser(
        client_user_id='user_unique_id'
    ),
    client_name='Your App Name',
    products=['transactions'],
    country_codes=['CA'],  # Set the country code to Canada
    language='en',
    access_token='your_access_token',  # Add the access token for the item to update
)

response = client.link_token_create(request)
link_token = response['link_token']
