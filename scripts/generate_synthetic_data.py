"""
Synthetic Nigerian Fraud Data Generator

This script generates realistic transaction data for testing Sentinel's fraud detection platform.
It creates transactions across all 5 industries with realistic fraud patterns.

Features:
- Generates Nigerian-specific data (BVN, phone numbers, IP addresses)
- Supports all 5 industries (fintech, ecommerce, betting, crypto, marketplace)
- Realistic fraud patterns (loan stacking, SIM swap, bonus abuse, etc.)
- Configurable fraud rate
- Outputs to CSV or JSON

Usage:
    python scripts/generate_synthetic_data.py --count 10000 --fraud-rate 0.10

Author: Sentinel Team
"""

import random
import json
import csv
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any
import hashlib


class NigerianDataGenerator:
    """Generate realistic Nigerian transaction data"""

    def __init__(self):
        """Initialize with Nigerian-specific data"""

        # Nigerian mobile operators and their prefixes
        self.phone_prefixes = {
            'MTN': ['0803', '0806', '0810', '0813', '0814', '0816', '0903', '0906'],
            'Airtel': ['0802', '0808', '0812', '0902', '0907', '0912'],
            'Glo': ['0805', '0807', '0811', '0815', '0905'],
            '9mobile': ['0809', '0817', '0818', '0909']
        }

        # Nigerian IP address ranges (major ISPs)
        self.ip_ranges = [
            '41.58',    # MTN
            '105.112',  # MTN
            '197.210',  # Airtel
            '105.113',  # Glo
            '105.117',  # Spectranet
            '102.89',   # Various ISPs
            '154.118',  # Various ISPs
        ]

        # VPN/Proxy IPs (for fraud patterns)
        self.vpn_ips = [
            '185.220.101.1',   # Known VPN
            '185.220.102.1',   # Known VPN
            '45.134.212.1',    # Known proxy
        ]

        # Nigerian cities
        self.cities = [
            'Lagos', 'Abuja', 'Port Harcourt', 'Kano', 'Ibadan',
            'Benin City', 'Kaduna', 'Enugu', 'Aba', 'Ilorin'
        ]

        # Common Nigerian names
        self.first_names = [
            'Chukwu', 'Adewale', 'Ibrahim', 'Chioma', 'Ngozi', 'Yusuf',
            'Oluwaseun', 'Amina', 'Tunde', 'Blessing', 'Mohammed', 'Grace'
        ]

        self.last_names = [
            'Okafor', 'Adeleke', 'Musa', 'Okonkwo', 'Bello', 'Eze',
            'Adeyemi', 'Hassan', 'Nwankwo', 'Abubakar', 'Ojo', 'Usman'
        ]

        # Email domains
        self.email_domains = [
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com'
        ]

        # Disposable email domains (fraud indicator)
        self.disposable_domains = [
            'tempmail.com', 'guerrillamail.com', '10minutemail.com',
            'throwaway.email', 'temp-mail.org'
        ]

        # Device types
        self.devices = [
            'Samsung Galaxy', 'iPhone', 'Tecno', 'Infinix', 'Xiaomi',
            'Huawei', 'OnePlus', 'Oppo', 'Nokia', 'Google Pixel'
        ]

        # Product categories (marketplace/ecommerce)
        self.product_categories = [
            'phones', 'electronics', 'fashion', 'home_appliances',
            'computers', 'gift_cards', 'luxury_goods', 'gadgets',
            'groceries', 'books'
        ]

        # High-risk categories (more fraud)
        self.high_risk_categories = [
            'phones', 'electronics', 'gift_cards', 'luxury_goods', 'gadgets'
        ]

    def generate_phone_number(self, is_fraud: bool = False) -> str:
        """
        Generate Nigerian phone number

        Returns:
            Phone number in format +234XXXXXXXXXX
        """
        # Pick random operator
        operator = random.choice(list(self.phone_prefixes.keys()))
        prefix = random.choice(self.phone_prefixes[operator])

        # Generate remaining 7 digits
        remaining = ''.join([str(random.randint(0, 9)) for _ in range(7)])

        # Convert 0XXX to +234XXX format
        return f"+234{prefix[1:]}{remaining}"

    def generate_bvn(self) -> str:
        """
        Generate BVN (Bank Verification Number)

        Returns:
            11-digit BVN
        """
        return ''.join([str(random.randint(0, 9)) for _ in range(11)])

    def generate_ip_address(self, is_fraud: bool = False) -> str:
        """
        Generate Nigerian IP address

        Args:
            is_fraud: If True, might return VPN/proxy IP

        Returns:
            IP address string
        """
        # 20% chance of VPN for fraud transactions
        if is_fraud and random.random() < 0.2:
            return random.choice(self.vpn_ips)

        # Regular Nigerian IP
        prefix = random.choice(self.ip_ranges)
        return f"{prefix}.{random.randint(1, 254)}.{random.randint(1, 254)}"

    def generate_email(self, user_id: str, is_fraud: bool = False) -> str:
        """
        Generate email address

        Args:
            user_id: User identifier
            is_fraud: If True, might use disposable email

        Returns:
            Email address
        """
        # 15% chance of disposable email for fraud
        if is_fraud and random.random() < 0.15:
            domain = random.choice(self.disposable_domains)
        else:
            domain = random.choice(self.email_domains)

        # Generate email username
        first = random.choice(self.first_names).lower()
        last = random.choice(self.last_names).lower()
        number = random.randint(1, 999)

        return f"{first}.{last}{number}@{domain}"

    def generate_device_id(self) -> str:
        """
        Generate device identifier

        Returns:
            Device ID string
        """
        device = random.choice(self.devices)
        device_id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
        return f"{device.lower().replace(' ', '_')}_{device_id}"

    def hash_pii(self, value: str) -> str:
        """
        Hash PII data (for privacy)

        Args:
            value: Value to hash

        Returns:
            SHA-256 hash
        """
        return hashlib.sha256(value.encode()).hexdigest()


