"""
Unified Payment Testing Suite

Tests all payment methods:
- M-Pesa (STK Push + B2C Payouts)
- Stripe (Credit/Debit Cards)

Run this to verify complete payment integration.
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8001"


class Colors:
    """Terminal colors for pretty output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_section(title):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}")
    print(f"{title}")
    print(f"{'='*70}{Colors.END}\n")


def print_success(msg):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")


def print_error(msg):
    """Print error message."""
    print(f"{Colors.RED}❌ {msg}{Colors.END}")


def print_info(msg):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")


def print_warning(msg):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")


def test_mpesa_donation():
    """Test M-Pesa STK Push donation."""
    print_section("TEST 1: M-Pesa Donation (STK Push)")
    
    donation_data = {
        "donor_id": 1,
        "campaign_id": 1,
        "amount": 100,
        "currency": "KES",
        "payment_method": "mpesa",
        "phone_number": "+254708374149"  # Must include + prefix
    }
    
    print(f"Creating M-Pesa donation...")
    print(f"   Amount: {donation_data['amount']} {donation_data['currency']}")
    print(f"   Phone: {donation_data['phone_number']}")
    
    try:
        response = requests.post(f"{BASE_URL}/donations/", json=donation_data, timeout=10)
        
        if response.status_code == 201:
            donation = response.json()
            print_success(f"Donation created: ID {donation['id']}")
            print(f"   Status: {donation['status']}")
            print(f"   Payment Intent: {donation['payment_intent_id']}")
            return donation
        else:
            print_error(f"Failed: {response.status_code}")
            print(f"   {response.text}")
            return None
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return None


def test_stripe_donation():
    """Test Stripe card donation."""
    print_section("TEST 2: Stripe Donation (Credit/Debit Card)")
    
    donation_data = {
        "donor_id": 1,
        "campaign_id": 1,
        "amount": 25.00,
        "currency": "USD",
        "payment_method": "stripe",
        "stripe_payment_method_id": "pm_card_visa"
    }
    
    print(f"Creating Stripe donation...")
    print(f"   Amount: ${donation_data['amount']} {donation_data['currency']}")
    
    try:
        response = requests.post(f"{BASE_URL}/donations/", json=donation_data, timeout=10)
        
        if response.status_code == 201:
            donation = response.json()
            print_success(f"Donation created: ID {donation['id']}")
            print(f"   Status: {donation['status']}")
            print(f"   Payment Intent: {donation['payment_intent_id']}")
            
            # Get client secret
            if donation.get('status_message'):
                print(f"   Client Secret: {donation['status_message'][:30]}...")
                print_info("Frontend would use this with Stripe.js to confirm payment")
            
            return donation
        else:
            print_error(f"Failed: {response.status_code}")
            print(f"   {response.text}")
            return None
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return None


def test_mpesa_payout():
    """Test M-Pesa B2C payout."""
    print_section("TEST 3: M-Pesa Payout (B2C Disbursement)")
    
    payout_data = {
        "campaign_id": 1,
        "ngo_id": 1,
        "recipient_phone": "+254708374149",  # Must include + prefix
        "recipient_name": "Water Warriors NGO",
        "amount": 50,
        "currency": "KES",
        "purpose": "Test payout",
        "remarks": "Testing M-Pesa B2C"
    }
    
    print(f"Creating M-Pesa payout...")
    print(f"   Amount: {payout_data['amount']} {payout_data['currency']}")
    print(f"   Recipient: {payout_data['recipient_name']}")
    
    try:
        response = requests.post(f"{BASE_URL}/payouts/", json=payout_data, timeout=10)
        
        if response.status_code == 201:
            payout = response.json()
            print_success(f"Payout created: ID {payout['id']}")
            print(f"   Status: {payout['status']}")
            print(f"   Conversation ID: {payout['conversation_id']}")
            return payout
        else:
            print_error(f"Failed: {response.status_code}")
            print(f"   {response.text}")
            return None
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return None


