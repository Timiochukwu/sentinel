"""
Core Fraud Detection Engine

This is the "brain" of Sentinel. When a client sends a transaction to check,
this file coordinates all the fraud detection components to make a decision.

Think of it like a fraud analyst examining a loan application:
1. They gather context (user history, device info, location, etc.)
2. They run through a checklist of red flags (the fraud rules)
3. They check with other lenders if this person applied elsewhere (consortium)
4. They calculate a risk score and make a recommendation (approve, review, or decline)

This file does all of that, but automated and in <100ms.

Key Components:
- FraudDetector: Main class that orchestrates everything
- _build_context(): Gathers all the background information needed
- check_transaction(): The main method that runs fraud detection
- _store_transaction(): Saves results to database for learning
"""

import time
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.schemas import TransactionCheckRequest, TransactionCheckResponse, FraudFlag
from app.models.database import Transaction, Client
from app.services.rules import FraudRulesEngine
from app.services.consortium import ConsortiumService
from app.services.fingerprint_rules import FingerprintFraudRules
from app.core.security import hash_device_id, hash_bvn, hash_phone, hash_email
from app.core.config import settings


class FraudDetector:
    """
    Main fraud detection engine

    This is like a fraud analyst who reviews every transaction. It:
    1. Gathers context about the user (history, device, location)
    2. Runs 29 fraud detection rules
    3. Checks consortium data (cross-lender intelligence)
    4. Calculates a risk score (0-100)
    5. Makes a decision (approve, review, or decline)
    6. Provides human-readable recommendations

    Example usage:
        detector = FraudDetector(db=db, client_id="client_123")
        result = detector.check_transaction(transaction)

        if result.decision == "decline":
            print(f"Fraud detected! Risk score: {result.risk_score}")
            print(f"Reasons: {[flag.message for flag in result.flags]}")

    Coordinates:
    - Fraud detection rules (29 rules in app/services/rules.py)
    - Consortium intelligence (cross-lender fraud patterns)
    - Context building (velocity, device history, location history)
    - Risk scoring (weighted sum of triggered rules)
    """

    def __init__(self, db: Session, client_id: str):
        """
        Initialize fraud detector

        Args:
            db: Database session for querying transaction history
            client_id: ID of the client making the fraud check request
                      (used for multi-tenancy and consortium)
        """
        self.db = db
        self.client_id = client_id

        # Initialize fraud rules engine (contains all 29 detection rules)
        self.rules_engine = FraudRulesEngine()

        # Initialize device fingerprint fraud detector (catches loan stacking)
        self.fingerprint_rules = FingerprintFraudRules()

        # Initialize consortium service (cross-lender intelligence)
        # This checks if the user has applied to other lenders recently
        self.consortium = ConsortiumService(db, client_id)

    def check_transaction(
        self,
        transaction: TransactionCheckRequest
    ) -> TransactionCheckResponse:
        """
        Main fraud detection method - this is where the magic happens!

        This method is called for every transaction that needs to be checked.
        It orchestrates all the fraud detection components and returns a
        comprehensive fraud analysis.

        Flow:
        1. Build context (gather user history, device info, location, etc.)
        2. Run all 29 fraud detection rules
        3. Calculate risk score (sum of triggered rule scores)
        4. Generate human-readable recommendation
        5. Store results in database for learning
        6. Return comprehensive fraud analysis

        Args:
            transaction: Transaction data to check
                        (contains amount, user_id, device_id, etc.)

        Returns:
            TransactionCheckResponse with:
            - risk_score: 0-100 (0 = safe, 100 = definitely fraud)
            - risk_level: "low", "medium", or "high"
            - decision: "approve", "review", or "decline"
            - flags: List of fraud indicators detected
            - recommendation: Human-readable action to take
            - processing_time_ms: How long the check took

        Example:
            transaction = TransactionCheckRequest(
                transaction_id="txn_001",
                user_id="user_123",
                amount=500000,
                device_id="iphone_abc",
                account_age_days=2,
                phone_changed_recently=True
            )

            result = detector.check_transaction(transaction)
            # result.risk_score = 75
            # result.decision = "decline"
            # result.flags = [
            #     {"type": "new_account_large_amount", "score": 30, ...},
            #     {"type": "sim_swap_pattern", "score": 45, ...}
            # ]
        """
        # Track how long this fraud check takes (for performance monitoring)
        start_time = time.time()

        # Step 0: Check if this transaction was already processed (idempotent)
        # If the same transaction_id is submitted twice, return the cached result
        # This prevents duplicate processing and database constraint violations
        from app.models.database import Transaction as TransactionModel
        existing_transaction = self.db.query(TransactionModel).filter(
            TransactionModel.transaction_id == transaction.transaction_id,
            TransactionModel.client_id == self.client_id
        ).first()

        if existing_transaction:
            # Transaction already processed - return existing result
            # This makes the API idempotent (same request = same response)
            from app.models.schemas import FraudFlag

            flags = []
            if existing_transaction.flags:
                flags = [
                    FraudFlag(
                        type=flag.get("type"),
                        severity=flag.get("severity"),
                        message=flag.get("message"),
                        score=flag.get("score"),
                        confidence=flag.get("confidence"),
                        metadata=flag.get("metadata")
                    )
                    for flag in existing_transaction.flags
                ]

            # Generate recommendation based on existing decision
            recommendation = self._generate_recommendation(
                existing_transaction.decision,
                existing_transaction.risk_level
            )

            return TransactionCheckResponse(
                transaction_id=existing_transaction.transaction_id,
                risk_score=existing_transaction.risk_score,
                risk_level=existing_transaction.risk_level,
                decision=existing_transaction.decision,
                flags=flags,
                recommendation=recommendation,
                processing_time_ms=existing_transaction.processing_time_ms,
                cached=True  # Indicate this is a cached result
            )

        # Step 1: Build context - gather background information
        # This queries the database for user history, device usage, etc.
        # Think of this as pulling up the user's "file" before reviewing
        context = self._build_context(transaction)

        # Step 2: Run all fraud detection rules
        # The rules engine checks the transaction against 29 different rules
        # Each rule that triggers adds to the risk score
        # Example: "new_account_large_amount" rule might add 30 points
        risk_score, risk_level, decision, flags = self.rules_engine.evaluate(
            transaction, context
        )

        # Step 2.5: Run device fingerprint fraud rules (NEW!)
        # Check for loan stacking, high velocity, fraud history, and consortium patterns
        # These rules are specifically designed to catch Nigerian loan stacking fraud
        if transaction.device_fingerprint:
            fingerprint_flags = self.fingerprint_rules.check_fingerprint_fraud(
                fingerprint=transaction.device_fingerprint,
                user_id=transaction.user_id,
                client_id=self.client_id,
                db=self.db,
                amount=transaction.amount
            )

            # Merge fingerprint flags with existing flags
            if fingerprint_flags:
                # Convert fingerprint flag dicts to FraudFlag objects
                for fp_flag in fingerprint_flags:
                    flags.append(FraudFlag(**fp_flag))

                # Recalculate risk score with fingerprint flags included
                risk_score = sum(flag.score for flag in flags)

                # Ensure risk score doesn't exceed 100
                risk_score = min(risk_score, 100)

                # Recalculate risk level based on new risk score
                if risk_score >= 70:
                    risk_level = "high"
                    decision = "decline"
                elif risk_score >= 40:
                    risk_level = "medium"
                    decision = "review"
                else:
                    risk_level = "low"
                    decision = "approve"

        # Step 3: Extract consortium intelligence
        # Consortium = shared intelligence across multiple lenders
        # Checks if this user applied to other lenders recently (loan stacking)
        consortium_data = context.get("consortium", {})
        consortium_alerts = consortium_data.get("alerts", [])

        # Step 4: Generate human-readable recommendation
        # Converts technical decision into actionable advice
        # Example: "DECLINE - High risk of SIM swap attack. Request video verification."
        recommendation = self._generate_recommendation(
            risk_level, decision, flags, consortium_alerts
        )

        # Step 5: Calculate how long this check took
        # Target: <100ms for real-time fraud detection
        # With caching, this can be as low as 5ms
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Step 6: Store transaction in database
        # This enables:
        # - Historical analysis
        # - ML model training
        # - Fraud pattern identification
        # - Client analytics/reporting
        self._store_transaction(
            transaction=transaction,
            risk_score=risk_score,
            risk_level=risk_level,
            decision=decision,
            flags=flags,
            processing_time_ms=processing_time_ms
        )

        # Step 7: Build comprehensive response
        # This is what gets sent back to the client
        response = TransactionCheckResponse(
            transaction_id=transaction.transaction_id,
            risk_score=risk_score,
            risk_level=risk_level,
            decision=decision,
            flags=flags,
            recommendation=recommendation,
            processing_time_ms=processing_time_ms,
            consortium_alerts=consortium_alerts if consortium_alerts else None
        )

        return response

    def _build_context(self, transaction: TransactionCheckRequest) -> Dict[str, Any]:
        """
        Build context for fraud detection

        "Context" is all the background information we need to make a good decision.
        Think of it like a detective gathering clues before solving a case.

        For a loan application, we want to know:
        - Has this person applied to other lenders? (consortium)
        - How many transactions has this user done today? (velocity)
        - How many people use this device? (device sharing)
        - Where was the user last time? (impossible travel detection)
        - Is the IP address from a VPN? (location spoofing)

        This context is passed to the fraud rules so they can make informed decisions.

        Why is context important?
        - Amount alone doesn't tell us much
        - ₦100k is normal for a 2-year-old account
        - But ₦100k is suspicious for a 2-day-old account!
        - Context makes the difference

        Args:
            transaction: The transaction being checked

        Returns:
            Dictionary of contextual information:
            {
                "consortium": {...},      # Cross-lender intelligence
                "new_device": True/False, # First time device?
                "velocity": {...},        # Transaction velocity
                "device_usage": {...},    # How many accounts use this device
                "last_location": {...},   # Last known location
                "is_vpn": True/False,     # Is IP from VPN?
                "max_loan_amount": 500000 # Client's max loan amount
            }
        """
        context = {}

        # CONSORTIUM INTELLIGENCE
        # Check if this user has applied to other lenders recently
        # This catches "loan stacking" - applying to many lenders at once
        if settings.ENABLE_CONSORTIUM:
            # Query consortium database for fraud patterns
            consortium_data = self.consortium.check_fraud_patterns(transaction)
            context["consortium"] = consortium_data

            # Also check loan stacking specifically
            # Loan stacking = applying to 3+ lenders in a week
            stacking_data = self.consortium.check_loan_stacking(transaction)

            # Take the max client count from both checks
            # (Some fraud patterns might not be loan applications)
            context["consortium"]["client_count"] = max(
                consortium_data.get("client_count", 0),
                stacking_data.get("client_count", 0)
            )
            context["consortium"]["lenders"] = stacking_data.get("lenders", [])

        # DEVICE FINGERPRINTING
        # Check if this is the first time we've seen this device for this user
        # New device + withdrawal = possible account takeover
        context["new_device"] = self._is_new_device(transaction)

        # VELOCITY CHECKS
        # How many transactions has this user done in the last 10min/1hr/24hr?
        # High velocity = possible fraud (card testing, bonus abuse, etc.)
        # Note: In production, this would query Redis for real-time data
        context["velocity"] = self._get_velocity_data(transaction)

        # DEVICE SHARING DETECTION
        # How many different accounts use this device?
        # 5+ accounts on same device = multi-accounting fraud
        context["device_usage"] = self._get_device_usage(transaction)

        # IMPOSSIBLE TRAVEL
        # Where was the user last time? Can they physically be here now?
        # Example: Last transaction in Lagos 2 hours ago, now in Kano = suspicious
        context["last_location"] = self._get_last_location(transaction)

        # VPN/PROXY DETECTION
        # Is the IP address from a VPN or proxy service?
        # Fraudsters use VPNs to hide their real location
        context["is_vpn"] = self._is_vpn(transaction)

        # CLIENT CONFIGURATION
        # What's the maximum loan amount this client offers?
        # Used to detect "maximum first transaction" fraud
        context["max_loan_amount"] = self._get_max_loan_amount()

        return context

    def _is_new_device(self, transaction: TransactionCheckRequest) -> bool:
        """
        Check if this is a new device for the user

        Why this matters:
        - Legitimate users typically use the same 1-2 devices
        - New device + withdrawal = possible account takeover
        - New device + large transaction = suspicious

        How it works:
        1. Hash the device ID (for privacy)
        2. Query database for any previous transactions from this user with this device
        3. If no matches found, it's a new device

        Args:
            transaction: Transaction being checked

        Returns:
            True if this is the first time we've seen this device for this user
            False if we've seen this device before, or if no device_id provided

        Example:
            User "user_123" normally uses device "iphone_abc"
            They now submit transaction from device "android_xyz"
            _is_new_device() returns True
            This triggers "new_device" fraud rule
        """
        if not transaction.device_id:
            return False  # No device ID provided, can't check

        # Hash the device ID for privacy
        # We never store raw device IDs, only SHA-256 hashes
        device_hash = hash_device_id(transaction.device_id)

        # Query database: has this user used this device before?
        existing = self.db.query(Transaction).filter(
            Transaction.client_id == self.client_id,      # Only check this client's data
            Transaction.user_id == transaction.user_id,   # For this specific user
            Transaction.device_id == device_hash          # With this specific device
        ).first()

        # If no matching record found, it's a new device
        return existing is None

    def _get_velocity_data(self, transaction: TransactionCheckRequest) -> Dict:
        """
        Get transaction velocity for the user

        Velocity = how many transactions in recent time windows
        Used to detect:
        - Card testing (many small transactions in minutes)
        - Bonus abuse (rapid bet placements)
        - Money laundering (high transaction volume)

        In production, this would query Redis for real-time counters.
        Redis is used because:
        - It's fast (sub-millisecond lookups)
        - Counters auto-expire (INCR with TTL)
        - No complex database queries needed

        Current implementation:
        This is a simplified version returning mock data.
        TODO: Replace with Redis-based velocity tracking

        Args:
            transaction: Transaction being checked

        Returns:
            Dictionary with transaction counts:
            {
                "transaction_count_10min": 1,   # Transactions in last 10 minutes
                "transaction_count_1hour": 2,   # Transactions in last hour
                "transaction_count_24hour": 5   # Transactions in last 24 hours
            }

        Production implementation would be:
            redis_key = f"velocity:{user_id}:10min"
            count_10min = redis.get(redis_key) or 0
        """
        # In production, this would query Redis for real-time velocity
        # For now, return mock data to show structure
        return {
            "transaction_count_10min": 1,
            "transaction_count_1hour": 2,
            "transaction_count_24hour": 5
        }

    def _get_device_usage(self, transaction: TransactionCheckRequest) -> Dict:
        """
        Get device usage statistics

        Checks how many different user accounts have used this device.

        Why this matters:
        - Legitimate users: 1 device = 1 account
        - Fraudsters: 1 device = many accounts
        - 5+ accounts on same device = multi-accounting fraud

        Common fraud patterns:
        - Bonus abuse (create many accounts to claim welcome bonuses)
        - Betting fraud (circumvent betting limits)
        - Loan stacking (apply with multiple fake identities)

        How it works:
        1. Hash the device ID
        2. Count distinct user_ids that have used this device
        3. Return the count

        Args:
            transaction: Transaction being checked

        Returns:
            Dictionary with account count:
            {
                "account_count": 5  # Number of accounts using this device
            }

        Example:
            Device "samsung_123" has been used by:
            - user_001
            - user_002
            - user_003
            - user_004
            - user_005
            _get_device_usage() returns {"account_count": 5}
            This triggers "device_sharing" fraud rule
        """
        if not transaction.device_id:
            return {"account_count": 0}  # No device ID, can't check

        # Hash device ID for privacy
        device_hash = hash_device_id(transaction.device_id)

        # Count unique users with this device
        # Uses SQL: SELECT COUNT(DISTINCT user_id) FROM transactions WHERE device_id = ?
        from sqlalchemy import func
        count = self.db.query(func.count(func.distinct(Transaction.user_id))).filter(
            Transaction.client_id == self.client_id,
            Transaction.device_id == device_hash
        ).scalar()

        return {"account_count": count or 0}

    def _get_last_location(self, transaction: TransactionCheckRequest) -> Dict:
        """
        Get user's last known location

        Used for "impossible travel" detection.

        Example fraud pattern:
        - Last transaction: Lagos (6.5°N, 3.4°E) at 10:00 AM
        - Current transaction: Kano (12.0°N, 8.5°E) at 11:00 AM
        - Distance: ~850km in 1 hour = 850 km/h speed
        - Impossible! This is likely account takeover or VPN fraud

        How it works:
        1. Query database for user's most recent transaction with GPS coordinates
        2. Calculate time difference between then and now
        3. Return location and time difference for distance/speed calculation

        Args:
            transaction: Transaction being checked

        Returns:
            Dictionary with last location:
            {
                "latitude": 6.5245,
                "longitude": 3.3792,
                "time_diff_hours": 1.5  # Hours since last transaction
            }
            Or empty dict {} if no previous location found

        Note:
            Not all transactions have GPS coordinates. Mobile apps typically
            provide them, but web transactions might not.
        """
        # Query for most recent transaction with GPS coordinates
        last_txn = self.db.query(Transaction).filter(
            Transaction.client_id == self.client_id,
            Transaction.user_id == transaction.user_id,
            Transaction.latitude.isnot(None),   # Must have latitude
            Transaction.longitude.isnot(None)   # Must have longitude
        ).order_by(Transaction.created_at.desc()).first()

        if not last_txn:
            return {}  # No previous location data found

        # Calculate time difference between last transaction and now
        from datetime import datetime
        time_diff = datetime.utcnow() - last_txn.created_at
        time_diff_hours = time_diff.total_seconds() / 3600  # Convert to hours

        return {
            "latitude": float(last_txn.latitude),
            "longitude": float(last_txn.longitude),
            "time_diff_hours": time_diff_hours
        }

    def _is_vpn(self, transaction: TransactionCheckRequest) -> bool:
        """
        Check if IP address is from a VPN or proxy service

        Why fraudsters use VPNs:
        - Hide their real location
        - Circumvent geo-restrictions
        - Avoid IP-based blocking
        - Make multiple accounts appear from different locations

        Current implementation:
        This is a simplified version that checks for private IP addresses.

        Production implementation should use:
        - IPHub API (https://iphub.info) - Detects VPN/proxy/hosting IPs
        - IPQualityScore - Fraud score for IP addresses
        - MaxMind GeoIP2 - Geo-location and proxy detection
        - IP2Proxy - Commercial IP detection database

        Args:
            transaction: Transaction being checked

        Returns:
            True if IP appears to be VPN/proxy
            False if IP appears legitimate or if no IP provided

        Example:
            IP 197.210.52.34 (Nigerian ISP) = False
            IP 185.220.101.1 (Known VPN) = True

        TODO: Replace with proper VPN detection service
        """
        # In production, use a service like IPHub, IPQualityScore, etc.
        if not transaction.ip_address:
            return False  # No IP provided, can't check

        # Simple check for private IPs (these shouldn't appear in production)
        # Private IP ranges: 10.x.x.x, 172.16-31.x.x, 192.168.x.x
        vpn_indicators = ["10.", "172.", "192.168."]
        return any(transaction.ip_address.startswith(indicator) for indicator in vpn_indicators)

    def _get_max_loan_amount(self) -> float:
        """
        Get maximum loan amount from client configuration

        Used to detect "maximum first transaction" fraud pattern.

        Fraud pattern:
        - Fraudsters know they'll only get one shot before being caught
        - So they apply for the maximum possible amount immediately
        - Legitimate users typically start small and build trust

        Example:
        - Client's max loan: ₦500,000
        - New user applies for: ₦495,000 (99% of max)
        - This triggers "maximum_first_transaction" rule

        Args:
            None (uses self.client_id from constructor)

        Returns:
            Maximum loan amount for this client (defaults to ₦500,000)

        Note:
            In production, this would be stored in client configuration table
            along with other settings like interest rates, terms, etc.
        """
        # Query client configuration from database
        client = self.db.query(Client).filter(
            Client.client_id == self.client_id
        ).first()

        # TODO: Add max_loan_amount column to Client table
        # For now, return default value
        # Default to ₦500k if not configured
        return 500000

    def _generate_recommendation(
        self,
        risk_level: str,
        decision: str,
        flags: list,
        consortium_alerts: list
    ) -> str:
        """
        Generate human-readable recommendation for client

        Converts technical fraud detection results into actionable advice
        that non-technical staff can understand and act on.

        Why this matters:
        - risk_score=75 doesn't tell customer service what to do
        - But "DECLINE - SIM swap attack detected" gives clear action
        - Recommendations help train customer service teams
        - Reduces false declines through clear instructions

        Recommendation strategy:
        - HIGH RISK: Clear decline with specific reason
        - MEDIUM RISK: Request additional verification before deciding
        - LOW RISK: Approve with confidence

        Args:
            risk_level: "low", "medium", or "high"
            decision: "approve", "review", or "decline"
            flags: List of fraud flags that were triggered
            consortium_alerts: Alerts from consortium intelligence

        Returns:
            Human-readable recommendation string

        Examples:
            - "DECLINE - High risk of SIM swap attack. Request video verification if needed."
            - "REVIEW - Moderate fraud risk. Request additional verification (ID, video call)."
            - "APPROVE - Low fraud risk. Transaction appears legitimate."

        Note:
            Recommendations can be customized per client based on their
            risk appetite and verification capabilities.
        """

        if risk_level == "high":
            # High risk - provide specific reason for decline

            # Check for specific fraud patterns and provide tailored recommendations
            if any(flag.type == "sim_swap_pattern" for flag in flags):
                return "DECLINE - High risk of SIM swap attack. Request video verification if needed."

            elif any(flag.type == "loan_stacking" for flag in flags):
                return "DECLINE - Loan stacking detected across multiple lenders."

            else:
                # Generic high-risk decline
                return "DECLINE - High fraud risk. Manual review required."

        elif risk_level == "medium":
            # Medium risk - request additional verification before deciding
            # This reduces false positives while still catching fraud
            return "REVIEW - Moderate fraud risk. Request additional verification (ID, video call, or bank statement)."

        else:
            # Low risk - safe to approve
            return "APPROVE - Low fraud risk. Transaction appears legitimate."

    def _store_transaction(
        self,
        transaction: TransactionCheckRequest,
        risk_score: int,
        risk_level: str,
        decision: str,
        flags: list,
        processing_time_ms: int
    ) -> None:
        """
        Store transaction and fraud detection results in database

        Why we store every transaction:
        1. **Analytics**: Track fraud rates, false positives, accuracy
        2. **ML Training**: Historical data trains future ML models
        3. **Auditing**: Compliance and fraud investigation
        4. **Learning**: Identify new fraud patterns over time
        5. **Reporting**: Client dashboards and fraud reports

        Privacy & Security:
        - All PII (BVN, phone, email, device ID) is hashed with SHA-256
        - We NEVER store raw PII
        - Hashing allows matching without exposing sensitive data
        - Example: hash("08012345678") = "7f8a9b2c..." (one-way, irreversible)

        Args:
            transaction: Original transaction request
            risk_score: Calculated risk score (0-100)
            risk_level: "low", "medium", or "high"
            decision: "approve", "review", or "decline"
            flags: List of fraud flags triggered
            processing_time_ms: How long the check took

        Returns:
            None (saves to database)

        Side effects:
        - Creates new Transaction record in database
        - Updates client's total_checks counter
        - Enables future fraud pattern detection

        Example:
            After processing a transaction:
            - Transaction stored with hashed PII
            - Client's total_checks incremented
            - Data available for analytics and ML training
        """

        # STEP 1: Hash all sensitive identifiers before storage
        # This protects customer privacy while still allowing fraud detection

        # Hash device ID (e.g., "iphone_abc123" → "7f8a9b2c...")
        device_hash = hash_device_id(transaction.device_id) if transaction.device_id else None

        # Hash BVN (Bank Verification Number - Nigerian SSN equivalent)
        bvn_hash = hash_bvn(transaction.bvn) if transaction.bvn else None

        # Hash phone number
        phone_hash = hash_phone(transaction.phone) if transaction.phone else None

        # Hash email address
        email_hash = hash_email(transaction.email) if transaction.email else None

        # Why hash instead of encrypt?
        # - Hashing is one-way (can't reverse)
        # - Still allows matching (same input = same hash)
        # - Meets NDPR/GDPR compliance requirements
        # - No risk of data breach exposing raw PII

        # STEP 2: Convert flags to JSON-serializable format
        # Pydantic models aren't directly JSON-serializable for PostgreSQL JSONB
        flags_json = [
            {
                "type": flag.type,              # e.g., "sim_swap_pattern"
                "severity": flag.severity,      # e.g., "critical"
                "message": flag.message,        # Human-readable description
                "score": flag.score,            # Risk score contribution
                "confidence": flag.confidence,  # Confidence level (0-1)
                "metadata": flag.metadata       # Additional context
            }
            for flag in flags
        ]

        # STEP 3: Create transaction database record
        # This creates a row in the 'transactions' table
        db_transaction = Transaction(
            # Transaction identifiers
            transaction_id=transaction.transaction_id,
            client_id=self.client_id,
            user_id=transaction.user_id,

            # Transaction details
            amount=transaction.amount,
            transaction_type=transaction.transaction_type,

            # Device and network info (hashed for privacy)
            device_id=device_hash,              # SHA-256 hash of device ID
            device_fingerprint=transaction.device_fingerprint,  # Browser fingerprint from FingerprintJS
            fingerprint_components=transaction.fingerprint_components,  # Detailed fingerprint data for forensics
            ip_address=transaction.ip_address,  # IP addresses are not considered PII

            # Account information
            account_age_days=transaction.account_age_days,
            transaction_count=transaction.transaction_count,

            # Contact change flags
            phone_changed_recently=transaction.phone_changed_recently,
            email_changed_recently=transaction.email_changed_recently,

            # Hashed PII (for matching without exposing raw data)
            bvn=bvn_hash,
            phone=phone_hash,
            email=email_hash,

            # Location data
            latitude=transaction.latitude,
            longitude=transaction.longitude,
            city=transaction.city,
            country=transaction.country,

            # Fraud detection results
            risk_score=risk_score,
            risk_level=risk_level,
            decision=decision,
            flags=flags_json,  # Stored as JSONB in PostgreSQL
            processing_time_ms=processing_time_ms
        )

        # Save transaction to database
        self.db.add(db_transaction)
        self.db.commit()

        # STEP 4: Update client statistics
        # Track how many fraud checks this client has performed
        client = self.db.query(Client).filter(
            Client.client_id == self.client_id
        ).first()

        if client:
            # Increment total fraud checks counter
            # Used for:
            # - Usage analytics
            # - Billing (subscription tier enforcement)
            # - Client dashboard statistics
            client.total_checks += 1
            self.db.commit()
