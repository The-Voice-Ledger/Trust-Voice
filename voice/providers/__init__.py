"""
Voice Providers Module
Provides abstraction for different voice service providers (AddisAI, OpenAI)
"""

from .addis_ai import AddisAIProvider

__all__ = ["AddisAIProvider"]
