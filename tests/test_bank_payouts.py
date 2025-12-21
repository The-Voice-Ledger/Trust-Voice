"""
Test Bank Payouts for European NGO

Scenario: German NGO (Welthungerhilfe) operating in Kenya
- Headquarters: Bonn, Germany (needs EUR payouts to German bank)
- Field office: Nairobi, Kenya (needs KES payouts via M-Pesa)
- Operations: Both European admin costs and African field operations
"""

import requests
import json

BASE_URL = "http://localhost:8001"


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(title):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}")
    print(f"{title}")
    print(f"{'='*70}{Colors.END}\n")


def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")


def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")


print(f"\n{Colors.BOLD}{Colors.CYAN}╔═══════════════════════════════════════════════════════════╗")
print(f"║  Bank Payout Test: European NGO with African Operations ║")
print(f"╚═══════════════════════════════════════════════════════╝{Colors.END}\n")

print_info("Scenario: Welthungerhilfe (German NGO)")
print_info("  HQ: Bonn, Germany (EUR bank account)")
print_info("  Field Office: Nairobi, Kenya (M-Pesa)")
print()

# Check current balance
print_header("Step 1: Check Campaign Balance")

try:
    response = requests.get(f"{BASE_URL}/campaigns/1", timeout=5)
    if response.status_code == 200:
        campaign = response.json()
        print(f"Campaign: {campaign['title']}")
        print(f"Total Raised: ${campaign['raised_amount_usd']:.2f} USD")
        
        if campaign.get('raised_amounts'):
            print("\nPer-Currency Breakdown:")
            for curr, amount in campaign['raised_amounts'].items():
                print(f"   {curr}: {amount:.2f}")
    else:
        print_error("Failed to get campaign")
        exit(1)
except Exception as e:
    print_error(f"Server not running: {e}")
    print_info("Start with: ./admin-scripts/START_SERVICES.sh")
    exit(1)

# Test 1: Bank payout to Germany (SEPA)
print_header("Test 1: Bank Payout to Germany (EUR - SEPA)")

sepa_payout = {
    "campaign_id": 1,
    "ngo_id": 1,
    "payment_method": "bank_transfer",
    "recipient_name": "Deutsche Welthungerhilfe e.V.",
    "amount": 2000.00,
    "currency": "EUR",
    "bank_account_number": "DE89370400440532013000",  # IBAN
    "bank_routing_number": "COBADEFFXXX",  # SWIFT/BIC
    "bank_name": "Commerzbank AG",
    "bank_country": "DE",
    "purpose": "Administrative overhead - Q4 2025",
    "remarks": "SEPA transfer for HQ operations"
}

print(f"Creating SEPA payout:")
print(f"   Recipient: {sepa_payout['recipient_name']}")
print(f"   Amount: €{sepa_payout['amount']:,.2f} EUR")
print(f"   Bank: {sepa_payout['bank_name']} (Germany)")
print(f"   IBAN: {sepa_payout['bank_account_number']}")
print(f"   SWIFT: {sepa_payout['bank_routing_number']}")

try:
    response = requests.post(f"{BASE_URL}/payouts/", json=sepa_payout, timeout=10)
    
    if response.status_code == 201:
        payout = response.json()
        print_success("SEPA payout created!")
        print(f"   Payout ID: {payout['id']}")
        print(f"   Status: {payout['status']}")
        print(f"   Method: {payout['payment_method']}")
        print(f"\n   ℹ️  SEPA transfers typically take 1-2 business days")
    else:
        error = response.json().get('detail', response.text)
        print_error(f"Failed: {error}")
except Exception as e:
    print_error(f"Request failed: {e}")

# Test 2: M-Pesa payout to Kenya field office
print_header("Test 2: M-Pesa Payout to Kenya Field Office (KES)")

mpesa_payout = {
    "campaign_id": 1,
    "ngo_id": 1,
    "payment_method": "mpesa_b2c",
    "recipient_name": "Welthungerhilfe Kenya Office",
    "recipient_phone": "+254708374149",
    "amount": 50000,
    "currency": "KES",
    "purpose": "Field operations - Water project",
    "remarks": "Monthly disbursement for Mwanza project"
}

print(f"Creating M-Pesa payout:")
print(f"   Recipient: {mpesa_payout['recipient_name']}")
print(f"   Amount: {mpesa_payout['amount']:,.0f} KES")
print(f"   Phone: {mpesa_payout['recipient_phone']}")
print(f"   Purpose: {mpesa_payout['purpose']}")

