# Complete Rules Reference: Fintech & Lending Verticals

## Overview

This document lists **ALL fraud detection rules** applicable to **FINTECH** and **LENDING** verticals, with their configured weights and applicability.

---

## FINTECH Vertical

**Configuration:**
```python
Industry: FINTECH
Fraud Threshold: 60.0% (medium threshold)
AML Threshold: 70.0%
Description: Digital wallets, payment apps, payment processors, mobile money
```

### Fintech Rules (Weighted)

**HIGH PRIORITY RULES (Weight > 1.3x):**

| Rule | Weight | Score Impact | Description |
|------|--------|--------------|-------------|
| `SIMSwapPatternRule` | **1.5x** | Critical | Detects SIM swap attacks (common in fintech) |
| `NewAccountLargeAmountRule` | **1.4x** | High | New account with large withdrawal/transfer |
| `VelocityCheckRule` | **1.3x** | High | Transaction velocity monitoring |
| `ImpossibleTravelRule` | **1.3x** | High | Geographic impossibility detection |

**MEDIUM PRIORITY RULES (Weight 1.0x - 1.3x):**

| Rule | Weight | Score Impact | Description |
|------|--------|--------------|-------------|
| `DeviceSharingRule` | **1.2x** | Medium-High | Multiple users on same device |
| `DisposableEmailRule` | **1.2x** | Medium-High | Temporary email detection |
| `MaximumFirstTransactionRule` | **1.0x** | Medium | First transaction amount check |
| `NewDeviceRule` | **1.0x** | Medium | Transaction from new device |
| `DormantAccountActivationRule` | **1.0x** | Medium | Dormant account suddenly active |
| `SequentialApplicationsRule` | **1.0x** | Medium | Sequential fraud applications |
| `EmailDomainLegitimacyRule` | **1.0x** | Medium | Email domain legitimacy |
| `EmailVerificationMismatchRule` | **1.0x** | Medium | Email verification mismatch |
| `PhoneVerificationFailureRule` | **1.0x** | Medium | Phone verification failure |
| `PhoneCountryMismatchRule` | **1.0x** | Medium | Phone vs IP country mismatch |
| `BVNAgeInconsistencyRule` | **1.0x** | Medium | BVN age inconsistency (Nigeria) |
| `DeviceFingerprintChangeRule` | **1.0x** | Medium | Device fingerprint changed |
| `VPNProxyRule` | **1.0x** | Medium | VPN/proxy usage |
| `IPLocationConsistencyRule` | **1.0x** | Medium | IP location inconsistency |
| `MouseMovementSuspiciousRule` | **1.0x** | Medium | Mouse movement bot-like |
| `TypingSpeedConstantRule` | **1.0x** | Medium | Typing speed constant (bot) |
| `KeystrokeDynamicsFailureRule` | **1.0x** | Medium | Keystroke dynamics failure |
| `ContactChangeWithdrawalRule` | **1.0x** | Medium | Contact change + withdrawal |
| `SuspiciousHoursRule` | **1.0x** | Medium | Transaction at unusual hours |
| `RoundAmountRule` | **1.0x** | Medium | Round amount transaction |

**REDUCED PRIORITY RULES (Weight < 1.0x):**

