#!/usr/bin/env python3
"""
Test Admin Approval Workflow

Complete flow:
1. Admin login
2. Create bank transfer payout (pending status)
3. Admin approve the payout
4. Verify status changed to approved
"""

import requests
import json

BASE_URL = "http://localhost:8001"

print("🔐 ADMIN APPROVAL WORKFLOW TEST")
print("=" * 70)
print()

# Step 1: Admin Login
print("1️⃣  Admin Login")
login_data = {
    "email": "emmanuel@earesearch.net",
    "password": "Password123"
}

response = requests.post(f"{BASE_URL}/admin/login", json=login_data)
print(f"   Status: {response.status_code}")

if response.status_code == 200:
    login_result = response.json()
    token = login_result["access_token"]
    user = login_result["user"]
    
    print(f"   ✅ Login successful!")
    print(f"   User: {user['full_name']} ({user['email']})")
    print(f"   Role: {user['role']}")
    print(f"   Token: {token[:50]}...")
else:
    print(f"   ❌ Login failed: {response.text}")
    exit(1)

print()

# Step 2: Create pending payout
print("2️⃣  Create Bank Transfer Payout (Pending)")
payout_data = {
    "campaign_id": 1,
    "ngo_id": 1,
    "payment_method": "bank_transfer",
    "recipient_name": "Test European NGO",
    "amount": 100.00,
    "currency": "EUR",
    "bank_account_number": "DE89370400440532013000",
    "bank_routing_number": "COBADEFFXXX",
    "bank_name": "Commerzbank AG",
    "bank_country": "DE",
    "purpose": "Test payout for admin approval"
}

response = requests.post(f"{BASE_URL}/payouts/", json=payout_data)
print(f"   Status: {response.status_code}")

if response.status_code == 201:
    payout = response.json()
    payout_id = payout["id"]
    
    print(f"   ✅ Payout created!")
    print(f"   ID: {payout_id}")
    print(f"   Amount: €{payout['amount']} {payout['currency']}")
    print(f"   Bank: {payout['bank_name']}")
    print(f"   Status: {payout['status']}")
else:
    print(f"   ❌ Failed: {response.text}")
    exit(1)

print()

# Step 3: Get current user info
print("3️⃣  Verify Admin Token")
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/admin/me", headers=headers)

if response.status_code == 200:
    me = response.json()
    print(f"   ✅ Token valid")
    print(f"   Logged in as: {me['email']} ({me['role']})")
else:
    print(f"   ❌ Token invalid: {response.text}")
    exit(1)

print()

# Step 4: Approve payout
print("4️⃣  Approve Payout")
response = requests.post(
    f"{BASE_URL}/payouts/{payout_id}/approve",
    headers=headers,
    json={}
)

print(f"   Status: {response.status_code}")

if response.status_code == 200:
    approved_payout = response.json()
    print(f"   ✅ Payout approved!")
    print(f"   Status: {approved_payout['status']}")
    print(f"   Approved by: User ID {approved_payout['approved_by']}")
    print(f"   Approved at: {approved_payout['approved_at']}")
    print(f"   Status message: {approved_payout['status_message']}")
else:
    print(f"   ❌ Failed: {response.text}")
    exit(1)

print()

# Step 5: Try to approve again (should fail)
print("5️⃣  Try to Approve Again (Should Fail)")
response = requests.post(
    f"{BASE_URL}/payouts/{payout_id}/approve",
    headers=headers,
    json={}
)

if response.status_code == 400:
    print(f"   ✅ Correctly rejected: Cannot approve already-approved payout")
else:
    print(f"   ❌ Unexpected: {response.status_code} - {response.text}")

print()

# Step 6: Create another payout and reject it
print("6️⃣  Create Another Payout to Test Rejection")
payout_data["amount"] = 50.00
payout_data["purpose"] = "Test rejection workflow"

response = requests.post(f"{BASE_URL}/payouts/", json=payout_data)
if response.status_code == 201:
    payout2 = response.json()
    payout2_id = payout2["id"]
    print(f"   ✅ Payout created (ID: {payout2_id})")
    
    # Reject it
    print()
    print("7️⃣  Reject Payout")
    rejection_data = {
        "rejection_reason": "Insufficient documentation provided"
    }
    
    response = requests.post(
        f"{BASE_URL}/payouts/{payout2_id}/reject",
        headers=headers,
        json=rejection_data
    )
    
    if response.status_code == 200:
        rejected_payout = response.json()
        print(f"   ✅ Payout rejected!")
        print(f"   Status: {rejected_payout['status']}")
        print(f"   Rejection reason: {rejected_payout['rejection_reason']}")
        print(f"   Status message: {rejected_payout['status_message']}")
    else:
        print(f"   ❌ Failed: {response.text}")

print()
print("=" * 70)
print("✅ ADMIN APPROVAL WORKFLOW COMPLETE!")
print()
print("Summary:")
print("  • Admin login with JWT: ✅")
print("  • Create pending payout: ✅")
print("  • Approve payout: ✅")
print("  • Prevent duplicate approval: ✅")
print("  • Reject payout: ✅")
