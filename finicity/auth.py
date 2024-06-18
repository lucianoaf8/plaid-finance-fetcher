import requests
import json

# Replace with your actual client ID and client secret
client_id = 'your_sandbox_client_id'
client_secret = 'your_sandbox_client_secret'

auth_url = 'https://api.finicity.com/aggregation/v1/oauth2/token'

auth_payload = {
    'grant_type': 'client_credentials'
}

auth_headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Basic {client_id}:{client_secret}'
}

response = requests.post(auth_url, headers=auth_headers, json=auth_payload)
access_token = response.json().get('access_token')

print(f'Access Token: {access_token}')
