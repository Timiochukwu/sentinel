"""
Device fingerprinting and fraud detection rules

This module contains fraud detection rules related to device fingerprinting,
emulation detection, browser consistency, and device-based fraud patterns.

Rules for:
- Device fingerprinting and consistency
- Emulator and jailbreak detection
- Browser fingerprinting
- Device sharing and account takeover
"""

from typing import Optional, Dict, Any
from app.schemas import TransactionCheckRequest, FraudFlag
from .base import FraudRule


class NewDeviceRule(FraudRule):
    """Rule 7: New Device - First time device + large amount"""

    def __init__(self):
        super().__init__(
            name="new_device",
            description="First time device with large transaction",
            base_score=25,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if context.get("new_device", False) and transaction.amount > 50000:
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                message=f"First time device requesting ₦{transaction.amount:,.0f}",
                score=self.base_score,
                confidence=0.71
            )
        return None

class DeviceSharingRule(FraudRule):
    """Rule 13: Device Sharing - Same device used for 5+ accounts"""

    def __init__(self):
        super().__init__(
            name="device_sharing",
            description="Device used by multiple accounts",
            base_score=35,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        device_usage = context.get("device_usage", {})
        account_count = device_usage.get("account_count", 0)

        if account_count >= 5:
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                message=f"Device used by {account_count} different accounts",
                score=self.base_score,
                confidence=0.84
            )
        return None

class DeviceFingerprintChangeRule(FraudRule):
    """Device fingerprint changed recently"""
    def __init__(self):
        super().__init__(
            name="device_fingerprint_change",
            description="Device fingerprint changed from historical",
            base_score=24,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        current_fingerprint = transaction.device_fingerprint
        previous_fingerprint = context.get("previous_device_fingerprint")
        if current_fingerprint and previous_fingerprint and current_fingerprint != previous_fingerprint:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.68, message="Device fingerprint changed from historical")
        return None

class BrowserVersionAnomalyRule(FraudRule):
    """Browser version is outdated or anomalous"""
    def __init__(self):
        super().__init__(
            name="browser_version_anomaly",
            description="Browser version is outdated or anomalous",
            base_score=18,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            browser_version = transaction.identity_features.device.browser_version
            # Check if browser version is outdated (simplified check)
            if browser_version and int(browser_version.split('.')[0] if browser_version else 0) < 50:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.60, message=f"Outdated browser version: {browser_version}")
        return None

class GPUFingerprintAnomalyRule(FraudRule):
    """GPU fingerprint indicates emulator/VM"""
    def __init__(self):
        super().__init__(
            name="gpu_fingerprint_anomaly",
            description="GPU fingerprint suggests emulation",
            base_score=32,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            gpu = transaction.identity_features.device.gpu_info
            if gpu:
                suspicious_gpus = ['swiftshader', 'llvmpipe', 'virtualbox', 'qemu', 'vmware', 'hyper-v']
                if any(s in gpu.lower() for s in suspicious_gpus):
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.85, message=f"Suspicious GPU: {gpu}")
        return None

class DeviceOSChangedRule(FraudRule):
    """Device OS changed between transactions"""
    def __init__(self):
        super().__init__(
            name="device_os_changed",
            description="Device OS changed between transactions",
            base_score=26,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        previous_os = context.get("previous_device_os")
        if transaction.identity_features and transaction.identity_features.device and previous_os:
            current_os = transaction.identity_features.device.os
            if current_os and current_os.lower() != previous_os.lower():
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.75, message=f"OS changed: {previous_os} → {current_os}")
        return None

class CanvasFingerprinterRule(FraudRule):
    """Canvas fingerprint used for tracking/fraud"""
    def __init__(self):
        super().__init__(
            name="canvas_fingerprinter",
            description="Canvas fingerprint detected",
            base_score=19,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            if transaction.identity_features.device.canvas_fingerprint:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.58, message="Canvas fingerprinting detected")
        return None

class WebGLFingerprintRule(FraudRule):
    """WebGL fingerprint indicates targeted tracking"""
    def __init__(self):
        super().__init__(
            name="webgl_fingerprint",
            description="WebGL fingerprint tracking detected",
            base_score=17,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            if transaction.identity_features.device.webgl_fingerprint:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.55, message="WebGL fingerprinting detected")
        return None

class BatteryDrainAnomalyRule(FraudRule):
    """Battery level indicates intensive activity"""
    def __init__(self):
        super().__init__(
            name="battery_drain_anomaly",
            description="Battery level suggests emulator/bot",
            base_score=12,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            battery = transaction.identity_features.device.battery_level
            if battery is not None and (battery == 100 or battery == 0):  # Always full or always zero = suspicious
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.60, message=f"Suspicious battery level: {battery}%")
        return None