class FraudTransactionGenerator:
    """Generate transactions with fraud patterns"""

    def __init__(self, data_gen: NigerianDataGenerator):
        self.data_gen = data_gen

    def generate_fintech_transaction(self, txn_id: int, is_fraud: bool) -> Dict[str, Any]:
        """Generate fintech/lending transaction"""

        user_id = f"user_{random.randint(1000, 99999)}"
        account_age = random.randint(1, 365) if not is_fraud else random.randint(1, 10)

        # Fraud patterns for fintech
        if is_fraud:
            fraud_pattern = random.choice([
                'loan_stacking',
                'sim_swap',
                'new_account_large',
                'first_transaction_max'
            ])

            if fraud_pattern == 'loan_stacking':
                # Loan stacking: applied to multiple lenders
                amount = random.randint(100000, 500000)
                account_age = random.randint(5, 30)
                transaction_count = random.randint(1, 3)
                phone_changed = False
                consortium_count = random.randint(3, 7)  # Applied to 3-7 lenders

            elif fraud_pattern == 'sim_swap':
                # SIM swap: phone changed + new device + withdrawal
                amount = random.randint(200000, 1000000)
                account_age = random.randint(30, 180)
                transaction_count = random.randint(5, 20)
                phone_changed = True  # Key indicator!
                consortium_count = 0

            elif fraud_pattern == 'new_account_large':
                # New account with large amount
                amount = random.randint(200000, 500000)
                account_age = random.randint(1, 5)
                transaction_count = 0
                phone_changed = False
                consortium_count = 0

            else:  # first_transaction_max
                # First transaction at maximum limit
                amount = 500000  # Max amount
                account_age = random.randint(1, 7)
                transaction_count = 0
                phone_changed = False
                consortium_count = 0

            # Fraud transactions often use round amounts
            amount = round(amount / 50000) * 50000

        else:
            # Legitimate transaction
            amount = random.randint(10000, 200000)
            transaction_count = random.randint(1, 50)
            phone_changed = False
            consortium_count = random.choice([0, 0, 0, 1])  # Mostly 0, sometimes 1

        return {
            'transaction_id': f'txn_{txn_id:06d}',
            'user_id': user_id,
            'amount': amount,
            'transaction_type': random.choice(['loan_disbursement', 'loan_repayment', 'transfer']),
            'industry': 'lending',

            # Device & Network
            'device_id': self.data_gen.generate_device_id(),
            'ip_address': self.data_gen.generate_ip_address(is_fraud),

            # Account info
            'account_age_days': account_age,
            'transaction_count': transaction_count,
            'is_first_transaction': transaction_count == 0,

            # Contact changes
            'phone_changed_recently': phone_changed,
            'email_changed_recently': False,

            # PII (hashed)
            'bvn_hash': self.data_gen.hash_pii(self.data_gen.generate_bvn()),
            'phone_hash': self.data_gen.hash_pii(self.data_gen.generate_phone_number(is_fraud)),
            'email': self.data_gen.generate_email(user_id, is_fraud),

            # Location
            'city': random.choice(self.data_gen.cities),
            'country': 'Nigeria',

            # Additional
            'dormant_days': 0,
            'previous_fraud_count': 1 if is_fraud and random.random() < 0.3 else 0,

            # Consortium data (for loan stacking)
            'consortium_client_count': consortium_count if is_fraud else random.choice([0, 0, 0, 1]),

            # Label
            'is_fraud': is_fraud,
            'created_at': datetime.now() - timedelta(days=random.randint(0, 30))
        }

    def generate_ecommerce_transaction(self, txn_id: int, is_fraud: bool) -> Dict[str, Any]:
        """Generate e-commerce transaction"""

        user_id = f"user_{random.randint(1000, 99999)}"
        amount = random.randint(5000, 150000) if not is_fraud else random.randint(50000, 300000)

        # Fraud patterns
        if is_fraud:
            fraud_type = random.choice(['card_testing', 'shipping_mismatch', 'digital_goods_fraud'])

            if fraud_type == 'card_testing':
                # Multiple failed payments
                failed_count = random.randint(3, 10)
                shipping_match = True
            elif fraud_type == 'shipping_mismatch':
                # Different shipping/billing
                failed_count = 0
                shipping_match = False
            else:  # digital_goods_fraud
                failed_count = 0
                shipping_match = True

            account_age = random.randint(1, 30)
        else:
            failed_count = 0
            shipping_match = random.choice([True, True, True, False])  # Mostly match
            account_age = random.randint(30, 365)

        return {
            'transaction_id': f'txn_{txn_id:06d}',
            'user_id': user_id,
            'amount': amount,
            'transaction_type': random.choice(['purchase', 'checkout']),
            'industry': 'ecommerce',
            'device_id': self.data_gen.generate_device_id(),
            'ip_address': self.data_gen.generate_ip_address(is_fraud),
            'account_age_days': account_age,
            'transaction_count': random.randint(0, 20),

            # E-commerce specific
            'card_bin': f"{random.randint(400000, 599999)}",
            'card_last4': f"{random.randint(1000, 9999)}",
            'card_type': random.choice(['debit', 'credit']),
            'payment_method': 'card',
            'shipping_address_matches_billing': shipping_match,
            'is_digital_goods': random.choice([True, False]),

            # Velocity
            'failed_payment_count_1hour': failed_count,

            'email': self.data_gen.generate_email(user_id, is_fraud),
            'city': random.choice(self.data_gen.cities),
            'is_fraud': is_fraud,
            'created_at': datetime.now() - timedelta(hours=random.randint(0, 720))
        }

    def generate_betting_transaction(self, txn_id: int, is_fraud: bool) -> Dict[str, Any]:
        """Generate betting/gaming transaction"""

        user_id = f"user_{random.randint(1000, 99999)}"
        amount = random.randint(5000, 100000)

        if is_fraud:
            fraud_type = random.choice(['bonus_abuse', 'withdrawal_without_wagering', 'excessive_withdrawals'])

            if fraud_type == 'bonus_abuse':
                # Multiple accounts same device
                device_account_count = random.randint(3, 8)
                wagering_ratio = random.uniform(0.5, 2.0)
                withdrawal_count = 0
            elif fraud_type == 'withdrawal_without_wagering':
                # Deposit + immediate withdrawal (money laundering)
                device_account_count = 1
                wagering_ratio = random.uniform(0.1, 0.4)  # Low wagering!
                withdrawal_count = random.randint(1, 3)
                amount = random.randint(100000, 500000)  # Large amount
            else:  # excessive_withdrawals
                device_account_count = 1
                wagering_ratio = random.uniform(0.6, 1.5)
                withdrawal_count = random.randint(5, 12)  # Many withdrawals!

            account_age = random.randint(1, 30)
        else:
            device_account_count = 1
            wagering_ratio = random.uniform(1.0, 5.0)  # Good wagering
            withdrawal_count = random.randint(0, 2)
            account_age = random.randint(30, 365)

        return {
            'transaction_id': f'txn_{txn_id:06d}',
            'user_id': user_id,
            'amount': amount,
            'transaction_type': random.choice(['bet_placement', 'bet_withdrawal', 'bonus_claim']),
            'industry': 'betting',
            'device_id': self.data_gen.generate_device_id(),
            'ip_address': self.data_gen.generate_ip_address(is_fraud),
            'account_age_days': account_age,
            'transaction_count': random.randint(5, 200),

            # Betting specific
            'bet_count_today': random.randint(0, 20),
            'bonus_balance': random.randint(0, 50000),
            'withdrawal_count_today': withdrawal_count,
            'wagering_ratio': wagering_ratio,

            # Device sharing (multi-accounting)
            'device_account_count': device_account_count,

            'email': self.data_gen.generate_email(user_id, is_fraud),
            'city': random.choice(self.data_gen.cities),
            'is_fraud': is_fraud,
            'created_at': datetime.now() - timedelta(hours=random.randint(0, 720))
        }

    def generate_crypto_transaction(self, txn_id: int, is_fraud: bool) -> Dict[str, Any]:
        """Generate crypto transaction"""

        user_id = f"user_{random.randint(1000, 99999)}"

        if is_fraud:
            fraud_type = random.choice(['new_wallet_high_value', 'p2p_velocity'])

            if fraud_type == 'new_wallet_high_value':
                amount = random.randint(500000, 2000000)  # Large amount
                is_new_wallet = True
                wallet_age = random.randint(1, 7)
                p2p_count = 0
            else:  # p2p_velocity
                amount = random.randint(50000, 300000)
                is_new_wallet = False
                wallet_age = random.randint(30, 180)
                p2p_count = random.randint(11, 25)  # High P2P volume!

            account_age = random.randint(1, 30)
        else:
            amount = random.randint(10000, 200000)
            is_new_wallet = random.choice([True, False])
            wallet_age = random.randint(1, 365) if not is_new_wallet else random.randint(1, 7)
            p2p_count = random.randint(0, 8)
            account_age = random.randint(30, 365)

        # Generate crypto wallet address
        wallet = '0x' + ''.join(random.choices('0123456789abcdef', k=40))

        return {
            'transaction_id': f'txn_{txn_id:06d}',
            'user_id': user_id,
            'amount': amount,
            'transaction_type': random.choice(['crypto_deposit', 'crypto_withdrawal', 'p2p_trade', 'swap']),
            'industry': 'crypto',
            'device_id': self.data_gen.generate_device_id(),
            'ip_address': self.data_gen.generate_ip_address(is_fraud),
            'account_age_days': account_age,
            'transaction_count': random.randint(1, 100),

            # Crypto specific
            'wallet_address': wallet if not is_fraud else wallet,  # Could blacklist fraud wallets
            'blockchain': random.choice(['bitcoin', 'ethereum', 'tron', 'binance_smart_chain']),
            'is_new_wallet': is_new_wallet,
            'wallet_age_days': wallet_age,
            'p2p_count_24h': p2p_count,

            'email': self.data_gen.generate_email(user_id, is_fraud),
            'city': random.choice(self.data_gen.cities),
            'is_fraud': is_fraud,
            'created_at': datetime.now() - timedelta(hours=random.randint(0, 720))
        }

    def generate_marketplace_transaction(self, txn_id: int, is_fraud: bool) -> Dict[str, Any]:
        """Generate marketplace transaction"""

        user_id = f"user_{random.randint(1000, 99999)}"
        seller_id = f"seller_{random.randint(1000, 9999)}"

        # Product category
        if is_fraud:
            category = random.choice(self.data_gen.high_risk_categories)
        else:
            category = random.choice(self.data_gen.product_categories)

        is_high_value = category in self.data_gen.high_risk_categories

        if is_fraud:
            fraud_type = random.choice(['new_seller_high_value', 'low_rated_seller'])

            if fraud_type == 'new_seller_high_value':
                seller_age = random.randint(1, 5)
                seller_rating = random.uniform(3.0, 4.5)
                amount = random.randint(100000, 500000)
            else:  # low_rated_seller
                seller_age = random.randint(30, 180)
                seller_rating = random.uniform(1.0, 2.4)  # Low rating!
                amount = random.randint(50000, 200000)

            account_age = random.randint(1, 30)
        else:
            seller_age = random.randint(30, 730)
            seller_rating = random.uniform(3.5, 5.0)
            amount = random.randint(5000, 150000)
            account_age = random.randint(30, 365)

        return {
            'transaction_id': f'txn_{txn_id:06d}',
            'user_id': user_id,
            'amount': amount,
            'transaction_type': random.choice(['buyer_payment', 'seller_payout']),
            'industry': 'marketplace',
            'device_id': self.data_gen.generate_device_id(),
            'ip_address': self.data_gen.generate_ip_address(is_fraud),
            'account_age_days': account_age,
            'transaction_count': random.randint(1, 50),

            # Marketplace specific
            'seller_id': seller_id,
            'seller_rating': round(seller_rating, 1),
            'seller_account_age_days': seller_age,
            'product_category': category,
            'is_high_value_item': is_high_value,

            'email': self.data_gen.generate_email(user_id, is_fraud),
            'city': random.choice(self.data_gen.cities),
            'is_fraud': is_fraud,
            'created_at': datetime.now() - timedelta(hours=random.randint(0, 720))
        }