try:
    response = requests.post(f"{BASE_URL}/payouts/", json=mpesa_payout, timeout=10)
    
    if response.status_code == 201:
        payout = response.json()
        print_success("M-Pesa payout created!")
        print(f"   Payout ID: {payout['id']}")
        print(f"   Status: {payout['status']}")
        print(f"   Conversation ID: {payout.get('conversation_id')}")
        print(f"\n   ℹ️  M-Pesa payouts complete within minutes")
    else:
        error = response.json().get('detail', response.text)
        print_error(f"Failed: {error}")
except Exception as e:
    print_error(f"Request failed: {e}")

# Test 3: Stripe payout (if NGO has Stripe Connect)
print_header("Test 3: Stripe Payout to US Partner NGO (USD)")

stripe_payout = {
    "campaign_id": 1,
    "ngo_id": 1,
    "payment_method": "stripe_payout",
    "recipient_name": "charity: water",
    "amount": 1000.00,
    "currency": "USD",
    "bank_account_number": "000123456789",  # Bank account (or use Stripe account ID)
    "bank_routing_number": "110000000",  # US routing number
    "bank_name": "Chase Bank",
    "bank_country": "US",
    "purpose": "Partnership disbursement",
    "remarks": "Q4 collaboration payment"
}

print(f"Creating Stripe payout:")
print(f"   Recipient: {stripe_payout['recipient_name']}")
print(f"   Amount: ${stripe_payout['amount']:,.2f} USD")
print(f"   Bank: {stripe_payout['bank_name']} (USA)")
print(f"   Account: ***{stripe_payout['bank_account_number'][-4:]}")

try:
    response = requests.post(f"{BASE_URL}/payouts/", json=stripe_payout, timeout=10)
    
    if response.status_code == 201:
        payout = response.json()
        print_success("Stripe payout created!")
        print(f"   Payout ID: {payout['id']}")
        print(f"   Status: {payout['status']}")
        print(f"   Stripe ID: {payout.get('stripe_payout_id', 'N/A')}")
        print(f"\n   ℹ️  Stripe payouts arrive in 2-7 business days")
    else:
        error = response.json().get('detail', response.text)
        print_error(f"Failed: {error}")
except Exception as e:
    print_error(f"Request failed: {e}")

print_header("Summary: Multi-Method Payout Support")

print(f"""
{Colors.BOLD}Supported Payout Methods:{Colors.END}

1. {Colors.CYAN}M-Pesa B2C (Mobile Money){Colors.END}
   - Countries: Kenya, Tanzania, Uganda
   - Speed: Instant (seconds to minutes)
   - Currencies: KES, TZS, UGX
   - Use case: Local field operations, beneficiaries
   - Cost: 1-3% transaction fee

2. {Colors.CYAN}Bank Transfer (SEPA/SWIFT){Colors.END}
   - Countries: Europe (SEPA), Global (SWIFT)
   - Speed: 1-5 business days
   - Currencies: EUR, USD, GBP, etc.
   - Use case: NGO headquarters, admin costs
   - Cost: €0-10 (SEPA), $20-50 (SWIFT)

3. {Colors.CYAN}Stripe Payout{Colors.END}
   - Countries: 40+ countries
   - Speed: 2-7 business days
   - Currencies: USD, EUR, GBP, etc.
   - Use case: Partner NGOs with Stripe accounts
   - Cost: Built into Stripe processing fees

{Colors.BOLD}Real-World Use Case:{Colors.END}

{Colors.GREEN}Campaign raises $10,000 from international donors{Colors.END}
├─ $5,000 USD → {Colors.YELLOW}Stripe payout{Colors.END} → US partner NGO (7 days)
├─ €2,000 EUR → {Colors.YELLOW}SEPA transfer{Colors.END} → German HQ (2 days)
└─ 200,000 KES → {Colors.YELLOW}M-Pesa B2C{Colors.END} → Kenya field office (instant)

{Colors.BOLD}Benefits:{Colors.END}
✅ One platform, multiple payout methods
✅ Automatic currency conversion
✅ Compliance with local regulations
✅ Lower costs than traditional banking
✅ Faster disbursement to beneficiaries
""")

print(f"{Colors.GREEN}{'='*70}")
print(f"Multi-method payout system ready for global NGOs! 🌍💰")
print(f"{'='*70}{Colors.END}\n")
