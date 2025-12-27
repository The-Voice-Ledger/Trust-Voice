"""
M-Pesa Payment Integration Service

Handles M-Pesa STK Push (Lipa Na M-Pesa Online) payments.
This is a stub/mock implementation that can be replaced with
actual Safaricom Daraja API calls when credentials are available.

M-Pesa Flow:
1. Initiate STK Push (send payment prompt to phone)
2. Customer enters PIN on their phone
3. Receive callback with payment status
4. Update donation record
"""

import os
import requests
import base64
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class MPesaService:
    """M-Pesa payment service."""
    
    def __init__(self):
        """Initialize M-Pesa service with credentials from environment."""
        self.consumer_key = os.getenv('MPESA_CONSUMER_KEY', 'mock_key')
        self.consumer_secret = os.getenv('MPESA_CONSUMER_SECRET', 'mock_secret')
        self.business_short_code = os.getenv('MPESA_SHORTCODE', '174379')
        self.passkey = os.getenv('MPESA_PASSKEY', 'mock_passkey')
        self.callback_url = os.getenv('MPESA_CALLBACK_URL', 'http://localhost:8001/webhooks/mpesa')
        
        # B2C (Business to Customer - Payouts)
        self.initiator_name = os.getenv('MPESA_INITIATOR_NAME', 'testapi')
        self.initiator_password = os.getenv('MPESA_INITIATOR_PASSWORD', '')
        self.b2c_queue_timeout_url = os.getenv('MPESA_B2C_QUEUE_TIMEOUT_URL', 'http://localhost:8001/webhooks/mpesa/b2c/timeout')
        self.b2c_result_url = os.getenv('MPESA_B2C_RESULT_URL', 'http://localhost:8001/webhooks/mpesa/b2c/result')
        
        # Sandbox vs Production
        self.environment = os.getenv('MPESA_ENVIRONMENT', 'sandbox')
        
        if self.environment == 'production':
            self.base_url = 'https://api.safaricom.co.ke'
        else:
            self.base_url = 'https://sandbox.safaricom.co.ke'
        
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
    
    def get_access_token(self) -> str:
        """
        Get OAuth access token from M-Pesa API.
        
        In mock mode, returns a fake token.
        In real mode, makes API call to get actual token.
        """
        # Mock mode (no real credentials)
        if self.consumer_key == 'mock_key':
            logger.info("M-Pesa: Using mock access token")
            return "mock_access_token_12345"
        
        # Real API call
        try:
            auth_url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
            
            # Create basic auth header
            credentials = f"{self.consumer_key}:{self.consumer_secret}"
            encoded = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded}'
            }
            
            response = requests.get(auth_url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data['access_token']
            
            logger.info("M-Pesa: Access token obtained successfully")
            return self.access_token
            
        except Exception as e:
            logger.error(f"M-Pesa: Failed to get access token: {str(e)}")
            raise Exception(f"Failed to authenticate with M-Pesa: {str(e)}")
    
    def initiate_stk_push(
        self,
        phone_number: str,
        amount: float,
        account_reference: str,
        transaction_desc: str
    ) -> Dict:
        """
        Initiate STK Push (Lipa Na M-Pesa Online).
        
        Args:
            phone_number: Customer phone in format 254XXXXXXXXX
            amount: Amount to charge (integer, no decimals)
            account_reference: Reference for the transaction
            transaction_desc: Description shown to customer
        
        Returns:
            Dict with response data including CheckoutRequestID
        """
        # Normalize phone number (remove + and ensure 254 format)
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]
        
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        
        # Mock mode
        if self.consumer_key == 'mock_key':
            logger.info(f"M-Pesa Mock: STK Push to {phone_number} for KES {amount}")
            return {
                'MerchantRequestID': f'mock_merchant_{int(datetime.utcnow().timestamp())}',
                'CheckoutRequestID': f'mock_checkout_{int(datetime.utcnow().timestamp())}',
                'ResponseCode': '0',
                'ResponseDescription': 'Success. Request accepted for processing',
                'CustomerMessage': 'Success. Request accepted for processing'
            }
        
        # Real API call
        try:
            access_token = self.get_access_token()
            
            # Generate password (base64 of shortcode + passkey + timestamp)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password_str = f"{self.business_short_code}{self.passkey}{timestamp}"
            password = base64.b64encode(password_str.encode()).decode()
            
            stk_push_url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'BusinessShortCode': self.business_short_code,
                'Password': password,
                'Timestamp': timestamp,
                'TransactionType': 'CustomerPayBillOnline',
                'Amount': int(amount),  # M-Pesa expects integer
                'PartyA': phone_number,
                'PartyB': self.business_short_code,
                'PhoneNumber': phone_number,
                'CallBackURL': self.callback_url,
                'AccountReference': account_reference,
                'TransactionDesc': transaction_desc
            }
            
            response = requests.post(stk_push_url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"M-Pesa: STK Push initiated - {data.get('ResponseDescription')}")
            
            return data
            
        except Exception as e:
            logger.error(f"M-Pesa: STK Push failed: {str(e)}")
            raise Exception(f"Failed to initiate M-Pesa payment: {str(e)}")
    
    def query_transaction_status(self, checkout_request_id: str) -> Dict:
        """
        Query the status of an STK Push transaction.
        
        Args:
            checkout_request_id: The CheckoutRequestID from STK Push response
        
        Returns:
            Dict with transaction status
        """
        # Mock mode
        if self.consumer_key == 'mock_key':
            logger.info(f"M-Pesa Mock: Query status for {checkout_request_id}")
            return {
                'ResponseCode': '0',
                'ResponseDescription': 'The service request has been accepted successfully',
                'ResultCode': '0',
                'ResultDesc': 'The service request is processed successfully.'
            }
        
        # Real API call
        try:
            access_token = self.get_access_token()
            
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password_str = f"{self.business_short_code}{self.passkey}{timestamp}"
            password = base64.b64encode(password_str.encode()).decode()
            
            query_url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'BusinessShortCode': self.business_short_code,
                'Password': password,
                'Timestamp': timestamp,
                'CheckoutRequestID': checkout_request_id
            }
            
            response = requests.post(query_url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"M-Pesa: Query result - {data.get('ResultDesc')}")
            
            return data
            
        except Exception as e:
            logger.error(f"M-Pesa: Query failed: {str(e)}")
            raise Exception(f"Failed to query M-Pesa transaction: {str(e)}")
    
    def b2c_payment(
        self,
        phone_number: str,
        amount: float,
        remarks: str,
        occasion: str = "Payout"
    ) -> Dict:
        """
        Send money to customer (B2C - Business to Customer).
        
        Use cases:
        - Disburse campaign funds to NGO
        - Refund donor
        - Pay beneficiaries
        
        Args:
            phone_number: Recipient phone in format 254XXXXXXXXX
            amount: Amount to send (integer, no decimals)
            remarks: Transaction description (shown to recipient)
            occasion: Category (e.g., "Payout", "Refund", "Salary")
        
        Returns:
            Dict with response data including ConversationID, OriginatorConversationID
        
        M-Pesa B2C Flow:
        1. Call B2C API with recipient details
        2. M-Pesa returns ConversationID immediately
        3. M-Pesa processes payment asynchronously
        4. M-Pesa sends result to ResultURL webhook
        5. Update payout status based on webhook
        """
        # Normalize phone number
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        
        # Mock mode
        if self.consumer_key == 'mock_key':
            logger.info(f"M-Pesa Mock: B2C payout to {phone_number} for KES {amount}")
            return {
                'ConversationID': f'mock_conv_{int(datetime.utcnow().timestamp())}',
                'OriginatorConversationID': f'mock_orig_{int(datetime.utcnow().timestamp())}',
                'ResponseCode': '0',
                'ResponseDescription': 'Accept the service request successfully.'
            }
        
        # Real API call
        try:
            access_token = self.get_access_token()
            
            b2c_url = f"{self.base_url}/mpesa/b2c/v1/paymentrequest"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'InitiatorName': self.initiator_name,
                'SecurityCredential': self.initiator_password,
                'CommandID': 'BusinessPayment',  # Or 'SalaryPayment', 'PromotionPayment'
                'Amount': int(amount),
                'PartyA': self.business_short_code,
                'PartyB': phone_number,
                'Remarks': remarks,
                'QueueTimeOutURL': self.b2c_queue_timeout_url,
                'ResultURL': self.b2c_result_url,
                'Occasion': occasion
            }
            
            response = requests.post(b2c_url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"M-Pesa: B2C initiated - {data.get('ResponseDescription')}")
            
            return data
            
        except Exception as e:
            logger.error(f"M-Pesa: B2C failed: {str(e)}")
            raise Exception(f"Failed to initiate M-Pesa B2C: {str(e)}")


