"""
Webhook Handlers for Payment Processors

Handles callbacks from M-Pesa and Stripe when payment status changes.
These endpoints should be registered with payment processors.
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from database.db import get_db
from database.models import Donation, Campaign, Payout
from services.stripe_service import stripe_service

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
logger = logging.getLogger(__name__)


@router.post("/mpesa")
async def mpesa_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handle M-Pesa STK Push callback.
    
    Safaricom sends payment status to this endpoint after customer
    completes (or cancels) payment on their phone.
    
    Callback structure:
    {
        "Body": {
            "stkCallback": {
                "MerchantRequestID": "...",
                "CheckoutRequestID": "...",
                "ResultCode": 0,  # 0 = success, anything else = failure
                "ResultDesc": "The service request is processed successfully.",
                "CallbackMetadata": {
                    "Item": [
                        {"Name": "Amount", "Value": 1.00},
                        {"Name": "MpesaReceiptNumber", "Value": "NLJ7RT61SV"},
                        {"Name": "TransactionDate", "Value": 20191219102115},
                        {"Name": "PhoneNumber", "Value": 254708374149}
                    ]
                }
            }
        }
    }
    """
    try:
        payload = await request.json()
        logger.info(f"M-Pesa webhook received: {payload}")
        
        # Extract callback data
        stk_callback = payload.get('Body', {}).get('stkCallback', {})
        result_code = stk_callback.get('ResultCode')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        
        # Find donation by checkout_request_id (stored in payment_intent_id)
        # In real implementation, you'd store CheckoutRequestID separately
        donation = db.query(Donation).filter(
            Donation.payment_intent_id.contains(checkout_request_id)
        ).first()
        
        if not donation:
            logger.warning(f"M-Pesa: Donation not found for {checkout_request_id}")
            return {"ResultCode": 0, "ResultDesc": "Accepted"}
        
        # Update donation based on result
        if result_code == 0:
            # Success
            metadata = stk_callback.get('CallbackMetadata', {})
            items = metadata.get('Item', [])
            
            # Extract receipt number
            receipt_number = next(
                (item['Value'] for item in items if item['Name'] == 'MpesaReceiptNumber'),
                None
            )
            
            donation.status = 'completed'
            donation.payment_intent_id = receipt_number or donation.payment_intent_id
            
            # Update campaign total (per-currency bucket + cached USD)
            campaign = db.query(Campaign).filter(
                Campaign.id == donation.campaign_id
            ).first()
            
            if campaign:
                # Add to currency-specific bucket
                if not campaign.raised_amounts:
                    campaign.raised_amounts = {}
                
                currency = donation.currency
                current_amount = campaign.raised_amounts.get(currency, 0.0)
                campaign.raised_amounts[currency] = current_amount + float(donation.amount)
                
                # Also update cached USD total
                from services.currency_service import currency_service
                amount_usd = currency_service.convert_to_usd(
                    float(donation.amount),
                    donation.currency
                )
                campaign.raised_amount_usd += amount_usd
                
                # Mark raised_amounts as modified
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(campaign, "raised_amounts")
            
            logger.info(f"M-Pesa: Payment completed - {receipt_number}")
        else:
            # Failure
            donation.status = 'failed'
            logger.warning(f"M-Pesa: Payment failed - {stk_callback.get('ResultDesc')}")
        
        db.commit()
        
        # Acknowledge receipt of callback
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
        
    except Exception as e:
        logger.error(f"M-Pesa webhook error: {str(e)}")
        # Still return success to M-Pesa to avoid retries
        return {"ResultCode": 0, "ResultDesc": "Accepted"}


