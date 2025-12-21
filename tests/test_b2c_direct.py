"""
Test M-Pesa B2C directly with detailed logging
"""

import requests
import os
import base64
from dotenv import load_dotenv

load_dotenv()

# Configuration
CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET')
SHORTCODE = os.getenv('MPESA_SHORTCODE')
INITIATOR_NAME = os.getenv('MPESA_INITIATOR_NAME')
INITIATOR_PASSWORD = os.getenv('MPESA_INITIATOR_PASSWORD')
B2C_RESULT_URL = os.getenv('MPESA_B2C_RESULT_URL', 'https://briary-torridly-raul.ngrok-free.dev/webhooks/mpesa/b2c/result')
B2C_TIMEOUT_URL = os.getenv('MPESA_B2C_QUEUE_TIMEOUT_URL', 'https://briary-torridly-raul.ngrok-free.dev/webhooks/mpesa/b2c/timeout')

BASE_URL = 'https://sandbox.safaricom.co.ke'

print("="*70)
print("M-Pesa B2C Direct Test")
print("="*70)
print(f"\nConfiguration:")
print(f"  Shortcode: {SHORTCODE}")
print(f"  Initiator Name: {INITIATOR_NAME}")
print(f"  Initiator Password: {INITIATOR_PASSWORD[:30]}...")
print(f"  Result URL: {B2C_RESULT_URL}")
print(f"  Timeout URL: {B2C_TIMEOUT_URL}")

# Get Access Token
print("\n" + "="*70)
print("Getting Access Token")
print("="*70)

auth_url = f"{BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
credentials = f"{CONSUMER_KEY}:{CONSUMER_SECRET}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()

try:
    response = requests.get(auth_url, headers={'Authorization': f'Basic {encoded_credentials}'})
    access_token = response.json()['access_token']
    print(f"✅ Access Token: {access_token[:30]}...")
except Exception as e:
    print(f"❌ Failed: {e}")
    exit(1)

# Test B2C
print("\n" + "="*70)
print("Testing B2C Payment Request")
print("="*70)

b2c_url = f"{BASE_URL}/mpesa/b2c/v1/paymentrequest"

headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

payload = {
    'InitiatorName': INITIATOR_NAME,
    'SecurityCredential': INITIATOR_PASSWORD,
    'CommandID': 'BusinessPayment',
    'Amount': 10,  # Minimum test amount
    'PartyA': SHORTCODE,
    'PartyB': '254708374149',  # Test phone
    'Remarks': 'Test B2C payout',
    'QueueTimeOutURL': B2C_TIMEOUT_URL,
    'ResultURL': B2C_RESULT_URL,
    'Occasion': 'Test'
}

print(f"\nRequest URL: {b2c_url}")
print(f"\nPayload:")
for key, value in payload.items():
    if key == 'SecurityCredential':
        print(f"  {key}: {value[:30]}...")
    else:
        print(f"  {key}: {value}")

try:
    response = requests.post(b2c_url, json=payload, headers=headers)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('ResponseCode') == '0':
            print(f"\n✅ B2C initiated successfully!")
            print(f"   ConversationID: {data.get('ConversationID')}")
            print(f"   OriginatorConversationID: {data.get('OriginatorConversationID')}")
        else:
            print(f"\n⚠️  B2C returned error code: {data.get('ResponseCode')}")
            print(f"   {data.get('ResponseDescription')}")
    else:
        print(f"\n❌ B2C failed with status {response.status_code}")
        try:
            error = response.json()
            print(f"   Error: {error}")
        except:
            print(f"   Raw response: {response.text}")
            
except Exception as e:
    print(f"❌ Exception: {e}")

print("\n" + "="*70)
print("💡 Common B2C Issues:")
print("="*70)
print("1. Security Credential must be Base64-encoded public key")
print("2. For sandbox, use test credentials from:")
print("   https://developer.safaricom.co.ke/test_credentials")
print("3. Initiator must be approved for your app")
print("4. Shortcode must have sufficient balance in sandbox")
