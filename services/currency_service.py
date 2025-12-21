"""
Currency Conversion Service

Provides real-time and cached currency conversion rates.
Uses exchangerate-api.io (free tier: 1,500 requests/month).

Features:
- Fetch live exchange rates
- Cache rates for 24 hours to reduce API calls
- Convert between any supported currencies
- Fallback to static rates if API unavailable
"""

import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class CurrencyService:
    """
    Currency conversion service with caching.
    
    Usage:
        service = CurrencyService()
        usd_amount = service.convert(100.00, "KES", "USD")  # 100 KES to USD
        eur_amount = service.convert(50.00, "USD", "EUR")   # 50 USD to EUR
    """
    
    # frankfurter.app - Free, no API key needed, maintained by European Central Bank
    # Supports 30+ currencies, no rate limits for reasonable use
    BASE_URL = "https://api.frankfurter.app/latest?from={}"
    
    # Fallback static rates (updated monthly, USD base)
    # These are approximate rates as of Dec 2025
    FALLBACK_RATES = {
        "USD": 1.0,       # US Dollar
        "EUR": 0.88,      # Euro
        "GBP": 0.75,      # British Pound
        "JPY": 110.0,     # Japanese Yen
        "CHF": 0.92,      # Swiss Franc
        "CAD": 1.35,      # Canadian Dollar
        "AUD": 1.45,      # Australian Dollar
        "CNY": 6.45,      # Chinese Yuan
        "SEK": 10.5,      # Swedish Krona
        "NOK": 10.8,      # Norwegian Krone
        "DKK": 6.55,      # Danish Krone
        "NZD": 1.58,      # New Zealand Dollar
        "SGD": 1.35,      # Singapore Dollar
        "HKD": 7.80,      # Hong Kong Dollar
        "KES": 129.0,     # Kenyan Shilling
        "TZS": 2350.0,    # Tanzanian Shilling
        "UGX": 3700.0,    # Ugandan Shilling
        "ZAR": 18.5,      # South African Rand
    }
    
    def __init__(self):
        self.cache: Dict[str, dict] = {}  # {currency: {rates: {...}, expires: datetime}}
        self.cache_duration = timedelta(hours=24)  # Cache for 24 hours
        self.api_key = os.getenv("EXCHANGE_RATE_API_KEY")  # Optional
    
    def get_rates(self, base_currency: str = "USD") -> Dict[str, float]:
        """
        Get exchange rates for a base currency.
        
        Args:
            base_currency: Currency to get rates for (e.g., "USD", "EUR")
        
        Returns:
            Dictionary of {currency_code: rate}
        """
        base_currency = base_currency.upper()
        
        # Check cache first
        if base_currency in self.cache:
            cached = self.cache[base_currency]
            if datetime.utcnow() < cached["expires"]:
                logger.debug(f"Using cached rates for {base_currency}")
                return cached["rates"]
        
        # Fetch from API
        try:
            url = self.BASE_URL.format(base_currency)
            logger.info(f"Fetching exchange rates for {base_currency} from API")
            
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # frankfurter.app response format
            if "rates" in data:
                rates = data.get("rates", {})
                # Add base currency to rates (always 1.0)
                rates[base_currency] = 1.0
                
                # Cache the rates
                self.cache[base_currency] = {
                    "rates": rates,
                    "expires": datetime.utcnow() + self.cache_duration
                }
                
                logger.info(f"Successfully fetched {len(rates)} exchange rates for {base_currency}")
                return rates
            else:
                logger.warning(f"API returned unexpected format: {data}")
                return self._get_fallback_rates(base_currency)
        
        except requests.RequestException as e:
            logger.error(f"Failed to fetch exchange rates: {e}")
            return self._get_fallback_rates(base_currency)
        except Exception as e:
            logger.error(f"Unexpected error fetching rates: {e}")
            return self._get_fallback_rates(base_currency)
    
    def _get_fallback_rates(self, base_currency: str) -> Dict[str, float]:
        """
        Get static fallback rates when API is unavailable.
        
        Converts FALLBACK_RATES (USD-based) to requested base currency.
        """
        base_currency = base_currency.upper()
        
        if base_currency not in self.FALLBACK_RATES:
            logger.warning(f"Unknown currency {base_currency}, using USD rates")
            return self.FALLBACK_RATES
        
        base_rate = self.FALLBACK_RATES[base_currency]
        
        # Convert all rates to the requested base currency
        converted_rates = {}
        for currency, rate in self.FALLBACK_RATES.items():
            converted_rates[currency] = rate / base_rate
        
        logger.info(f"Using fallback rates for {base_currency}")
        return converted_rates
    
    def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str
    ) -> float:
        """
        Convert amount from one currency to another.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code (e.g., "KES")
            to_currency: Target currency code (e.g., "USD")
        
        Returns:
            Converted amount
        
        Example:
            >>> service.convert(5000, "KES", "USD")
            44.05  # 5000 KES = ~44 USD
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # No conversion needed
        if from_currency == to_currency:
            return amount
        
        # Get rates with from_currency as base
        rates = self.get_rates(from_currency)
        
        if to_currency not in rates:
            logger.error(f"Currency {to_currency} not found in rates")
            # Try fallback
            rates = self._get_fallback_rates(from_currency)
            
            if to_currency not in rates:
                logger.error(f"Cannot convert {from_currency} to {to_currency}")
                # Return original amount as last resort
                return amount
        
        conversion_rate = rates[to_currency]
        converted_amount = amount * conversion_rate
        
        logger.debug(
            f"Converted {amount} {from_currency} to "
            f"{converted_amount:.2f} {to_currency} (rate: {conversion_rate})"
        )
        
        return converted_amount
    
    def convert_to_usd(self, amount: float, from_currency: str) -> float:
        """
        Convenience method to convert any currency to USD.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
        
        Returns:
            Amount in USD
        """
        return self.convert(amount, from_currency, "USD")


# Singleton instance
currency_service = CurrencyService()
