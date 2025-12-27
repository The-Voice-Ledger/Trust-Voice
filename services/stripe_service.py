"""
Stripe Payment Integration Service

Handles credit/debit card payments via Stripe.
Supports payment intents, customer management, and webhooks.

Stripe Flow:
1. Create PaymentIntent with amount and currency
2. Client confirms payment on frontend (using stripe.js)
3. Stripe sends webhook with payment status
4. Update donation record
"""

import os
import stripe
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class StripeService:
    """Stripe payment service."""
    
    def __init__(self):
        """Initialize Stripe service with API key from environment."""
        self.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_mock_key')
        self.publishable_key = os.getenv('STRIPE_PUBLISHABLE_KEY', 'pk_test_mock_key')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', 'whsec_mock_secret')
        
        # Set Stripe API key
        stripe.api_key = self.api_key
        
        # Mock mode flag
        self.is_mock = self.api_key.startswith('sk_test_mock')
        
        if self.is_mock:
            logger.info("Stripe: Running in mock mode (no real API key)")
        else:
            logger.info("Stripe: Initialized with real API key")
    
    def create_payment_intent(
        self,
        amount: float,
        currency: str,
        customer_email: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Create a Stripe PaymentIntent.
        
        Args:
            amount: Amount in currency units (e.g., 10.00 for $10)
            currency: Three-letter currency code (USD, EUR, KES, etc.)
            customer_email: Optional customer email
            metadata: Optional metadata to attach to payment
        
        Returns:
            Dict with PaymentIntent data including client_secret
        """
        # Convert amount to cents/smallest currency unit
        amount_cents = int(amount * 100)
        
        # Mock mode
        if self.is_mock:
            logger.info(f"Stripe Mock: Creating PaymentIntent for {amount} {currency}")
            return {
                'id': f'pi_mock_{int(os.urandom(4).hex(), 16)}',
                'object': 'payment_intent',
                'amount': amount_cents,
                'currency': currency.lower(),
                'status': 'requires_payment_method',
                'client_secret': f'pi_mock_secret_{int(os.urandom(4).hex(), 16)}',
                'metadata': metadata or {}
            }
        
        # Real API call
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                receipt_email=customer_email,
                metadata=metadata or {},
                automatic_payment_methods={'enabled': True}
            )
            
            logger.info(f"Stripe: PaymentIntent created - {payment_intent.id}")
            
            return {
                'id': payment_intent.id,
                'object': payment_intent.object,
                'amount': payment_intent.amount,
                'currency': payment_intent.currency,
                'status': payment_intent.status,
                'client_secret': payment_intent.client_secret,
                'metadata': payment_intent.metadata
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe: PaymentIntent creation failed: {str(e)}")
            raise Exception(f"Failed to create Stripe payment: {str(e)}")
    
    def retrieve_payment_intent(self, payment_intent_id: str) -> Dict:
        """
        Retrieve a PaymentIntent by ID.
        
        Args:
            payment_intent_id: The PaymentIntent ID
        
        Returns:
            Dict with PaymentIntent data
        """
        # Mock mode
        if self.is_mock:
            logger.info(f"Stripe Mock: Retrieving PaymentIntent {payment_intent_id}")
            return {
                'id': payment_intent_id,
                'object': 'payment_intent',
                'status': 'succeeded',
                'amount': 1000,
                'currency': 'usd'
            }
        
        # Real API call
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                'id': payment_intent.id,
                'object': payment_intent.object,
                'status': payment_intent.status,
                'amount': payment_intent.amount,
                'currency': payment_intent.currency,
                'metadata': payment_intent.metadata
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe: Retrieval failed: {str(e)}")
            raise Exception(f"Failed to retrieve Stripe payment: {str(e)}")
    
    def confirm_payment_intent(
        self,
        payment_intent_id: str,
        payment_method: str
    ) -> Dict:
        """
        Confirm a PaymentIntent (used for server-side confirmation).
        
        Note: In typical Stripe integration, confirmation happens
        client-side using stripe.js. This method is for special cases.
        
        Args:
            payment_intent_id: The PaymentIntent ID
            payment_method: The PaymentMethod ID
        
        Returns:
            Dict with confirmed PaymentIntent data
        """
        # Mock mode
        if self.is_mock:
            logger.info(f"Stripe Mock: Confirming PaymentIntent {payment_intent_id}")
            return {
                'id': payment_intent_id,
                'status': 'succeeded',
                'amount': 1000,
                'currency': 'usd'
            }
        
        # Real API call
        try:
            payment_intent = stripe.PaymentIntent.confirm(
                payment_intent_id,
                payment_method=payment_method
            )
            
            logger.info(f"Stripe: PaymentIntent confirmed - {payment_intent.id}")
            
            return {
                'id': payment_intent.id,
                'status': payment_intent.status,
                'amount': payment_intent.amount,
                'currency': payment_intent.currency
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe: Confirmation failed: {str(e)}")
            raise Exception(f"Failed to confirm Stripe payment: {str(e)}")
    
    def create_payout(
        self,
        amount: float,
        currency: str,
        destination: str,
        description: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Create a Stripe Payout to send funds to bank account.
        
        Note: This requires Stripe Connect or manual bank account setup.
        For production, NGO must provide bank details and complete verification.
        
        Args:
            amount: Amount in currency units (e.g., 1000.00 for $1,000)
            currency: Three-letter currency code (USD, EUR, GBP, etc.)
            destination: Bank account ID or 'default' for NGO's default account
            description: Payout description
            metadata: Optional metadata
        
        Returns:
            Dict with Payout data including payout ID
        """
        amount_cents = int(amount * 100)
        
        # Mock mode
        if self.is_mock:
            logger.info(f"Stripe Mock: Creating payout for {amount} {currency}")
            return {
                'id': f'po_mock_{int(os.urandom(4).hex(), 16)}',
                'object': 'payout',
                'amount': amount_cents,
                'currency': currency.lower(),
                'status': 'pending',
                'arrival_date': 1735689600,  # Unix timestamp
                'description': description,
                'metadata': metadata or {}
            }
        
        # Real API call
        try:
            payout = stripe.Payout.create(
                amount=amount_cents,
                currency=currency.lower(),
                destination=destination if destination != 'default' else None,
                description=description,
                metadata=metadata or {}
            )
            
            logger.info(f"Stripe: Payout created - {payout.id}")
            
            return {
                'id': payout.id,
                'object': payout.object,
                'amount': payout.amount,
                'currency': payout.currency,
                'status': payout.status,
                'arrival_date': payout.arrival_date,
                'description': payout.description,
                'metadata': payout.metadata
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe: Payout creation failed: {str(e)}")
            raise Exception(f"Failed to create Stripe payout: {str(e)}")
    
    def create_transfer(
        self,
        amount: float,
        currency: str,
        destination: str,
        description: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Create a Stripe Transfer (for Connect accounts).
        
        Use this if NGO has a Stripe Connect account.
        Transfers are instant, while Payouts take 2-7 days.
        
        Args:
            amount: Amount in currency units
            currency: Three-letter currency code
            destination: Connected Stripe account ID (starts with 'acct_')
            description: Transfer description
            metadata: Optional metadata
        
        Returns:
            Dict with Transfer data
        """
        amount_cents = int(amount * 100)
        
        # Mock mode
        if self.is_mock:
            logger.info(f"Stripe Mock: Creating transfer for {amount} {currency}")
            return {
                'id': f'tr_mock_{int(os.urandom(4).hex(), 16)}',
                'object': 'transfer',
                'amount': amount_cents,
                'currency': currency.lower(),
                'destination': destination,
                'description': description,
                'metadata': metadata or {}
            }
        
        # Real API call
        try:
            transfer = stripe.Transfer.create(
                amount=amount_cents,
                currency=currency.lower(),
                destination=destination,
                description=description,
                metadata=metadata or {}
            )
            
            logger.info(f"Stripe: Transfer created - {transfer.id}")
            
            return {
                'id': transfer.id,
                'object': transfer.object,
                'amount': transfer.amount,
                'currency': transfer.currency,
                'destination': transfer.destination,
                'description': transfer.description,
                'metadata': transfer.metadata
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe: Transfer creation failed: {str(e)}")
            raise Exception(f"Failed to create Stripe transfer: {str(e)}")
    
    def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Create a Stripe Customer for recurring donors.
        
        Args:
            email: Customer email
            name: Customer name
            phone: Customer phone
            metadata: Optional metadata
        
        Returns:
            Dict with Customer data
        """
        # Mock mode
        if self.is_mock:
            logger.info(f"Stripe Mock: Creating customer for {email}")
            return {
                'id': f'cus_mock_{int(os.urandom(4).hex(), 16)}',
                'object': 'customer',
                'email': email,
                'name': name,
                'phone': phone
            }
        
        # Real API call
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                phone=phone,
                metadata=metadata or {}
            )
            
            logger.info(f"Stripe: Customer created - {customer.id}")
            
            return {
                'id': customer.id,
                'object': customer.object,
                'email': customer.email,
                'name': customer.name,
                'phone': customer.phone
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe: Customer creation failed: {str(e)}")
            raise Exception(f"Failed to create Stripe customer: {str(e)}")
    
    def construct_webhook_event(
        self,
        payload: bytes,
        signature: str
    ) -> stripe.Event:
        """
        Verify and construct webhook event from Stripe.
        
        Args:
            payload: Raw request body
            signature: Stripe-Signature header value
        
        Returns:
            Verified Stripe Event object
        
        Raises:
            ValueError: If signature verification fails
        """
        # Mock mode - skip verification
        if self.is_mock:
            logger.warning("Stripe Mock: Skipping webhook signature verification")
            # In mock mode, just parse the JSON
            import json
            return stripe.Event.construct_from(
                json.loads(payload),
                stripe.api_key
            )
        
        # Real verification
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                self.webhook_secret
            )
            
            logger.info(f"Stripe: Webhook event verified - {event.type}")
            return event
            
        except ValueError as e:
            logger.error(f"Stripe: Invalid webhook payload: {str(e)}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Stripe: Invalid webhook signature: {str(e)}")
            raise ValueError("Invalid signature")


# Singleton instance
stripe_service = StripeService()


# ============================================================================
# WRAPPER FUNCTIONS (for backwards compatibility with Lab 5 handlers)
# ============================================================================

def create_payment_intent(
    amount: float,
    currency: str,
    customer_email: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Wrapper function for Lab 5 donation_handler.py compatibility.
    Calls StripeService.create_payment_intent().
    """
    return stripe_service.create_payment_intent(
        amount=amount,
        currency=currency,
        customer_email=customer_email,
        metadata=metadata
    )
