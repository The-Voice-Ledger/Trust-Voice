# M-Pesa Integration - Complete Setup

## ✅ What's Been Implemented

### 1. STK Push (Donations - Money IN)
- ✅ Initiate payment prompt on donor's phone
- ✅ Webhook callback for payment confirmation
- ✅ Donation status tracking (pending → completed/failed)
- ✅ Multi-currency support with per-currency buckets

### 2. B2C Payments (Payouts - Money OUT)
- ✅ Send money to NGOs/beneficiaries
- ✅ Webhook callbacks for payout results
- ✅ Payout status tracking (pending → processing → completed/failed)
- ✅ Full API endpoints for managing payouts

---

## 🔑 M-Pesa Credentials (Sandbox)

All credentials are configured in `.env`:

```bash
# Lipa Na M-Pesa Online (STK Push - Donations)
MPESA_CONSUMER_KEY=tANfIX5AAHA0672M73hhUy3UA3hJQJE1ADNYA1y3rFZORe8P
MPESA_CONSUMER_SECRET=knTUIMYX4rSdPoOrP9yFmPZQ18fQm8M6GK7fNjp7JkUGaAzWBtb23a6NqqRAWuoK
MPESA_SHORTCODE=174379
MPESA_PASSKEY=bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919
MPESA_CALLBACK_URL=http://localhost:8001/webhooks/mpesa

# B2C (Business to Customer - Payouts)
MPESA_INITIATOR_NAME=testapi
MPESA_INITIATOR_PASSWORD=X6v5Vk1U9KvH1bSF... (encrypted password)
MPESA_B2C_QUEUE_TIMEOUT_URL=http://localhost:8001/webhooks/mpesa/b2c/timeout
MPESA_B2C_RESULT_URL=http://localhost:8001/webhooks/mpesa/b2c/result
```

---

## 🚀 Quick Start

### Step 1: Start Services
```bash
./admin-scripts/START_SERVICES.sh
```

This will:
- Start FastAPI on http://localhost:8001
- Start ngrok tunnel with public URL
- Auto-update webhook URLs in `.env`

### Step 2: Test Donation & Payout
```bash
source venv/bin/activate
python test_mpesa_flow.py
```

### Step 3: Check Status
- **API Docs:** http://localhost:8001/docs
- **ngrok Dashboard:** http://localhost:4040
- **Logs:** `tail -f logs/trustvoice_api.log`

---

## 📊 API Endpoints

### Donations (STK Push)

**Create Donation:**
```bash
POST /donations/
{
  "donor_id": 1,
  "campaign_id": 1,
  "amount": 1000,
  "currency": "KES",
  "payment_method": "mpesa",
  "phone_number": "254708374149"
}
```

**Get Donation:**
```bash
GET /donations/{id}
```

**M-Pesa Webhook (STK Push Callback):**
```bash
POST /webhooks/mpesa
```

---

### Payouts (B2C)

**Create Payout:**
```bash
POST /payouts/
{
  "campaign_id": 1,
  "ngo_id": 1,
  "recipient_phone": "254708374149",
  "recipient_name": "Water Warriors NGO",
  "amount": 50000,
  "currency": "KES",
  "purpose": "Campaign completion disbursement",
  "remarks": "Mwanza Water Project - Final Payment"
}
```

**Get Payout:**
```bash
GET /payouts/{id}
```

**List Campaign Payouts:**
```bash
GET /payouts/campaign/{campaign_id}
```

**M-Pesa Webhooks (B2C Callbacks):**
```bash
POST /webhooks/mpesa/b2c/result    # Payment result
POST /webhooks/mpesa/b2c/timeout   # Timeout notification
```

---

## 🔄 Payment Flows

### Donation Flow (STK Push)
```
1. Client calls POST /donations/
2. Backend calls M-Pesa STK Push API
3. M-Pesa sends prompt to donor's phone
4. Donor enters PIN and confirms
5. M-Pesa sends callback to /webhooks/mpesa
6. Backend updates donation status to 'completed'
7. Campaign raised_amounts updated
```

