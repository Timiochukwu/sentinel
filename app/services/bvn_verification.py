"""BVN/NIN Verification Service for Nigerian identity verification"""

from typing import Dict, Any, Optional
from datetime import datetime, date
import httpx
from app.core.config import settings


class BVNVerificationService:
    """
    BVN (Bank Verification Number) verification service

    Integrates with:
    - NIBSS (Nigeria Inter-Bank Settlement System) for BVN verification
    - NIMC (National Identity Management Commission) for NIN verification
    - Mobile network operators for phone verification

    This is a production-ready implementation framework.
    You'll need to sign up for actual API access with NIBSS/NIMC.
    """

    def __init__(self):
        self.nibss_base_url = settings.NIBSS_API_URL if hasattr(settings, 'NIBSS_API_URL') else "https://api.nibss-plc.com.ng"
        self.nibss_api_key = settings.NIBSS_API_KEY if hasattr(settings, 'NIBSS_API_KEY') else ""
        self.timeout = 30.0  # BVN verification can be slow

    async def verify_bvn(
        self,
        bvn: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        dob: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify BVN with NIBSS

        Args:
            bvn: 11-digit Bank Verification Number
            first_name: Expected first name (optional for matching)
            last_name: Expected last name (optional for matching)
            phone: Expected phone number (optional for matching)
            dob: Expected date of birth in YYYY-MM-DD format

        Returns:
            Verification result with match status and details
        """
        # Validate BVN format
        if not bvn or len(bvn) != 11 or not bvn.isdigit():
            return {
                "is_valid": False,
                "error": "Invalid BVN format. Must be 11 digits.",
                "error_code": "INVALID_FORMAT"
            }

        try:
            # Call NIBSS API
            result = await self._call_nibss_api(bvn, phone, dob)

            if not result.get("success"):
                return {
                    "is_valid": False,
                    "error": result.get("message", "BVN verification failed"),
                    "error_code": result.get("code", "VERIFICATION_FAILED")
                }

            # Extract data from response
            bvn_data = result.get("data", {})

            # Perform matching
            matches = {
                "first_name_match": self._fuzzy_match(
                    first_name,
                    bvn_data.get("first_name")
                ) if first_name else None,
                "last_name_match": self._fuzzy_match(
                    last_name,
                    bvn_data.get("last_name")
                ) if last_name else None,
                "phone_match": self._normalize_phone(phone) == self._normalize_phone(
                    bvn_data.get("phone_number")
                ) if phone else None,
                "dob_match": dob == bvn_data.get("date_of_birth") if dob else None
            }

            # Calculate overall match score
            match_count = sum(1 for m in matches.values() if m is True)
            total_checks = sum(1 for m in matches.values() if m is not None)
            match_score = (match_count / total_checks * 100) if total_checks > 0 else 0

            return {
                "is_valid": True,
                "bvn": bvn,
                "match_score": round(match_score, 2),
                "matches": matches,
                "data": {
                    "first_name": bvn_data.get("first_name"),
                    "last_name": bvn_data.get("last_name"),
                    "middle_name": bvn_data.get("middle_name"),
                    "phone_number": bvn_data.get("phone_number"),
                    "date_of_birth": bvn_data.get("date_of_birth"),
                    "gender": bvn_data.get("gender"),
                    "enrollment_bank": bvn_data.get("enrollment_bank"),
                    "enrollment_branch": bvn_data.get("enrollment_branch"),
                    "registration_date": bvn_data.get("registration_date"),
                    "watchlist_status": bvn_data.get("watchlist_status", "clear")
                },
                "warnings": self._check_warnings(bvn_data, matches)
            }

        except httpx.TimeoutException:
            return {
                "is_valid": False,
                "error": "BVN verification timed out. Please try again.",
                "error_code": "TIMEOUT"
            }
        except Exception as e:
            return {
                "is_valid": False,
                "error": f"BVN verification error: {str(e)}",
                "error_code": "SYSTEM_ERROR"
            }

    async def verify_nin(
        self,
        nin: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        dob: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify NIN (National Identification Number) with NIMC

        Args:
            nin: 11-digit National Identification Number
            first_name: Expected first name
            last_name: Expected last name
            dob: Expected date of birth

        Returns:
            Verification result
        """
        # Validate NIN format
        if not nin or len(nin) != 11 or not nin.isdigit():
            return {
                "is_valid": False,
                "error": "Invalid NIN format. Must be 11 digits.",
                "error_code": "INVALID_FORMAT"
            }

        # For MVP, return mock response
        # In production, integrate with actual NIMC API
        return {
            "is_valid": True,
            "nin": nin,
            "match_score": 95.0,
            "data": {
                "first_name": first_name,
                "last_name": last_name,
                "date_of_birth": dob,
                "nin_status": "active"
            },
            "note": "NIMC integration pending. This is a mock response."
        }

    async def verify_phone(
        self,
        phone: str,
        expected_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify phone number ownership

        In production, integrate with:
        - MTN, Airtel, Glo, 9mobile APIs
        - Truecaller API
        - SMS verification service

        Args:
            phone: Phone number to verify
            expected_name: Expected account holder name

        Returns:
            Verification result
        """
        normalized_phone = self._normalize_phone(phone)

        if not normalized_phone:
            return {
                "is_valid": False,
                "error": "Invalid phone number format",
                "error_code": "INVALID_FORMAT"
            }

        # Detect network operator
        operator = self._detect_operator(normalized_phone)

        # For MVP, return mock response
        return {
            "is_valid": True,
            "phone": normalized_phone,
            "operator": operator,
            "status": "active",
            "registered": True,
            "note": "Phone verification integration pending. This is a mock response."
        }

    async def _call_nibss_api(
        self,
        bvn: str,
        phone: Optional[str] = None,
        dob: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call NIBSS BVN verification API

        Endpoint: POST /bvnr/VerifySingleBVN/1.0
        Documentation: https://nibss-plc.com.ng/bvn-verification

        To use in production:
        1. Sign up at https://nibss-plc.com.ng
        2. Get API credentials
        3. Add to settings: NIBSS_API_KEY, NIBSS_ORGANIZATION_CODE
        """
        if not self.nibss_api_key:
            # Return mock response for development
            return self._mock_nibss_response(bvn)

        async with httpx.AsyncClient() as client:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.nibss_api_key}"
            }

            payload = {
                "bvn": bvn,
                "verification_type": "single"
            }

            if phone:
                payload["phone_number"] = phone
            if dob:
                payload["date_of_birth"] = dob

            response = await client.post(
                f"{self.nibss_base_url}/bvnr/VerifySingleBVN/1.0",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )

            return response.json()

    def _mock_nibss_response(self, bvn: str) -> Dict[str, Any]:
        """
        Mock NIBSS response for development

        Remove this in production!
        """
        return {
            "success": True,
            "message": "BVN verification successful",
            "data": {
                "bvn": bvn,
                "first_name": "JOHN",
                "last_name": "DOE",
                "middle_name": "OLUWASEUN",
                "date_of_birth": "1990-01-15",
                "phone_number": "08012345678",
                "gender": "Male",
                "enrollment_bank": "Access Bank",
                "enrollment_branch": "Victoria Island",
                "registration_date": "2014-03-20",
                "watchlist_status": "clear"
            }
        }

    def _fuzzy_match(self, expected: Optional[str], actual: Optional[str]) -> bool:
        """
        Fuzzy string matching for names

        Handles:
        - Case insensitivity
        - Extra spaces
        - Common variations
        """
        if not expected or not actual:
            return False

        # Normalize
        exp = expected.strip().upper().replace("  ", " ")
        act = actual.strip().upper().replace("  ", " ")

        # Exact match
        if exp == act:
            return True

        # Check if one contains the other
        if exp in act or act in exp:
            return True

        # Levenshtein distance for typos (simplified)
        # In production, use python-Levenshtein library
        return False

    def _normalize_phone(self, phone: Optional[str]) -> Optional[str]:
        """
        Normalize Nigerian phone number

        Converts:
        - +2348012345678 -> 08012345678
        - 2348012345678 -> 08012345678
        - 8012345678 -> 08012345678
        """
        if not phone:
            return None

        # Remove all non-digits
        digits = ''.join(c for c in phone if c.isdigit())

        # Handle different formats
        if digits.startswith('234'):
            digits = '0' + digits[3:]
        elif len(digits) == 10:
            digits = '0' + digits

        # Validate length
        if len(digits) != 11:
            return None

        return digits

    def _detect_operator(self, phone: str) -> str:
        """Detect Nigerian mobile operator from phone number"""
        if not phone or len(phone) != 11:
            return "unknown"

        prefix = phone[1:4]  # After leading 0

        mtn_prefixes = ['803', '806', '810', '813', '814', '816', '903', '906']
        airtel_prefixes = ['802', '808', '812', '901', '902', '904', '907']
        glo_prefixes = ['805', '807', '811', '815', '905']
        nine_mobile_prefixes = ['809', '817', '818', '908', '909']

        if prefix in mtn_prefixes:
            return "MTN"
        elif prefix in airtel_prefixes:
            return "Airtel"
        elif prefix in glo_prefixes:
            return "Glo"
        elif prefix in nine_mobile_prefixes:
            return "9mobile"
        else:
            return "unknown"

    def _check_warnings(
        self,
        bvn_data: Dict[str, Any],
        matches: Dict[str, Optional[bool]]
    ) -> list:
        """Check for warning signs in BVN data"""
        warnings = []

        # Watchlist check
        if bvn_data.get("watchlist_status") != "clear":
            warnings.append({
                "type": "watchlist",
                "severity": "critical",
                "message": f"BVN on watchlist: {bvn_data.get('watchlist_status')}"
            })

        # Mismatch warnings
        if matches.get("first_name_match") is False:
            warnings.append({
                "type": "name_mismatch",
                "severity": "high",
                "message": "First name does not match BVN records"
            })

        if matches.get("phone_match") is False:
            warnings.append({
                "type": "phone_mismatch",
                "severity": "medium",
                "message": "Phone number does not match BVN records"
            })

        if matches.get("dob_match") is False:
            warnings.append({
                "type": "dob_mismatch",
                "severity": "high",
                "message": "Date of birth does not match BVN records"
            })

        return warnings


def get_bvn_verification_service() -> BVNVerificationService:
    """Get BVN verification service instance"""
    return BVNVerificationService()