def generate_synthetic_data(
    count: int,
    fraud_rate: float,
    industries: List[str]
) -> List[Dict[str, Any]]:
    """
    Generate synthetic transaction data

    Args:
        count: Number of transactions to generate
        fraud_rate: Percentage of fraudulent transactions (0.0 to 1.0)
        industries: List of industries to include

    Returns:
        List of transaction dictionaries
    """
    data_gen = NigerianDataGenerator()
    fraud_gen = FraudTransactionGenerator(data_gen)

    transactions = []
    fraud_count = int(count * fraud_rate)

    # Industry generators
    generators = {
        'fintech': fraud_gen.generate_fintech_transaction,
        'lending': fraud_gen.generate_fintech_transaction,
        'ecommerce': fraud_gen.generate_ecommerce_transaction,
        'betting': fraud_gen.generate_betting_transaction,
        'crypto': fraud_gen.generate_crypto_transaction,
        'marketplace': fraud_gen.generate_marketplace_transaction,
    }

    # Filter generators by requested industries
    active_generators = {k: v for k, v in generators.items() if k in industries}

    if not active_generators:
        raise ValueError(f"No valid industries selected. Choose from: {list(generators.keys())}")

    print(f"🔄 Generating {count:,} transactions ({fraud_rate*100:.1f}% fraud rate)...")
    print(f"📊 Industries: {', '.join(industries)}")

    for i in range(count):
        # Determine if this transaction is fraud
        is_fraud = i < fraud_count

        # Pick random industry
        industry = random.choice(list(active_generators.keys()))
        generator = active_generators[industry]

        # Generate transaction
        transaction = generator(i + 1, is_fraud)

        transactions.append(transaction)

        # Progress indicator
        if (i + 1) % 1000 == 0:
            print(f"  Generated {i + 1:,} transactions...")

    # Shuffle to mix fraud and legitimate transactions
    random.shuffle(transactions)

    fraud_actual = sum(1 for t in transactions if t['is_fraud'])
    print(f"✅ Generated {count:,} transactions")
    print(f"   Fraudulent: {fraud_actual:,} ({fraud_actual/count*100:.1f}%)")
    print(f"   Legitimate: {count - fraud_actual:,} ({(count-fraud_actual)/count*100:.1f}%)")

    return transactions