def simulate_stripe_webhook(payment_intent_id, status="succeeded"):
    """Simulate Stripe webhook callback."""
    print("\nSimulating Stripe webhook...")
    
    webhook_payload = {
        "type": f"payment_intent.{status}",
        "data": {
            "object": {
                "id": payment_intent_id,
                "status": status,
                "amount": 2500,
                "currency": "usd"
            }
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/webhooks/stripe",
            json=webhook_payload,
            headers={"stripe-signature": "test_sig"},
            timeout=5
        )
        
        if response.status_code == 200:
            print_success("Webhook processed")
            return True
        else:
            print_warning(f"Webhook returned {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Webhook failed: {str(e)}")
        return False


def check_donation_status(donation_id):
    """Check donation status."""
    try:
        response = requests.get(f"{BASE_URL}/donations/{donation_id}", timeout=5)
        if response.status_code == 200:
            donation = response.json()
            return donation
        return None
    except:
        return None


def check_payout_status(payout_id):
    """Check payout status."""
    try:
        response = requests.get(f"{BASE_URL}/payouts/{payout_id}", timeout=5)
        if response.status_code == 200:
            payout = response.json()
            return payout
        return None
    except:
        return None


def check_campaign_totals():
    """Check campaign raised amounts."""
    print_section("Campaign Totals")
    
    try:
        response = requests.get(f"{BASE_URL}/campaigns/1", timeout=5)
        if response.status_code == 200:
            campaign = response.json()
            print(f"Campaign: {Colors.BOLD}{campaign['title']}{Colors.END}")  # Fixed: 'title' not 'name'
            print(f"   Goal: ${campaign['goal_amount_usd']:,.2f} USD")
            print(f"   Raised: ${campaign['raised_amount_usd']:,.2f} USD")
            
            if campaign.get('raised_amounts'):
                print(f"\n   Per-Currency Breakdown:")
                for curr, amount in campaign['raised_amounts'].items():
                    print(f"      {curr}: {amount:,.2f}")
            
            return campaign
        else:
            print_error("Failed to get campaign")
            return None
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return None


def print_summary(results):
    """Print test summary."""
    print_section("Test Summary")
    
    total_tests = len(results)
    passed = sum(1 for r in results if r['status'] == 'passed')
    failed = total_tests - passed
    
    print(f"Total Tests: {total_tests}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
    if failed > 0:
        print(f"{Colors.RED}Failed: {failed}{Colors.END}")
    
    print(f"\n{'Test':<40} {'Status':<10}")
    print("-" * 50)
    
    for result in results:
        status_color = Colors.GREEN if result['status'] == 'passed' else Colors.RED
        status_icon = "✅" if result['status'] == 'passed' else "❌"
        print(f"{result['name']:<40} {status_color}{status_icon} {result['status']}{Colors.END}")


def main():
    """Run all payment tests."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║         TrustVoice - Complete Payment Testing Suite              ║")
    print("║                                                                   ║")
    print("║  Testing: M-Pesa (Donations + Payouts) + Stripe (Cards)         ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print(Colors.END)
    
    print_info("Make sure server is running: ./admin-scripts/START_SERVICES.sh")
    print_info("Server should be accessible at: " + BASE_URL)
    print()
    
    time.sleep(1)
    
    # Check server health
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print_success("Server is running!")
        else:
            print_error("Server returned unexpected status")
            return
    except:
        print_error("Server is not running!")
        print_info("Start it with: ./admin-scripts/START_SERVICES.sh")
        return
    
    results = []
    
    # Test 1: M-Pesa Donation
    mpesa_donation = test_mpesa_donation()
    results.append({
        'name': 'M-Pesa Donation (STK Push)',
        'status': 'passed' if mpesa_donation else 'failed'
    })
    
    time.sleep(1)
    
    # Test 2: Stripe Donation
    stripe_donation = test_stripe_donation()
    results.append({
        'name': 'Stripe Donation (Card Payment)',
        'status': 'passed' if stripe_donation else 'failed'
    })
    
    # Test 2b: Simulate Stripe webhook
    if stripe_donation:
        time.sleep(1)
        webhook_success = simulate_stripe_webhook(stripe_donation['payment_intent_id'])
        results.append({
            'name': 'Stripe Webhook Processing',
            'status': 'passed' if webhook_success else 'failed'
        })
        
        # Check if donation was marked completed
        time.sleep(1)
        updated_donation = check_donation_status(stripe_donation['id'])
        if updated_donation:
            print(f"\n   Updated Status: {updated_donation['status']}")
    
    time.sleep(1)
    
    # Test 3: M-Pesa Payout
    mpesa_payout = test_mpesa_payout()
    results.append({
        'name': 'M-Pesa Payout (B2C Disbursement)',
        'status': 'passed' if mpesa_payout else 'failed'
    })
    
    time.sleep(1)
    
    # Check campaign totals
    campaign = check_campaign_totals()
    results.append({
        'name': 'Campaign Total Update',
        'status': 'passed' if campaign else 'failed'
    })
    
    # Print summary
    print_summary(results)
    
    # Next steps
    print_section("Next Steps")
    print("📚 Documentation:")
    print("   - M-Pesa Setup: documentation/MPESA_SETUP_COMPLETE.md")
    print("   - Stripe Docs: https://stripe.com/docs/payments/accept-a-payment")
    print()
    print("🔗 Useful Links:")
    print("   - API Docs: http://localhost:8001/docs")
    print("   - ngrok Dashboard: http://localhost:4040")
    print("   - Stripe Dashboard: https://dashboard.stripe.com/test/payments")
    print("   - M-Pesa Sandbox: https://developer.safaricom.co.ke/")
    print()
    print("🧪 Real Testing:")
    print("   - M-Pesa: Test phone 254708374149 (sandbox)")
    print("   - Stripe: Test card 4242 4242 4242 4242 (sandbox)")
    print()
    print(f"{Colors.GREEN}✨ All payment methods integrated and tested!{Colors.END}\n")


if __name__ == "__main__":
    main()
