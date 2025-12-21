"""
Test M-Pesa Donation and Payout Flow

Tests both:
1. STK Push (donation) - Money coming IN
2. B2C Payment (payout) - Money going OUT
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"


def test_mpesa_donation():
    """Test M-Pesa STK Push donation flow."""
    print("\n" + "="*60)
    print("TEST 1: M-Pesa STK Push (Donation - Money IN)")
    print("="*60)
    
    # Create donation
    donation_data = {
        "donor_id": 1,
        "campaign_id": 1,
        "amount": 100,
        "currency": "KES",
        "payment_method": "mpesa",
        "phone_number": "254708374149"
    }
    
    print("\n1️⃣  Creating donation...")
    print(f"   Amount: {donation_data['amount']} {donation_data['currency']}")
    print(f"   Phone: {donation_data['phone_number']}")
    
    response = requests.post(
        f"{BASE_URL}/donations/",
        json=donation_data
    )
    
    if response.status_code == 201:
        donation = response.json()
        print(f"   ✅ Donation created: ID {donation['id']}")
        print(f"   Status: {donation['status']}")
        print(f"   Payment Intent ID: {donation['payment_intent_id']}")
        return donation
    else:
        print(f"   ❌ Failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return None


def test_mpesa_payout():
    """Test M-Pesa B2C payout flow."""
    print("\n" + "="*60)
    print("TEST 2: M-Pesa B2C (Payout - Money OUT)")
    print("="*60)
    
    # Create payout
    payout_data = {
        "campaign_id": 1,
        "ngo_id": 1,
        "recipient_phone": "254708374149",
        "recipient_name": "Water Warriors NGO",
        "amount": 50,
        "currency": "KES",
        "purpose": "Test payout",
        "remarks": "Testing M-Pesa B2C disbursement"
    }
    
    print("\n1️⃣  Creating payout...")
    print(f"   Amount: {payout_data['amount']} {payout_data['currency']}")
    print(f"   Recipient: {payout_data['recipient_name']}")
    print(f"   Phone: {payout_data['recipient_phone']}")
    
    response = requests.post(
        f"{BASE_URL}/payouts/",
        json=payout_data
    )
    
    if response.status_code == 201:
        payout = response.json()
        print(f"   ✅ Payout created: ID {payout['id']}")
        print(f"   Status: {payout['status']}")
        print(f"   Conversation ID: {payout['conversation_id']}")
        return payout
    else:
        print(f"   ❌ Failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return None


def check_donation_status(donation_id):
    """Check donation status."""
    print("\n2️⃣  Checking donation status...")
    response = requests.get(f"{BASE_URL}/donations/{donation_id}")
    
    if response.status_code == 200:
        donation = response.json()
        print(f"   Status: {donation['status']}")
        return donation
    else:
        print(f"   ❌ Failed to check status")
        return None


def check_payout_status(payout_id):
    """Check payout status."""
    print("\n2️⃣  Checking payout status...")
    response = requests.get(f"{BASE_URL}/payouts/{payout_id}")
    
    if response.status_code == 200:
        payout = response.json()
        print(f"   Status: {payout['status']}")
        if payout.get('transaction_id'):
            print(f"   Transaction ID: {payout['transaction_id']}")
        return payout
    else:
        print(f"   ❌ Failed to check status")
        return None


def main():
    """Run all tests."""
    print("\n🚀 TrustVoice M-Pesa Testing Suite")
    print("Testing both donations (STK Push) and payouts (B2C)")
    print("\nℹ️  Make sure the server is running: ./admin-scripts/START_SERVICES.sh")
    
    # Test 1: Donation (STK Push)
    donation = test_mpesa_donation()
    if donation:
        time.sleep(2)
        check_donation_status(donation['id'])
    
    # Test 2: Payout (B2C)
    payout = test_mpesa_payout()
    if payout:
        time.sleep(2)
        check_payout_status(payout['id'])
    
    print("\n" + "="*60)
    print("✅ Tests Complete!")
    print("="*60)
    print("\n📋 Next Steps:")
    print("   1. Check ngrok dashboard: http://localhost:4040")
    print("   2. M-Pesa will send webhooks when payments complete")
    print("   3. Check API logs: tail -f logs/trustvoice_api.log")
    print("\n💡 In production:")
    print("   - Donations: Money flows FROM donors TO campaigns")
    print("   - Payouts: Money flows FROM campaigns TO NGOs")
    print("")


if __name__ == "__main__":
    main()