def save_to_csv(transactions: List[Dict[str, Any]], filename: str):
    """Save transactions to CSV file"""

    if not transactions:
        print("⚠️  No transactions to save")
        return

    print(f"\n💾 Saving to {filename}...")

    # Get all possible fields
    fieldnames = set()
    for txn in transactions:
        fieldnames.update(txn.keys())

    fieldnames = sorted(list(fieldnames))

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transactions)

    print(f"✅ Saved {len(transactions):,} transactions to {filename}")


def save_to_json(transactions: List[Dict[str, Any]], filename: str):
    """Save transactions to JSON file"""

    if not transactions:
        print("⚠️  No transactions to save")
        return

    print(f"\n💾 Saving to {filename}...")

    # Convert datetime objects to strings
    for txn in transactions:
        if 'created_at' in txn and isinstance(txn['created_at'], datetime):
            txn['created_at'] = txn['created_at'].isoformat()

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(transactions, f, indent=2)

    print(f"✅ Saved {len(transactions):,} transactions to {filename}")


def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(
        description='Generate synthetic Nigerian fraud data for testing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 10,000 transactions with 10% fraud rate
  python generate_synthetic_data.py --count 10000 --fraud-rate 0.10

  # Generate fintech and e-commerce only
  python generate_synthetic_data.py --count 5000 --industries fintech,ecommerce

  # Generate to JSON instead of CSV
  python generate_synthetic_data.py --count 1000 --format json

  # Generate with 20% fraud rate
  python generate_synthetic_data.py --count 50000 --fraud-rate 0.20
        """
    )

    parser.add_argument(
        '--count',
        type=int,
        default=10000,
        help='Number of transactions to generate (default: 10000)'
    )

    parser.add_argument(
        '--fraud-rate',
        type=float,
        default=0.10,
        help='Fraud rate between 0.0 and 1.0 (default: 0.10 = 10%%)'
    )

    parser.add_argument(
        '--industries',
        type=str,
        default='fintech,ecommerce,betting,crypto,marketplace',
        help='Comma-separated list of industries (default: all)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='synthetic_transactions.csv',
        help='Output filename (default: synthetic_transactions.csv)'
    )

    parser.add_argument(
        '--format',
        type=str,
        choices=['csv', 'json'],
        default='csv',
        help='Output format (default: csv)'
    )

    args = parser.parse_args()

    # Validate fraud rate
    if not 0.0 <= args.fraud_rate <= 1.0:
        print("❌ Error: fraud-rate must be between 0.0 and 1.0")
        return

    # Parse industries
    industries = [i.strip() for i in args.industries.split(',')]

    # Generate data
    print("=" * 60)
    print("🇳🇬  SENTINEL SYNTHETIC DATA GENERATOR")
    print("=" * 60)

    transactions = generate_synthetic_data(
        count=args.count,
        fraud_rate=args.fraud_rate,
        industries=industries
    )

    # Save to file
    if args.format == 'csv':
        save_to_csv(transactions, args.output)
    else:
        save_to_json(transactions, args.output)

    # Print sample
    print("\n📋 Sample transactions:")
    for i, txn in enumerate(transactions[:3]):
        print(f"\n  Transaction {i+1}:")
        print(f"    ID: {txn['transaction_id']}")
        print(f"    Amount: ₦{txn['amount']:,}")
        print(f"    Industry: {txn['industry']}")
        print(f"    Type: {txn['transaction_type']}")
        print(f"    Fraud: {'⚠️  YES' if txn['is_fraud'] else '✅ NO'}")

    print("\n" + "=" * 60)
    print("✅ DONE! Your synthetic data is ready to use.")
    print("=" * 60)


if __name__ == '__main__':
    main()