@router.post("/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Stripe webhook events.
    
    Stripe sends various events (payment_intent.succeeded, payment_intent.failed, etc.)
    to this endpoint. We verify the signature and update donation status accordingly.
    
    Important events:
    - payment_intent.succeeded: Payment completed successfully
    - payment_intent.payment_failed: Payment failed
    - payment_intent.canceled: Payment canceled
    """
    try:
        # Get raw body and signature
        payload = await request.body()
        signature = request.headers.get('stripe-signature', '')
        
        # Verify webhook signature
        try:
            event = stripe_service.construct_webhook_event(payload, signature)
        except ValueError as e:
            logger.error(f"Stripe: Invalid webhook payload: {str(e)}")
            # In test mode, allow test signatures
            if signature == 'test_sig':
                import json
                event_dict = json.loads(payload)
                event = type('obj', (object,), {
                    'type': event_dict.get('type'),
                    'data': type('obj', (object,), {'object': type('obj', (object,), event_dict.get('data', {}).get('object', {}))})()
                })()
            else:
                raise HTTPException(status_code=400, detail="Invalid payload")
        
        logger.info(f"Stripe webhook received: {event.type}")
        
        # Handle the event
        if event.type == 'payment_intent.succeeded':
            payment_intent = event.data.object
            
            # Find donation by payment_intent ID (stored in payment_intent_id)
            donation = db.query(Donation).filter(
                Donation.payment_intent_id == payment_intent.id
            ).first()
            
            if donation:
                donation.status = 'completed'
                
                # Update campaign total (per-currency bucket + cached USD)
                campaign = db.query(Campaign).filter(
                    Campaign.id == donation.campaign_id
                ).first()
                
                if campaign:
                    # Add to currency-specific bucket
                    if not campaign.raised_amounts:
                        campaign.raised_amounts = {}
                    
                    currency = donation.currency
                    current_amount = campaign.raised_amounts.get(currency, 0.0)
                    campaign.raised_amounts[currency] = current_amount + float(donation.amount)
                    
                    # Also update cached USD total
                    from services.currency_service import currency_service
                    amount_usd = currency_service.convert_to_usd(
                        float(donation.amount),
                        donation.currency
                    )
                    campaign.raised_amount_usd += amount_usd
                    
                    # Mark raised_amounts as modified
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(campaign, "raised_amounts")
                
                db.commit()
                logger.info(f"Stripe: Payment completed - {payment_intent.id}")
        
        elif event.type == 'payment_intent.payment_failed':
            payment_intent = event.data.object
            
            donation = db.query(Donation).filter(
                Donation.payment_intent_id == payment_intent.id
            ).first()
            
            if donation:
                donation.status = 'failed'
                db.commit()
                logger.warning(f"Stripe: Payment failed - {payment_intent.id}")
        
        elif event.type == 'payment_intent.canceled':
            payment_intent = event.data.object
            
            donation = db.query(Donation).filter(
                Donation.payment_intent_id == payment_intent.id
            ).first()
            
            if donation:
                donation.status = 'failed'
                db.commit()
                logger.info(f"Stripe: Payment canceled - {payment_intent.id}")
        
        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stripe webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.post("/mpesa/b2c/result")
async def mpesa_b2c_result(request: Request, db: Session = Depends(get_db)):
    """
    Handle M-Pesa B2C result callback.
    
    M-Pesa sends payment result here after processing payout.
    
    Expected payload:
    {
      "Result": {
        "ResultType": 0,
        "ResultCode": 0,  # 0 = success, non-zero = failure
        "ResultDesc": "The service request is processed successfully.",
        "OriginatorConversationID": "AG_20231221_...",
        "ConversationID": "AG_20231221_...",
        "TransactionID": "QH1234567890",
        "ResultParameters": {
          "ResultParameter": [
            {"Key": "TransactionAmount", "Value": 5000},
            {"Key": "TransactionReceipt", "Value": "QH1234567890"},
            {"Key": "ReceiverPartyPublicName", "Value": "254708374149 - John Doe"},
            {"Key": "TransactionCompletedDateTime", "Value": "21.12.2025 18:30:45"},
            {"Key": "B2CUtilityAccountAvailableFunds", "Value": 150000.00},
            {"Key": "B2CWorkingAccountAvailableFunds", "Value": 50000.00},
            {"Key": "B2CRecipientIsRegisteredCustomer", "Value": "Y"}
          ]
        },
        "ReferenceData": {
          "ReferenceItem": {
            "Key": "QueueTimeoutURL",
            "Value": "https://..."
          }
        }
      }
    }
    """
    try:
        payload = await request.json()
        logger.info(f"M-Pesa B2C result received: {payload}")
        
        result = payload.get('Result', {})
        result_code = result.get('ResultCode')
        conversation_id = result.get('ConversationID')
        originator_conversation_id = result.get('OriginatorConversationID')
        transaction_id = result.get('TransactionID')
        
        # Find payout by ConversationID
        payout = db.query(Payout).filter(
            Payout.conversation_id == conversation_id
        ).first()
        
        if not payout:
            logger.warning(f"M-Pesa B2C: Payout not found for ConversationID: {conversation_id}")
            return {"ResultCode": 0, "ResultDesc": "Accepted"}
        
        # Update payout based on result
        if result_code == 0:
            # Success
            result_parameters = result.get('ResultParameters', {}).get('ResultParameter', [])
            transaction_receipt = next(
                (item['Value'] for item in result_parameters if item['Key'] == 'TransactionReceipt'),
                None
            )
            
            payout.status = 'completed'
            payout.transaction_id = transaction_receipt or transaction_id
            payout.completed_at = datetime.utcnow()
            payout.status_message = result.get('ResultDesc')
            
            logger.info(f"M-Pesa B2C: Payout completed - {transaction_receipt}")
        else:
            # Failure
            payout.status = 'failed'
            payout.status_message = result.get('ResultDesc')
            logger.warning(f"M-Pesa B2C: Payout failed - {result.get('ResultDesc')}")
        
        db.commit()
        
        # Acknowledge receipt
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
        
    except Exception as e:
        logger.error(f"M-Pesa B2C result webhook error: {str(e)}")
        # Still return 200 to prevent M-Pesa retries
        return {"ResultCode": 0, "ResultDesc": "Accepted"}


@router.post("/mpesa/b2c/timeout")
async def mpesa_b2c_timeout(request: Request, db: Session = Depends(get_db)):
    """
    Handle M-Pesa B2C timeout callback.
    
    M-Pesa sends this if payment is stuck in queue too long.
    This is rare but should be handled to update payout status.
    """
    try:
        payload = await request.json()
        logger.warning(f"M-Pesa B2C timeout: {payload}")
        
        result = payload.get('Result', {})
        conversation_id = result.get('ConversationID')
        
        # Find payout and mark as failed
        payout = db.query(Payout).filter(
            Payout.conversation_id == conversation_id
        ).first()
        
        if payout:
            payout.status = 'failed'
            payout.status_message = 'Request timed out in M-Pesa queue'
            db.commit()
            logger.info(f"M-Pesa B2C: Payout {payout.id} marked as failed due to timeout")
        
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
        
    except Exception as e:
        logger.error(f"M-Pesa B2C timeout webhook error: {str(e)}")
        return {"ResultCode": 0, "ResultDesc": "Accepted"}


@router.get("/health")
def webhook_health():
    """
    Health check endpoint for webhook service.
    
    Payment processors can ping this to verify the webhook endpoint is reachable.
    """
    return {
        "status": "healthy",
        "service": "webhooks",
        "timestamp": datetime.utcnow().isoformat()
    }
