"""
Voice Command Handlers

Lab 6 handlers for voice command execution:
- Donor handlers: Search, donate, history, updates, impact
- NGO handlers: Create campaign, withdraw, field report, dashboard
- General handlers: Help, greeting, language, unknown

Lab 5 handlers (payment processing):
- donation_handler: M-Pesa/Stripe payment initiation
- payout_handler: Campaign fund withdrawals
- impact_handler: Field agent verifications
- verification_handler: Campaign approval process

All Lab 6 handlers are registered with @register_handler decorator
and called by voice/command_router.py
"""

# Import Lab 6 handlers to register them
from voice.handlers import donor_handlers
from voice.handlers import ngo_handlers
from voice.handlers import general_handlers

# Lab 5 handlers are imported directly by Lab 6 handlers when needed

__all__ = [
    "donor_handlers",
    "ngo_handlers",
    "general_handlers"
]