| Rule | Weight | Score Impact | Description |
|------|--------|--------------|-------------|
| `CardBINFraudRule` | **0.7x** | Low | Card BIN fraud (some fintech doesn't use cards) |
| `ShippingMismatchRule` | **0.0x** | None | Not applicable (no shipping in fintech) |
| `LoanStackingRule` | **0.0x** | None | Not applicable (not lending) |
| `BonusAbuseRule` | **0.0x** | None | Not applicable (not betting/gaming) |
| `DigitalGoodsHighValueRule` | **0.0x** | None | Not applicable (not ecommerce) |

---

### All Applicable Fintech Rules (Alphabetical)

**A-C:**
1. `AccountResurrectionRule` - Old inactive account reactivated
2. `AccountVelocityRatioRule` - Account velocity ratio high
3. `AddressDistanceAnomalyRule` - Address distance anomaly
4. `AddressFraudHistoryRule` - Address in fraud history
5. `APIErrorVelocityRule` - API error rate high
6. `AppSwitchingRule` - App switching pattern suspicious
7. `ArbitrageDetectionRule` - Arbitrage pattern (if applicable)
8. `ASNBlacklistRule` - ASN on blacklist
9. `BatteryDrainAnomalyRule` - Battery behavior anomaly
10. `BehavioralFailedLoginsRule` - Failed login check
11. `BehavioralFailedLoginVelocityRule` - Failed login velocity
12. `BehavioralFirstTransactionAmountRule` - First transaction check
13. `BehavioralKeystrokeDynamicsRule` - Keystroke dynamics
14. `BehavioralLoginFrequencyRule` - Login frequency anomaly
15. `BehavioralMouseMovementRule` - Mouse behavior
16. `BehavioralPasswordResetRule` - Password reset pattern
17. `BehavioralSessionDurationRule` - Session duration check
18. `BehavioralTransactionVelocityRule` - Transaction velocity
19. `BehavioralTypingSpeedRule` - Typing speed anomaly
20. `BehavioralUnusualTimeRule` - Unusual transaction time
21. `BehavioralWeekendTransactionRule` - Weekend pattern
22. `BehaviorSimilarityHighRule` - Behavior similar to fraudster
23. `BeneficiaryPatternAnomalyRule` - Beneficiary pattern anomaly
24. `BiometricAuthFailureRule` - Biometric auth failed
25. `BrowserConsistencyRule` - Browser behavior inconsistent
26. `BrowserFingerprintConsistencyRule` - Fingerprint inconsistent
27. `BrowserVersionAnomalyRule` - Rare browser version
28. `BusinessConnectionDetectedRule` - Business connection to fraud
29. `BVNAgeInconsistencyRule` - BVN age inconsistency (1.0x weight)
30. `BVNFraudHistoryRule` - BVN fraud history
31. `BVNFraudMatchRule` - BVN matches fraudster
32. `CampaignTrackingAnomalyRule` - Campaign tracking anomaly
33. `CanvasFingerprinterRule` - Canvas fingerprint mismatch
34. `CardAgeNewRule` - Very new card
35. `CardBINFraudRule` - Card BIN fraud (0.7x weight)
36. `CardBINReputationRule` - Low BIN reputation
37. `CardReputationLowRule` - Card reputation low
38. `CardTestingPatternRule` - Card testing detected
39. `ChargebackHistoryRule` - Chargeback history
40. `CommonNameDetectionRule` - Common/generic name
41. `ConnectedAccountsDetectedRule` - Connected accounts
42. `ConsortiumBVNFrequencyRule` - BVN in consortium
43. `ConsortiumDeviceFrequencyRule` - Device in consortium
44. `ConsortiumEmailFrequencyRule` - Email in consortium
45. `ConsortiumPhoneFrequencyRule` - Phone in consortium
46. `ContactChangeWithdrawalRule` - Contact change + withdrawal (1.0x)
47. `CopyPasteAbuseRule` - Excessive copy/paste
48. `CPUCoreAnomalyRule` - CPU core count anomaly
49. `CrossAccountFundingRule` - Cross-account funding

**D-F:**
50. `DeepLearningScoreRule` - Deep learning score high
51. `DeepLinkBypassRule` - Deeplink bypass attempt
52. `DerivedFraudsterSimilarityRule` - Fraudster similarity
53. `DeviceAccelerationPatternRule` - Accelerometer unusual
54. `DeviceBatteryLevelRule` - Battery level suspicious
55. `DeviceBrowserFingerprintRule` - Browser fingerprint changed
56. `DeviceEmulatorDetectionRule` - Emulator detected
57. `DeviceFingerprintChangeRule` - Device fingerprint changed (1.0x)
58. `DeviceFraudHistoryRule` - Device fraud history
59. `DeviceFraudLinkageRule` - Device linked to fraud
60. `DeviceJailbreakDetectionRule` - Jailbreak detected
61. `DeviceOSChangedRule` - OS changed
62. `DeviceScreenResolutionRule` - Resolution doesn't match
63. `DeviceSharingRule` - Multiple users on device (1.2x)
64. `DeviceTimezoneHoppingRule` - Timezone hopping
65. `DisposableEmailRule` - Disposable email (1.2x)
66. `DollarOneAuthorizationRule` - $1 authorization tests
67. `DormantAccountActivationRule` - Dormant account active (1.0x)
68. `DuplicateTransactionRule` - Duplicate transaction
69. `EmailDomainAgeRule` - New email domain
70. `EmailDomainLegitimacyRule` - Email domain legitimacy (1.0x)
71. `EmailFraudHistoryRule` - Email fraud history
72. `EmailFraudLinkageRule` - Email linked to fraud
73. `EmailReputationRule` - Low email reputation
74. `EmailSimilarityHighRule` - Email similar to fraudster
75. `EmailVerificationMismatchRule` - Email verification mismatch (1.0x)
76. `EmulatorDetectionRule` - Emulator detected
77. `EnsembleConfidenceRule` - Ensemble confidence high
78. `EnsembleModelConsensusRule` - Ensemble consensus
79. `EntropyAnomalyRule` - Entropy anomaly
80. `ErrorCorrectionPatternRule` - No errors (bot)
81. `ExcessiveCopyPasteRule` - Too much copy/paste
82. `ExcessiveFailedLoginsRule` - Too many failed logins
83. `FailedLoginVelocityATORule` - Login failure velocity
84. `FamilyConnectionDetectedRule` - Family connection
85. `FamilyFraudLinkRule` - Family member fraud
86. `FirstTimeCardRule` - First time using card
87. `FirstTransactionAmountDeviation` - First amount deviates
88. `FirstTransactionAmountRule` - First amount suspicious
89. `FontListAnomalyRule` - Installed fonts suspicious
90. `FormFillingSpeedRule` - Form filled too fast
91. `FraudProbabilityHighRule` - Fraud probability > 80%
92. `FraudsterProfileMatchRule` - Matches fraudster profile
93. `FundingSourceNewCardWithdrawalRule` - New card withdrawal

**G-L:**
94. `GeographicConnectionDetectedRule` - Geographic connection
95. `GeographicImpossibilityATORule` - Geographic impossibility
96. `GNNGraphAnomalyRule` - Graph neural network anomaly
97. `GPUFingerprintAnomalyRule` - GPU fingerprint unusual
98. `HesitationDetectionRule` - No hesitation (bot)
99. `HighConfidenceFraudRule` - High confidence fraud
100. `HighRiskCountryFundingRule` - High-risk country funding
101. `HighRiskPhoneCarrierRule` - High-risk carrier
102. `HolidayWeekendTransactionRule` - Holiday/weekend txn
103. `IllegalEmailDomainRule` - Illegal domain
104. `ImpossibleTravelRule` - Impossible travel (1.3x)
105. `IPFraudLinkageRule` - IP linked to fraud
106. `IPLocationConsistencyRule` - IP location inconsistent (1.0x)
107. `ISPReputationRule` - Low ISP reputation
108. `JailbreakDetectionRule` - Jailbroken device
109. `KeystrokeDynamicsFailureRule` - Keystroke failure (1.0x)
110. `KeystrokeDynamicsRule` - Keystroke timing
111. `KnownFraudsterPatternRule` - Known fraudster pattern
112. `LoginFailureAccelerationRule` - Failed login accelerating
113. `LowBehavioralConsistencyRule` - Low behavioral consistency
114. `LowGeographicConsistencyRule` - Low geographic consistency
115. `LowLegitimacyScoreRule` - Low legitimacy score
116. `LowRatedSellerRule` - Low seller rating (if P2P payments)
117. `LowTemporalConsistencyRule` - Low temporal consistency
118. `LSTMSequenceAnomalyRule` - LSTM sequence anomaly

**M-P:**
119. `MalwareAppDetectionRule` - Malware app detected
120. `MaximumFirstTransactionRule` - First transaction too large (1.0x)
121. `MerchantChargebackRateRule` - High chargeback rate
122. `MerchantHighRiskCategoryRule` - High-risk category
123. `MerchantRefundRateRule` - High refund rate
124. `MobileGestureAnomalyRule` - Mobile gestures unusual
125. `MobileSwipePatternRule` - Swipe pattern unusual
126. `MouseMovementDeviationRule` - Mouse deviation
127. `MouseMovementSuspiciousRule` - Mouse movement bot-like (1.0x)
128. `MultipleCardsDeviceRule` - Too many cards on device
129. `MultipleDevicesSameUserRule` - User has too many devices
130. `MultipleEmailsDeviceRule` - Many emails from device
131. `MultipleFailedPaymentsRule` - Multiple payment failures
132. `MultipleSourcesAddedQuicklyRule` - Multiple funding sources
133. `NetworkBVNFraudLinkRule` - BVN fraud network
134. `NetworkDatacenterIPRule` - Datacenter IP
135. `NetworkDeviceFraudLinkRule` - Device fraud network
136. `NetworkEmailFraudLinkRule` - Email fraud network
137. `NetworkFraudRingDetectionRule` - Fraud ring
138. `NetworkIPFraudLinkRule` - IP fraud network
139. `NetworkIPReputationRule` - IP reputation
140. `NetworkMoneyMuleRule` - Money mule network
141. `NetworkPhoneFraudLinkRule` - Phone fraud network
142. `NetworkSyntheticIdentityRule` - Synthetic identity
143. `NetworkTorDetectionRule` - Tor network
144. `NetworkVelocityDeviceRule` - Device velocity
145. `NetworkVelocityEmailRule` - Email velocity
146. `NetworkVelocityIPRule` - IP velocity
147. `NetworkVelocityPhoneRule` - Phone velocity
148. `NetworkVPNDetectionRule` - VPN detected
149. `NewAccountLargeAmountRule` - New account large amount (1.4x)
150. `NewBankAccountWithdrawalRule` - New bank account withdrawal
151. `NewDeviceHighValueATORule` - New device high value
152. `NewDeviceRule` - New device (1.0x)
153. `NotificationInteractionRule` - Notification suspicious
154. `OSInconsistencyRule` - OS information inconsistent
155. `OutlierScoreHighRule` - Statistical outlier
156. `P2PVelocityRule` - P2P velocity (if applicable)
157. `PageRefreshAnomalyRule` - Page refreshing suspicious
158. `PasswordResetWithdrawalRule` - Password reset + withdrawal
159. `PhoneAgeRule` - Very new phone
160. `PhoneCarrierRiskRule` - High-risk carrier
161. `PhoneCountryMismatchRule` - Phone country mismatch (1.0x)
162. `PhoneFraudHistoryRule` - Phone fraud history
163. `PhoneFraudLinkageRule` - Phone linked to fraud
164. `PhoneVerificationFailureRule` - Phone verification failed (1.0x)
165. `ProfileDeviationRule` - Profile deviation

**Q-S:**
166. `QuickSignupTransactionRule` - Signup → transaction too fast
167. `RapidProgressionRule` - Rapid amount escalation
168. `ReferralFraudRule` - Referral fraud
169. `ReferrerSourceAnomalyRule` - Referrer suspicious
170. `RefundAbuseDetectedRule` - Refund abuse
171. `RefundAbusePatternRule` - Refund abuse pattern
172. `RefundAbuseSerialRule` - Serial refund abuse
173. `RobotSessionDetectionRule` - Bot session
174. `RoundAmountRule` - Round amount (1.0x)
175. `RoundAmountSuspiciousRule` - Suspicious round amount
176. `RoundTripTransactionRule` - Round-trip transaction
177. `RuleViolationCountHighRule` - Too many violations
178. `SameAddressMultipleUsersRule` - Many users same address
179. `SameDeviceMultipleUsersRule` - Multiple users device
180. `SameIPMultipleUsersRule` - Many users same IP
181. `ScreenOrientationAnomalyRule` - Screen rotation unusual
182. `ScreenResolutionAnomalyRule` - Unusual resolution
183. `ScreenResolutionHistoryRule` - Resolution changed
184. `ScrollBehaviorAnomalyRule` - Scroll behavior unusual
185. `SequentialApplicationsRule` - Sequential applications (1.0x)
186. `SessionDurationAnomalyRule` - Session too short/long
187. `SharedAccountDetectionRule` - Account sharing
188. `SIMSwapPatternRule` - SIM swap attack (1.5x)
189. `SmallFailsLargeSuccessRule` - Small fails → large success
190. `SuspiciousHoursRule` - Suspicious hours (1.0x)
191. `SuspiciousIPReputationRule` - IP reputation low
192. `SuspiciousTypingPatternRule` - Typing bot-like
193. `SyntheticIdentityRule` - Synthetic identity

**T-Z:**
194. `TabSwitchingRule` - Excessive tab switching
195. `TestTransactionPatternRule` - Test transaction pattern
196. `TimeOfDayDeviationRule` - Time of day deviation
197. `TimezoneHoppingRule` - Timezone changes frequently
198. `TimezoneOffsetAnomalyRule` - Timezone offset unusual
199. `TouchPressureInconsistencyRule` - Touch pressure inconsistent
200. `TransactionAmountMismatchRule` - Amount mismatch
201. `TransactionBankingNewAccountRule` - New banking account
202. `TransactionPatternDeviationRule` - Transaction pattern changed
203. `TransactionPatternEntropyRule` - Low entropy
204. `TransactionVelocityAccelerationRule` - Velocity accelerating
205. `TwoFactorBypassRule` - 2FA bypass
206. `TypingPatternDeviationRule` - Typing deviation
207. `TypingSpeedConstantRule` - Typing constant (1.0x)
208. `UnusualTimingPatternRule` - Timing unusual
209. `UnusualTransactionFrequencyRule` - Frequency unusual
210. `UnusualTransactionTimeRule` - Transaction time unusual
211. `UnverifiedAddressRule` - Address unverified
212. `UnverifiedPhoneIdentityRule` - Phone identity unverified
213. `UnverifiedPhoneRule` - Phone unverified
214. `UnverifiedSocialMediaRule` - Social media unverified
215. `VelocityCheckRule` - Velocity check (1.3x)
216. `VPNProxyRule` - VPN/proxy (1.0x)
217. `WebGLFingerprintRule` - WebGL fingerprint anomaly
218. `WindowResizeActivityRule` - Window resize suspicious
219. `XGBoostHighRiskRule` - XGBoost high risk

**Total Fintech Rules: ~150+ applicable rules**

---

## LENDING Vertical

**Configuration:**
```python
Industry: LENDING
Fraud Threshold: 65.0% (MOST LENIENT - false positives expensive)
AML Threshold: 75.0%
Description: Banks, loan providers, credit cards, personal loans
```

### Lending Rules (Weighted)

**CRITICAL PRIORITY RULES (Weight > 1.5x):**

| Rule | Weight | Score Impact | Description |
|------|--------|--------------|-------------|
| `MaximumFirstTransactionRule` | **1.8x** | CRITICAL | New borrowers with large loan amounts |

**HIGH PRIORITY RULES (Weight 1.3x - 1.5x):**

| Rule | Weight | Score Impact | Description |
|------|--------|--------------|-------------|
| `LoanStackingRule` | **1.5x** | Critical | Multiple loan applications (loan stacking) |
| `SIMSwapPatternRule` | **1.4x** | High | SIM swap attack detection |
| `NewAccountLargeAmountRule` | **1.3x** | High | New account with large loan |

**MEDIUM PRIORITY RULES (Weight 1.0x - 1.3x):**

| Rule | Weight | Score Impact | Description |
|------|--------|--------------|-------------|
| `DisposableEmailRule` | **1.2x** | Medium-High | Identity verification important |
| `VelocityCheckRule` | **1.0x** | Medium | Transaction/application velocity |
| `NewDeviceRule` | **1.0x** | Medium | New device detection |
| `ContactChangeWithdrawalRule` | **1.0x** | Medium | Contact change + withdrawal |
| `SuspiciousHoursRule` | **1.0x** | Medium | Application at unusual hours |
| `ImpossibleTravelRule` | **1.0x** | Medium | Geographic impossibility |
| `VPNProxyRule` | **1.0x** | Medium | VPN/proxy usage |
| `DeviceSharingRule` | **1.0x** | Medium | Device sharing detection |
| `DormantAccountActivationRule` | **1.0x** | Medium | Dormant account reactivated |
| `SequentialApplicationsRule` | **1.0x** | Medium | Sequential loan applications |
| `EmailDomainLegitimacyRule` | **1.0x** | Medium | Email domain check |
| `PhoneVerificationFailureRule` | **1.0x** | Medium | Phone verification |
| `BVNAgeInconsistencyRule` | **1.0x** | Medium | BVN age inconsistency |

**REDUCED/NOT APPLICABLE RULES (Weight < 1.0x):**

| Rule | Weight | Score Impact | Description |
|------|--------|--------------|-------------|
| `CardBINFraudRule` | **0.5x** | Low | Less relevant for loans (not card-based) |
| `GamblingTransactionRule` | **0.3x** | Very Low | Not applicable to lending |
| `BonusAbuseRule` | **0.0x** | None | Not applicable |
| `ShippingMismatchRule` | **0.0x** | None | Not applicable (no shipping) |
| `DigitalGoodsHighValueRule` | **0.0x** | None | Not applicable |
| `ArbitrageBettingRule` | **0.0x** | None | Not applicable |
| `WithdrawalWithoutWageringRule` | **0.0x** | None | Not applicable |

---

### All Applicable Lending Rules (Alphabetical)

**Lending-Specific Rules:**
1. `LoanStackingRule` (1.5x) - **CRITICAL** - Multiple concurrent loan applications
2. `SequentialApplicationsRule` (1.0x) - Sequential loan applications
3. `MaximumFirstTransactionRule` (1.8x) - **CRITICAL** - First loan too large
4. `NewAccountLargeAmountRule` (1.3x) - New borrower with large loan amount
5. `LendingCrossSellRule` - Cross-sell fraud detection

**Identity Verification (Critical for Lending):**
6. `DisposableEmailRule` (1.2x) - Temporary email addresses
7. `EmailDomainLegitimacyRule` (1.0x) - Email domain legitimacy
8. `EmailVerificationMismatchRule` (1.0x) - Email verification status
9. `PhoneVerificationFailureRule` (1.0x) - Phone verification failed
10. `PhoneCountryMismatchRule` (1.0x) - Phone vs IP country
11. `BVNAgeInconsistencyRule` (1.0x) - BVN age doesn't match
12. `BVNFraudMatchRule` - BVN matches known fraudster
13. `BVNFraudHistoryRule` - BVN in fraud history
14. `UnverifiedPhoneRule` - Phone not verified
15. `UnverifiedPhoneIdentityRule` - Phone identity unverified
16. `EmailDomainAgeRule` - New email domain
17. `EmailReputationRule` - Low email reputation
18. `PhoneAgeRule` - Very new phone number
19. `PhoneCarrierRiskRule` - High-risk phone carrier
20. `HighRiskPhoneCarrierRule` - Known high-risk carrier
21. `CommonNameDetectionRule` - Common/generic name
22. `IllegalEmailDomainRule` - Illegal/sanctioned domain

**Account Takeover (Critical for Lending):**
23. `SIMSwapPatternRule` (1.4x) - **HIGH PRIORITY** - SIM swap detection
24. `ContactChangeWithdrawalRule` (1.0x) - Contact change + withdrawal
25. `NewDeviceRule` (1.0x) - Transaction from new device
26. `PasswordResetWithdrawalRule` - Password reset then withdrawal
27. `ATOPasswordResetRule` - Suspicious password reset
28. `FailedLoginVelocityATORule` - Login failure velocity
29. `NewDeviceHighValueATORule` - New device + high value
30. `GeographicImpossibilityATORule` - Geographic impossibility
31. `DormantAccountActivationRule` (1.0x) - Dormant account active
32. `AccountResurrectionRule` - Old account reactivated
33. `ExcessiveFailedLoginsRule` - Too many failed logins
34. `LoginFailureAccelerationRule` - Failed login rate increasing
35. `TwoFactorBypassRule` - 2FA bypass attempt
36. `BiometricAuthFailureRule` - Biometric auth failed

**Velocity & Patterns:**
37. `VelocityCheckRule` (1.0x) - Application velocity
38. `TransactionVelocityAccelerationRule` - Velocity accelerating
39. `FirstTransactionAmountDeviation` - First loan amount deviation
40. `FirstTransactionAmountRule` - First amount suspicious
41. `QuickSignupTransactionRule` - Signup → loan too fast
42. `RapidProgressionRule` - Rapid loan amount escalation
43. `UnusualTransactionFrequencyRule` - Frequency unusual
44. `CrossVerticalVelocityRule` - Velocity across platforms

**Device & Network:**
45. `DeviceSharingRule` (1.0x) - Multiple users same device
46. `DeviceFingerprintChangeRule` - Device fingerprint changed
47. `NewDeviceRule` (1.0x) - New device
48. `MultipleDevicesSameUserRule` - Too many devices
49. `VPNProxyRule` (1.0x) - VPN/proxy usage
50. `ImpossibleTravelRule` (1.0x) - Impossible geographic travel
51. `IPLocationConsistencyRule` - IP location inconsistent
52. `SuspiciousIPReputationRule` - IP reputation low
53. `ASNBlacklistRule` - ASN on blacklist
54. `NetworkVPNDetectionRule` - VPN detected
55. `NetworkTorDetectionRule` - Tor network detected
56. `NetworkDatacenterIPRule` - Datacenter IP
57. `DeviceEmulatorDetectionRule` - Emulator detected
58. `EmulatorDetectionRule` - Mobile emulator
59. `JailbreakDetectionRule` - Jailbroken device
60. `DeviceJailbreakDetectionRule` - Device jailbreak/root

**Behavioral Biometrics:**
61. `MouseMovementSuspiciousRule` - Mouse movement bot-like
62. `TypingSpeedConstantRule` - Typing too constant
63. `KeystrokeDynamicsFailureRule` - Keystroke pattern failure
64. `CopyPasteAbuseRule` - Excessive copy/paste
65. `SessionDurationAnomalyRule` - Session duration unusual
66. `FormFillingSpeedRule` - Form filled too fast
67. `HesitationDetectionRule` - No hesitation (bot)
68. `ErrorCorrectionPatternRule` - No errors (bot)
69. `RobotSessionDetectionRule` - Bot session detected
70. `SuspiciousTypingPatternRule` - Typing bot-like
71. `ExcessiveCopyPasteRule` - Too much copy/paste
72. `BehavioralMouseMovementRule` - Mouse behavior
73. `BehavioralTypingSpeedRule` - Typing speed anomaly
74. `BehavioralKeystrokeDynamicsRule` - Keystroke dynamics
75. `BehavioralCopyPasteRule` - Copy/paste pattern
76. `BehavioralSessionDurationRule` - Session duration

**Consortium & Network Fraud:**
77. `EmailFraudLinkageRule` - Email linked to fraud
78. `PhoneFraudLinkageRule` - Phone linked to fraud
79. `DeviceFraudLinkageRule` - Device linked to fraud
80. `IPFraudLinkageRule` - IP linked to fraud
81. `EmailFraudHistoryRule` - Email fraud history
82. `PhoneFraudHistoryRule` - Phone fraud history
83. `DeviceFraudHistoryRule` - Device fraud history
84. `ConsortiumEmailFrequencyRule` - Email in consortium
85. `ConsortiumPhoneFrequencyRule` - Phone in consortium
86. `ConsortiumDeviceFrequencyRule` - Device in consortium
87. `ConsortiumBVNFrequencyRule` - BVN in consortium
88. `NetworkEmailFraudLinkRule` - Email fraud network
89. `NetworkPhoneFraudLinkRule` - Phone fraud network
90. `NetworkDeviceFraudLinkRule` - Device fraud network
91. `NetworkBVNFraudLinkRule` - BVN fraud network
92. `NetworkFraudRingDetectionRule` - Fraud ring detection
93. `ConnectedAccountsDetectedRule` - Connected accounts
94. `KnownFraudsterPatternRule` - Known fraudster pattern
95. `SyntheticIdentityRule` - Synthetic identity
96. `NetworkSyntheticIdentityRule` - Synthetic identity network
97. `FamilyFraudLinkRule` - Family member fraud
98. `FamilyConnectionDetectedRule` - Family connection

**Timing & Patterns:**
99. `SuspiciousHoursRule` (1.0x) - Application at unusual hours
100. `UnusualTransactionTimeRule` - Time unusual
101. `UnusualTimingPatternRule` - Timing pattern unusual
102. `HolidayWeekendTransactionRule` - Holiday/weekend application
103. `TimeOfDayDeviationRule` - Time of day deviation
104. `BehavioralUnusualTimeRule` - Unusual time
105. `BehavioralWeekendTransactionRule` - Weekend pattern
106. `LowTemporalConsistencyRule` - Low temporal consistency

**Amount & Financial Patterns:**
107. `RoundAmountRule` - Round amount (e.g., exactly $5000)
108. `RoundAmountSuspiciousRule` - Suspicious round amount
109. `AmountAnomalyRule` - Amount anomaly
110. `TransactionAmountMismatchRule` - Amount mismatch
111. `BehavioralFirstTransactionAmountRule` - First transaction
112. `OutlierScoreHighRule` - Statistical outlier

**Banking & Funding:**
113. `NewBankAccountWithdrawalRule` - New account withdrawal
114. `BankAccountVerificationFailRule` - Account verification failed
115. `TransactionBankingNewAccountRule` - New banking account
116. `CrossAccountFundingRule` - Cross-account funding
117. `RoundTripTransactionRule` - Round-trip transaction
118. `HighRiskCountryFundingRule` - High-risk country

**ML & AI Scores:**
119. `XGBoostHighRiskRule` - XGBoost high risk
120. `NeuralNetworkHighRiskRule` - Neural network risk
121. `EnsembleModelConsensusRule` - Ensemble consensus
122. `MLAnomalyDetectionRule` - ML anomaly
123. `MLAnomalyScoreRule` - ML-based anomaly
124. `DeepLearningScoreRule` - Deep learning score
125. `LSTMSequenceAnomalyRule` - LSTM sequence anomaly
126. `EntropyAnomalyRule` - Entropy anomaly
127. `ProfileDeviationRule` - Profile deviation
128. `LowLegitimacyScoreRule` - Low legitimacy score

**Similarity & Clustering:**
129. `FraudsterProfileMatchRule` - Matches fraudster
130. `DerivedFraudsterSimilarityRule` - Fraudster similarity
131. `EmailSimilarityHighRule` - Email similar to fraudster
132. `BehaviorSimilarityHighRule` - Behavior similarity

**History & Reputation:**
133. `ChargebackHistoryRule` - Chargeback history
134. `DeclinedTransactionHistoryRule` - Declined history
135. `HistoricalFraudPatternRule` - Historical pattern
136. `RefundAbuseSerialRule` - Serial refund abuse
137. `ChargebackAbuseSerialRule` - Serial chargeback

**Final Decision Rules:**
138. `FraudProbabilityHighRule` - Fraud probability > 80%
139. `RuleViolationCountHighRule` - Too many violations
140. `HighConfidenceFraudRule` - High confidence fraud
141. `EnsembleConfidenceRule` - Ensemble confidence

**Other Applicable Rules:**
142. `BrowserConsistencyRule` - Browser behavior
143. `BrowserFingerprintConsistencyRule` - Fingerprint
144. `BrowserVersionAnomalyRule` - Rare browser
145. `CanvasFingerprinterRule` - Canvas fingerprint
146. `WebGLFingerprintRule` - WebGL fingerprint
147. `GPUFingerprintAnomalyRule` - GPU fingerprint
148. `ScreenResolutionAnomalyRule` - Screen resolution
149. `DeviceScreenResolutionRule` - Resolution mismatch
150. `TimezoneHoppingRule` - Timezone hopping
151. `DeviceTimezoneHoppingRule` - Device timezone
152. `SameDeviceMultipleUsersRule` - Multiple users device
153. `SameIPMultipleUsersRule` - Multiple users IP
154. `SameAddressMultipleUsersRule` - Multiple users address
155. `TestTransactionPatternRule` - Test pattern
156. `TransactionPatternEntropyRule` - Low entropy
157. `LowBehavioralConsistencyRule` - Low consistency
158. `AccountVelocityRatioRule` - Velocity ratio
159. `LowGeographicConsistencyRule` - Low geographic
160. `GeographicConnectionDetectedRule` - Geographic connection
161. `BusinessConnectionDetectedRule` - Business connection

**Total Lending Rules: ~160+ applicable rules**

---

## Summary Comparison

| Metric | Fintech | Lending |
|--------|---------|---------|
| **Fraud Threshold** | 60% | 65% (more lenient) |
| **AML Threshold** | 70% | 75% |
| **Applicable Rules** | ~150+ | ~160+ |
| **Highest Weight Rule** | SIMSwapPatternRule (1.5x) | MaximumFirstTransactionRule (1.8x) |
| **Critical Focus** | SIM swap, velocity, device sharing | Loan stacking, identity verification, ATO |
| **Not Applicable** | Shipping, loan stacking | Shipping, betting, gaming, card-heavy rules |

---

## Usage Examples

### Fintech Example:
```python
from app.services.vertical_service import vertical_service
from app.models.schemas import Industry

# Get fintech configuration
config = vertical_service.get_config(Industry.FINTECH)
print(config.fraud_score_threshold)  # 60.0

# Get rule weight
weight = vertical_service.get_rule_weight(Industry.FINTECH, "SIMSwapPatternRule")
print(weight)  # 1.5
```

### Lending Example:
```python
# Get lending configuration
config = vertical_service.get_config(Industry.LENDING)
print(config.fraud_score_threshold)  # 65.0

# Get rule weight
weight = vertical_service.get_rule_weight(Industry.LENDING, "LoanStackingRule")
print(weight)  # 1.5

weight = vertical_service.get_rule_weight(Industry.LENDING, "MaximumFirstTransactionRule")
print(weight)  # 1.8 (HIGHEST)
```

---

## Key Differences: Fintech vs Lending

**Fintech Emphasizes:**
- SIM swap attacks (mobile money, digital wallets)
- Transaction velocity (frequent P2P transfers)
- Device sharing (multiple users, fraud rings)
- Impossible travel (location-based fraud)

**Lending Emphasizes:**
- Loan stacking (multiple concurrent applications)
- Identity verification (BVN, email, phone)
- First transaction amount (large initial loans)
- Account takeover (SIM swap, password reset)
- False positive minimization (rejecting good customers is expensive)

**Both Share:**
- Strong identity verification
- Consortium fraud intelligence
- Behavioral biometrics
- ML/AI anomaly detection
- Network fraud detection

---

**Total Rules Available:**
- **Fintech:** ~150+ rules
- **Lending:** ~160+ rules
- **Total Unique Rules in System:** 200+

Many rules apply to both verticals with different weights based on industry-specific fraud patterns.