# Singleton instance
mpesa_service = MPesaService()


# ==============================================================================
# Convenience Functions for Lab 5 Handlers
# ==============================================================================

def mpesa_stk_push(
    phone_number: str,
    amount: float,
    account_reference: str,
    transaction_desc: str
) -> Dict:
    """
    Convenience wrapper for STK Push (used by donation_handler).
    
    Returns:
        {
            "success": bool,
            "CheckoutRequestID": str,
            "error": str (if failed)
        }
    """
    try:
        result = mpesa_service.initiate_stk_push(
            phone_number=phone_number,
            amount=amount,
            account_reference=account_reference,
            transaction_desc=transaction_desc
        )
        
        # Check if successful
        if result.get('ResponseCode') == '0':
            return {
                "success": True,
                **result
            }
        else:
            return {
                "success": False,
                "error": result.get('ResponseDescription', 'STK Push failed')
            }
            
    except Exception as e:
        logger.error(f"STK Push wrapper error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def mpesa_b2c_payout(
    phone_number: str,
    amount: float,
    occasion: str,
    remarks: str
) -> Dict:
    """
    Convenience wrapper for B2C payout (used by payout_handler and impact_handler).
    
    Returns:
        {
            "success": bool,
            "ConversationID": str,
            "error": str (if failed)
        }
    """
    try:
        result = mpesa_service.b2c_payment(
            phone_number=phone_number,
            amount=amount,
            remarks=remarks,
            occasion=occasion
        )
        
        # Check if successful
        if result.get('ResponseCode') == '0':
            return {
                "success": True,
                **result
            }
        else:
            return {
                "success": False,
                "error": result.get('ResponseDescription', 'B2C payment failed')
            }
            
    except Exception as e:
        logger.error(f"B2C payout wrapper error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
