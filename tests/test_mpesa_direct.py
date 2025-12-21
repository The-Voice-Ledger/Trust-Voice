"""
Direct M-Pesa API Test

Tests M-Pesa API calls directly to see exact request/response.
"""

import requests
import base64
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Load credentials
CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET')
SHORTCODE = os.getenv('MPESA_SHORTCODE')
PASSKEY = os.getenv('MPESA_PASSKEY')
CALLBACK_URL = os.getenv('MPESA_CALLBACK_URL')

BASE_URL = 'https://sandbox.safaricom.co.ke'

print("="*70)
print("M-Pesa Direct API Test")
print("="*70)
print(f"\nConfiguration:")
print(f"  Consumer Key: {CONSUMER_KEY[:20]}...")
print(f"  Shortcode: {SHORTCODE}")
print(f"  Passkey: {PASSKEY[:20]}...")
print(f"  Callback: {CALLBACK_URL}")

# Step 1: Get Access Token
print("\n" + "="*70)
print("Step 1: Getting Access Token")
print("="*70)

auth_url = f"{BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
credentials = f"{CONSUMER_KEY}:{CONSUMER_SECRET}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()

headers = {
    'Authorization': f'Basic {encoded_credentials}'
}

try:
    response = requests.get(auth_url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        access_token = response.json()['access_token']
        print(f"\n✅ Access Token: {access_token[:30]}...")
    else:
        print(f"\n❌ Failed to get access token")
        exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Step 2: Test STK Push
print("\n" + "="*70)
print("Step 2: Testing STK Push (Lipa Na M-Pesa Online)")
print("="*70)

timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
password_str = f"{SHORTCODE}{PASSKEY}{timestamp}"
password = base64.b64encode(password_str.encode()).decode()

stk_push_url = f"{BASE_URL}/mpesa/stkpush/v1/processrequest"

headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

payload = {
    'BusinessShortCode': SHORTCODE,
    'Password': password,
    'Timestamp': timestamp,
    'TransactionType': 'CustomerPayBillOnline',
    'Amount': 1,  # Minimum amount
    'PartyA': '254708374149',  # Test phone
    'PartyB': SHORTCODE,
    'PhoneNumber': '254708374149',
    'CallBackURL': CALLBACK_URL,
    'AccountReference': 'Test123',
    'TransactionDesc': 'Test Payment'
}

print(f"\nRequest URL: {stk_push_url}")
print(f"Payload:")
for key, value in payload.items():
    if key == 'Password':
        print(f"  {key}: {value[:20]}...")
    else:
        print(f"  {key}: {value}")

try:
    response = requests.post(stk_push_url, json=payload, headers=headers)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('ResponseCode') == '0':
            print(f"\n✅ STK Push initiated successfully!")
            print(f"   CheckoutRequestID: {data.get('CheckoutRequestID')}")
        else:
            print(f"\n⚠️  STK Push returned error:")
            print(f"   {data.get('ResponseDescription')}")
    else:
        print(f"\n❌ STK Push failed")
        try:
            error_data = response.json()
            print(f"   Error: {error_data}")
        except:
            pass
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*70)
print("Test Complete")
print("="*70)
print("\n💡 If STK Push fails with 400:")
print("   1. Verify shortcode and passkey match")
print("   2. Check if sandbox credentials are approved")
print("   3. Ensure callback URL is publicly accessible (use ngrok)")
print("   4. Visit: https://developer.safaricom.co.ke/test_credentials")
