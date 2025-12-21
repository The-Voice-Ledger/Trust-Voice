"""
Test Stripe Payment Flow

Tests Stripe credit/debit card donations.

Stripe Test Cards:
- Success: 4242 4242 4242 4242
- Decline: 4000 0000 0000 0002
- Requires Auth: 4000 0025 0000 3155
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"

# Stripe test card
TEST_CARD = {
    "number": "4242424242424242",
    "exp_month": 12,
    "exp_year": 2026,
    "cvc": "123"
}


def test_stripe_donation():
    """Test Stripe donation flow."""
    print("\n" + "="*60)
    print("TEST: Stripe Donation (Credit/Debit Card)")
    print("="*60)
    
    # Step 1: Create donation (gets PaymentIntent)
    donation_data = {
        "donor_id": 1,
        "campaign_id": 1,
        "amount": 50.00,
        "currency": "USD",
        "payment_method": "stripe",
        "stripe_payment_method_id": "pm_card_visa"  # Test payment method
    }
    
    print("\n1️⃣  Creating Stripe donation...")
    print(f"   Amount: ${donation_data['amount']} {donation_data['currency']}")
    
    response = requests.post(
        f"{BASE_URL}/donations/",
        json=donation_data
    )
    
    if response.status_code == 201:
        donation = response.json()
        print(f"   ✅ Donation created: ID {donation['id']}")
        print(f"   Status: {donation['status']}")
        print(f"   Payment Intent ID: {donation['payment_intent_id']}")
        
        # In real app, client_secret is used by frontend to confirm payment
        if donation.get('status_message'):
            client_secret = donation['status_message']
            print(f"   Client Secret: {client_secret[:20]}...")
            print(f"   ℹ️  Frontend would use this to confirm payment with Stripe.js")
        
        # Step 2: Simulate webhook (in production, Stripe sends this)
        print("\n2️⃣  Simulating Stripe webhook...")
        print("   ℹ️  In production, Stripe sends this automatically")
        
        webhook_payload = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": donation['payment_intent_id'],
                    "status": "succeeded",
                    "amount": int(donation_data['amount'] * 100),
                    "currency": donation_data['currency'].lower()
                }
            }
        }
        
        webhook_response = requests.post(
            f"{BASE_URL}/webhooks/stripe",
            json=webhook_payload,
            headers={"stripe-signature": "test_signature"}
        )
        
        if webhook_response.status_code == 200:
            print("   ✅ Webhook processed")
        else:
            print(f"   ⚠️  Webhook returned {webhook_response.status_code}")
        
        # Step 3: Check updated status
        print("\n3️⃣  Checking donation status...")
        time.sleep(1)
        
        status_response = requests.get(f"{BASE_URL}/donations/{donation['id']}")
        if status_response.status_code == 200:
            updated_donation = status_response.json()
            print(f"   Status: {updated_donation['status']}")
            
            if updated_donation['status'] == 'completed':
                print("   ✅ Payment completed successfully!")
            else:
                print(f"   ℹ️  Status is '{updated_donation['status']}'")
        
        return donation
    else:
        print(f"   ❌ Failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return None


def test_stripe_with_real_card():
    """
    Test with Stripe test card (requires Stripe.js on frontend).
    
    This demonstrates the full flow but can't be automated
    without a frontend.
    """
    print("\n" + "="*60)
    print("INFO: Real Stripe Card Flow")
    print("="*60)
    print("\nStripe Test Cards:")
    print("   ✅ Success: 4242 4242 4242 4242")
    print("   ❌ Decline: 4000 0000 0000 0002")
    print("   🔐 Requires Auth: 4000 0025 0000 3155")
    print("\nFull flow requires frontend with Stripe.js:")
    print("   1. Backend creates PaymentIntent → gets client_secret")
    print("   2. Frontend uses client_secret with Stripe.js")
    print("   3. User enters card details (4242...)")
    print("   4. Stripe confirms payment")
    print("   5. Stripe sends webhook to /webhooks/stripe")
    print("   6. Backend marks donation as completed")
    print("\n📚 Docs: https://stripe.com/docs/payments/accept-a-payment")


def check_campaign_total():
    """Check if campaign total was updated."""
    print("\n" + "="*60)
    print("Checking Campaign Total")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/campaigns/1")
    if response.status_code == 200:
        campaign = response.json()
        print(f"\n   Campaign: {campaign['name']}")
        print(f"   Goal: ${campaign['goal_amount_usd']}")
        print(f"   Raised (USD): ${campaign['raised_amount_usd']}")
        
        if campaign.get('raised_amounts'):
            print(f"   Per-currency breakdown:")
            for curr, amount in campaign['raised_amounts'].items():
                print(f"      - {curr}: {amount}")
    else:
        print(f"   ❌ Failed to get campaign")


def main():
    """Run Stripe tests."""
    print("\n🚀 TrustVoice Stripe Testing Suite")
    print("Testing credit/debit card donations via Stripe")
    print("\nℹ️  Make sure the server is running: ./admin-scripts/START_SERVICES.sh")
    
    # Test donation flow
    donation = test_stripe_donation()
    
    if donation:
        # Show info about real card testing
        test_stripe_with_real_card()
        
        # Check campaign total
        check_campaign_total()
    
    print("\n" + "="*60)
    print("✅ Tests Complete!")
    print("="*60)
    print("\n📋 Next Steps:")
    print("   1. Donations work via API (backend creates PaymentIntent)")
    print("   2. For real card testing, need frontend with Stripe.js")
    print("   3. Check Stripe Dashboard: https://dashboard.stripe.com/test/payments")
    print("\n💡 Stripe Webhook Setup:")
    print("   1. Get ngrok URL from: http://localhost:4040")
    print("   2. Add to Stripe Dashboard: Webhooks → Add endpoint")
    print("   3. URL: https://your-ngrok-url/webhooks/stripe")
    print("   4. Events: payment_intent.succeeded, payment_intent.failed")
    print("")


if __name__ == "__main__":
    main()
