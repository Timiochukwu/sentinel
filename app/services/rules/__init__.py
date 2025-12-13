"""
Fraud detection rules organized by vertical

This package contains fraud detection rules organized by industry vertical:
- base.py: Base FraudRule class and RulesEngine
- lending.py: Lending-specific rules
- fintech.py: Fintech/payments rules
- ecommerce.py: E-commerce rules
- crypto.py: Cryptocurrency rules
- betting.py: Betting/gambling rules
- gaming.py: Gaming rules
- marketplace.py: Marketplace/P2P rules
- universal.py: Rules that apply to all verticals
- identity.py: Identity verification rules
- device.py: Device fingerprinting rules
- network.py: Network/IP rules
- behavioral.py: Behavioral biometrics rules
- ato.py: Account takeover rules
"""

from .base import FraudRule, FraudRulesEngine

# Import all rule lists when fully migrated
# from .lending import LENDING_RULES
# from .fintech import FINTECH_RULES
# etc.

__all__ = [
    'FraudRule',
    'FraudRulesEngine',
]