### Payout Flow (B2C)
```
1. Admin calls POST /payouts/
2. Backend validates sufficient funds
3. Backend calls M-Pesa B2C API
4. M-Pesa queues payment for processing
5. M-Pesa processes payment asynchronously
6. M-Pesa sends result to /webhooks/mpesa/b2c/result
7. Backend updates payout status to 'completed'
8. Recipient receives money on their M-Pesa
```

---

## 🧪 Testing

### Test Phone Number (Sandbox)
```
254708374149
```

### Test Scenarios

**1. Successful Donation:**
```bash
curl -X POST http://localhost:8001/donations/ \
  -H "Content-Type: application/json" \
  -d '{
    "donor_id": 1,
    "campaign_id": 1,
    "amount": 100,
    "currency": "KES",
    "payment_method": "mpesa",
    "phone_number": "254708374149"
  }'
```

**2. Successful Payout:**
```bash
curl -X POST http://localhost:8001/payouts/ \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": 1,
    "ngo_id": 1,
    "recipient_phone": "254708374149",
    "recipient_name": "Test NGO",
    "amount": 50,
    "currency": "KES",
    "purpose": "Test payout",
    "remarks": "Testing B2C"
  }'
```

---

## 📋 Database Schema

### Payout Model
```sql
CREATE TABLE payouts (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id),
    ngo_id INTEGER REFERENCES ngo_organizations(id),
    recipient_phone VARCHAR(20) NOT NULL,
    recipient_name VARCHAR(200),
    amount FLOAT NOT NULL,
    currency VARCHAR(3) DEFAULT 'KES',
    payment_method VARCHAR(20) DEFAULT 'mpesa_b2c',
    conversation_id VARCHAR(100),
    originator_conversation_id VARCHAR(100),
    transaction_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    status_message TEXT,
    purpose VARCHAR(200),
    remarks TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
```

---

## 🔍 Monitoring

### Check Donation Status
```bash
# Get donation
curl http://localhost:8001/donations/1

# Check if completed
{
  "id": 1,
  "status": "completed",
  "payment_intent_id": "mock_checkout_...",
  "amount": 100,
  "currency": "KES"
}
```

### Check Payout Status
```bash
# Get payout
curl http://localhost:8001/payouts/1

# Check if completed
{
  "id": 1,
  "status": "completed",
  "transaction_id": "QH1234567890",
  "amount": 50000,
  "currency": "KES"
}
```

### View Logs
```bash
# API logs
tail -f logs/trustvoice_api.log

# Watch for webhook callbacks
grep "M-Pesa" logs/trustvoice_api.log

# ngrok requests
curl http://localhost:4040/api/requests/http
```

---

## 🚨 Troubleshooting

### "Insufficient funds" error
Campaign must have raised >= payout amount. Check:
```bash
curl http://localhost:8001/campaigns/1
```

### Webhook not received
1. Check ngrok is running: http://localhost:4040
2. Verify callback URL in `.env` uses ngrok URL
3. Check ngrok dashboard for incoming requests
4. M-Pesa sandbox may have delays (up to 1 minute)

### "ConversationID not found"
Payout webhook arrived before payout was saved. This is normal - webhook will still update status.

---

## 📝 Next Steps

1. ✅ Test both donation and payout flows
2. ⏳ Add email notifications for completed payouts
3. ⏳ Add bulk payout feature (pay multiple NGOs at once)
4. ⏳ Add payout approval workflow (require admin approval)
5. ⏳ Add reconciliation reports (donations vs payouts)
6. ⏳ Add payout retry logic for failed payments

---

## 🎯 Production Checklist

Before going live:
- [ ] Get production M-Pesa credentials
- [ ] Deploy to cloud with static IP/domain
- [ ] Update webhook URLs to production URLs
- [ ] Enable webhook signature verification
- [ ] Set up monitoring/alerts for failed payouts
- [ ] Add payout approval process
- [ ] Test with real phone numbers
- [ ] Set up daily reconciliation reports

---

## 📚 Resources

- [M-Pesa API Docs](https://developer.safaricom.co.ke/docs)
- [Lipa Na M-Pesa Online](https://developer.safaricom.co.ke/APIs/MpesaExpressSimulate)
- [B2C API](https://developer.safaricom.co.ke/APIs/BusinessToCustomer)
- [Sandbox Test Credentials](https://developer.safaricom.co.ke/test_credentials)