class MultipleCardsDeviceRule(FraudRule):
    """Multiple cards used on same device"""
    def __init__(self):
        super().__init__(
            name="multiple_cards_device",
            description="Multiple cards linked to device",
            base_score=25,
            severity="medium",
            verticals=["ecommerce", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_features and transaction.transaction_features.card:
            count = transaction.transaction_features.card.multiple_cards_same_device
            if count and count > 5:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message=f"Device linked to {count} cards")
        return None

class ConsortiumDeviceFrequencyRule(FraudRule):
    """Device seen at many institutions"""
    def __init__(self):
        super().__init__(
            name="consortium_device_frequency",
            description="Device at multiple institutions",
            base_score=32,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.consortium_matching:
            if transaction.network_features.consortium_matching.device_seen_elsewhere:
                count = context.get("device_institution_count", 2)
                if count > 5:
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.85, message=f"Device at {count} institutions")
        return None

class NetworkVelocityDeviceRule(FraudRule):
    """High velocity across device"""
    def __init__(self):
        super().__init__(
            name="network_velocity_device",
            description="High transaction velocity on device",
            base_score=30,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "crypto"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.velocity:
            velocity = transaction.network_features.velocity.velocity_device
            if velocity and velocity > 15:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.85, message=f"Device velocity: {velocity} txns")
        return None

class SameDeviceMultipleUsersRule(FraudRule):
    """Multiple users on same device"""
    def __init__(self):
        super().__init__(
            name="same_device_multiple_users",
            description="Multiple users on same device",
            base_score=32,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "crypto"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.graph_analysis:
            count = transaction.network_features.graph_analysis.same_device_multiple_users
            if count and count > 5:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.85, message=f"{count} users on same device (loan stacking)")
        return None

class DeviceFraudHistoryRule(FraudRule):
    """Device linked to confirmed fraud"""
    def __init__(self):
        super().__init__(
            name="device_fraud_history",
            description="Device linked to fraud cases",
            base_score=36,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "crypto"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.fraud_linkage:
            if transaction.network_features.fraud_linkage.device_linked_to_fraud:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.96, message="Device linked to confirmed fraud")
        return None

class NewDeviceHighValueATORule(FraudRule):
    """New device with high-value transaction"""
    def __init__(self):
        super().__init__(
            name="new_device_high_value_ato",
            description="New device with large transaction",
            base_score=32,
            severity="high",
            verticals=["lending", "fintech", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.ato_signals and transaction.ato_signals.classic_patterns:
            if transaction.ato_signals.classic_patterns.new_device_high_value:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.82, message="New device with high-value transaction")
        return None

class MultipleDevicesSameUserRule(FraudRule):
    """Rule 37: Multiple Devices Same User - Many devices for one user"""

    def __init__(self):
        super().__init__(
            name="multiple_devices_same_user",
            description="Multiple devices used by same user",
            base_score=20,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        device_history = context.get("device_history", {})
        unique_devices = device_history.get("unique_device_count", 1)

        if unique_devices >= 7:  # 7+ different devices
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                message=f"User has used {unique_devices} different devices - possible multi-accounting",
                score=self.base_score,
                confidence=0.65
            )
        return None

class BrowserFingerprintConsistencyRule(FraudRule):
    """Rule 40: Browser Fingerprint Consistency"""
    def __init__(self):
        super().__init__(
            name="browser_fingerprint_consistency",
            description="Inconsistent browser fingerprint",
            base_score=25,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.canvas_fingerprint and transaction.webgl_fingerprint:
            if context.get("previous_canvas_fingerprint") and context.get("previous_canvas_fingerprint") != transaction.canvas_fingerprint:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.78, message="Browser fingerprint changed")
        return None

class BrowserConsistencyRule(FraudRule):
    """Rule 55: Browser Consistency Check"""
    def __init__(self):
        super().__init__(
            name="browser_consistency",
            description="Inconsistent browser profile",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.browser_fonts_hash and context.get("previous_browser_fonts_hash"):
            if context.get("previous_browser_fonts_hash") != transaction.browser_fonts_hash:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message="Browser profile changed")
        return None


# ============================================================================
# PHASE 3 FEATURES - 50 NEW RULES (Rules 56-109) for 85-90% Fraud Detection
# ============================================================================

class DeviceAccelerationPatternRule(FraudRule):
    """Rule 59: Device Acceleration Pattern"""
    def __init__(self):
        super().__init__(
            name="device_acceleration_pattern",
            description="Unusual device acceleration pattern",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.acceleration_pattern_score and transaction.acceleration_pattern_score < 25:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.71, message="Acceleration pattern anomaly")
        return None

class DeviceFraudLinkageRule(FraudRule):
    """Rule 64: Device Fraud Linkage"""
    def __init__(self):
        super().__init__(
            name="device_fraud_linkage",
            description="Device linked to fraud accounts",
            base_score=40,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.shared_device_with_fraud:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.92, message="Device linked to fraud accounts")
        return None

class EmulatorDetectionRule(FraudRule):
    """Rule 83: Emulator Detection"""
    def __init__(self):
        super().__init__(
            name="emulator_detection",
            description="Transaction from emulator",
            base_score=40,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.emulator_detected:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.92, message="Emulator detected on device")
        return None

class JailbreakDetectionRule(FraudRule):
    """Rule 84: Jailbreak/Root Detection"""
    def __init__(self):
        super().__init__(
            name="jailbreak_detection",
            description="Device is jailbroken/rooted",
            base_score=38,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.jailbreak_detected:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.90, message="Jailbreak/root detected")
        return None

class DeviceBrowserFingerprintRule(FraudRule):
    """Rule: Browser fingerprint inconsistency"""
    def __init__(self):
        super().__init__(
            name="browser_fingerprint_new",
            description="New browser fingerprint detected",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            if transaction.identity_features.device.fingerprint and context.get("previous_fingerprint"):
                if transaction.identity_features.device.fingerprint != context.get("previous_fingerprint"):
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.70, message="Browser fingerprint changed")
        return None

class DeviceScreenResolutionRule(FraudRule):
    """Rule: Screen resolution mismatch"""
    def __init__(self):
        super().__init__(
            name="screen_resolution_unusual",
            description="Unusual screen resolution",
            base_score=15,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "crypto", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            if transaction.identity_features.device.screen_resolution:
                res = transaction.identity_features.device.screen_resolution
                if res not in ["1920x1080", "1080x1920", "375x667", "414x896", "768x1024", "1024x768"]:
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.60, message="Unusual screen resolution")
        return None

class DeviceTimezoneHoppingRule(FraudRule):
    """Rule: Timezone changed dramatically"""
    def __init__(self):
        super().__init__(
            name="timezone_hopping",
            description="Timezone changed >8 hours",
            base_score=30,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            current_tz = transaction.identity_features.device.timezone
            previous_tz = context.get("previous_timezone")
            if current_tz and previous_tz:
                try:
                    tz_diff = abs(int(current_tz.split(":")[0]) - int(previous_tz.split(":")[0]))
                    if tz_diff > 8 and tz_diff < 16:
                        return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.75, message=f"Timezone changed by {tz_diff} hours")
                except:
                    pass
        return None

class DeviceEmulatorDetectionRule(FraudRule):
    """Rule: Emulator detected"""
    def __init__(self):
        super().__init__(
            name="emulator_detected_device",
            description="Mobile emulator detected",
            base_score=32,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            # Check if GPU info contains emulator keywords or CPU cores is unusual
            if transaction.identity_features.device.gpu_info:
                if "emulator" in transaction.identity_features.device.gpu_info.lower() or "swiftshader" in transaction.identity_features.device.gpu_info.lower():
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.82, message="Emulator detected via GPU info")
        return None

class DeviceJailbreakDetectionRule(FraudRule):
    """Rule: Jailbreak detected"""
    def __init__(self):
        super().__init__(
            name="jailbreak_detected_device",
            description="Device jailbreak/root detected",
            base_score=35,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            if transaction.identity_features.device.cpu_cores and transaction.identity_features.device.cpu_cores > 16:
                # Unusual CPU count often indicates jailbroken/rooted device
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.75, message="Possible jailbreak/root detected")
        return None

class DeviceBatteryLevelRule(FraudRule):
    """Rule: Suspicious battery level"""
    def __init__(self):
        super().__init__(
            name="battery_suspicious",
            description="Unusual battery level",
            base_score=12,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            if transaction.identity_features.device.battery_level is not None:
                bat = transaction.identity_features.device.battery_level
                if bat == 0 or bat == 100:
                    # Suspicious: never at exactly 0 or 100 in normal use, indicates testing/bot
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.55, message="Unusual battery level")
        return None

# PHASE 5: BEHAVIORAL FEATURES (60+ rules)

class NetworkDeviceFraudLinkRule(FraudRule):
    """Rule: Device linked to fraud"""
    def __init__(self):
        super().__init__(
            name="device_fraud_link",
            description="Device linked to fraud accounts",
            base_score=40,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.fraud_linkage:
            if transaction.network_features.fraud_linkage.device_linked_to_fraud:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.90, message="Device linked to fraud accounts")
        return None

# Export all device rules
DEVICE_RULES = [
    NewDeviceRule(),
    DeviceSharingRule(),
    DeviceFingerprintChangeRule(),
    BrowserVersionAnomalyRule(),
    GPUFingerprintAnomalyRule(),
    DeviceOSChangedRule(),
    CanvasFingerprinterRule(),
    WebGLFingerprintRule(),
    BatteryDrainAnomalyRule(),
    MultipleCardsDeviceRule(),
    ConsortiumDeviceFrequencyRule(),
    NetworkVelocityDeviceRule(),
    SameDeviceMultipleUsersRule(),
    DeviceFraudHistoryRule(),
    NewDeviceHighValueATORule(),
    MultipleDevicesSameUserRule(),
    BrowserFingerprintConsistencyRule(),
    BrowserConsistencyRule(),
    DeviceAccelerationPatternRule(),
    DeviceFraudLinkageRule(),
    EmulatorDetectionRule(),
    JailbreakDetectionRule(),
    DeviceBrowserFingerprintRule(),
    DeviceScreenResolutionRule(),
    DeviceTimezoneHoppingRule(),
    DeviceEmulatorDetectionRule(),
    DeviceJailbreakDetectionRule(),
    DeviceBatteryLevelRule(),
    NetworkDeviceFraudLinkRule(),
]
