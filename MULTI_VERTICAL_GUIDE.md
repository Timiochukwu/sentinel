# Multi-Vertical Fraud Detection Guide

Sentinel supports fraud detection across **5 major industries**. This guide shows you how to integrate Sentinel into your platform regardless of your vertical.

## Quick Industry Index

- [Fintech & Lending](#fintech--lending)
- [E-commerce](#e-commerce)
- [Betting & Gaming](#betting--gaming)
- [Crypto Platforms](#crypto-platforms)
- [Online Marketplaces](#online-marketplaces)

---

## Fintech & Lending

### Common Fraud Types
- **Loan Stacking**: Users applying to 3+ lenders within 7 days
- **SIM Swap Attacks**: Phone hijacking followed by loan disbursement
- **Account Takeover**: Stolen credentials used for unauthorized loans
- **Synthetic Identity**: Fake identities created with mixed real/fake data

### API Example

```bash
curl -X POST http://localhost:8080/api/v1/check-transaction \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "transaction_id": "loan_12345",
    "user_id": "user_789",
    "amount": 500000,
    "transaction_type": "loan_disbursement",
    "industry": "lending",
    "device_id": "abc123",
    "ip_address": "197.210.226.45",
    "account_age_days": 3,
    "transaction_count": 0,
    "phone_changed_recently": true,
    "bvn": "22234567890",
    "phone": "+2348012345678",
    "is_first_transaction": true
  }'
```

### Key Fields
- `bvn`: Bank Verification Number (hashed automatically)
- `phone_changed_recently`: Critical for SIM swap detection
- `transaction_count`: Helps detect first-time fraud
- `account_age_days`: New accounts are higher risk

### Triggered Rules
- Loan Stacking (if user applied to 3+ lenders)
- SIM Swap Pattern (phone change + new device + disbursement)
- New Account Large Amount (account <7 days + amount >₦100k)

---

## E-commerce

### Common Fraud Types
- **Card Testing**: Fraudsters testing stolen cards with small purchases
- **BIN Attacks**: Using cards from high-risk BINs
- **Chargeback Fraud**: Legitimate purchase followed by fraudulent chargeback
- **Fake Transfer Screenshots**: WhatsApp/social media fake payment proof

### API Example

```bash
curl -X POST http://localhost:8080/api/v1/check-transaction \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "transaction_id": "order_98765",
    "user_id": "customer_456",
    "amount": 89000,
    "transaction_type": "purchase",
    "industry": "ecommerce",
    "device_id": "mobile_xyz",
    "ip_address": "102.89.23.45",
    "account_age_days": 2,
    "card_bin": "539983",
    "card_last4": "4321",
    "card_type": "debit",
    "payment_method": "card",
    "shipping_address_matches_billing": false,
    "is_digital_goods": true,
    "product_category": "electronics"
  }'
```

### Key Fields
- `card_bin`: First 6 digits of card (checked against high-risk BIN database)
- `shipping_address_matches_billing`: Mismatches indicate higher risk
- `is_digital_goods`: Digital goods have higher chargeback risk
- `payment_method`: Card vs transfer vs wallet

### Triggered Rules
- Card BIN Fraud (if BIN is flagged)
- Multiple Failed Payments (3+ failed attempts in 1 hour)
- Shipping Mismatch (different addresses on high-value purchase)
- Digital Goods High Value (new account + expensive digital purchase)

### Integration Tips
1. **Velocity tracking**: Send failed payment attempts to track card testing
2. **Address verification**: Always include shipping/billing match status
3. **BIN intelligence**: Keep high-risk BIN database updated
4. **Digital goods**: Apply stricter rules for digital products

---

## Betting & Gaming

### Common Fraud Types
- **Bonus Abuse**: Creating multiple accounts to claim welcome bonuses
- **Gnoming**: Using friends/family accounts for bonus abuse
- **Arbitrage Betting**: Betting on all outcomes to guarantee profit
- **Money Laundering**: Depositing dirty money, minimal wagering, then withdrawing

### API Example

```bash
curl -X POST http://localhost:8080/api/v1/check-transaction \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "transaction_id": "bet_54321",
    "user_id": "player_999",
    "amount": 200000,
    "transaction_type": "bet_withdrawal",
    "industry": "betting",
    "device_id": "samsung_abc",
    "ip_address": "105.112.34.89",
    "account_age_days": 1,
    "bet_count_today": 5,
    "bonus_balance": 50000,
    "withdrawal_count_today": 3,
    "bet_pattern_unusual": true,
    "wagering_ratio": 0.3
  }'
```

### Key Fields
- `bet_count_today`: Track betting frequency
- `bonus_balance`: Flag large bonus withdrawals
- `withdrawal_count_today`: Detect structuring (breaking large withdrawals into small ones)
- `bet_pattern_unusual`: Your system's arbitrage detection flag
- `wagering_ratio`: Ratio of bets to deposits (low = possible money laundering)

### Context Fields (pass in velocity tracking)
```json
{
  "wagering_ratio": 0.3
}
```

### Triggered Rules
- Bonus Abuse (multiple accounts from same device claiming bonuses)
- Withdrawal Without Wagering (wagering ratio <0.5 on ₦100k+ withdrawal)
- Arbitrage Betting (unusual betting patterns)
- Excessive Withdrawals (5+ withdrawals in one day)

### Integration Tips
1. **Device fingerprinting**: Critical for multi-accounting detection
2. **Wagering calculation**: Track total bets vs total deposits
3. **Pattern detection**: Flag unusual bet distributions
4. **Velocity limits**: Set daily withdrawal limits

---

## Crypto Platforms

### Common Fraud Types
- **P2P Scams**: Fake payment proof in P2P trades
- **New Wallet Fraud**: Brand new wallets attempting large trades
- **Wash Trading**: Self-trading to manipulate volume/prices
- **Money Laundering**: Using crypto to clean dirty money
- **Wallet Compromise**: Stolen wallet credentials

### API Example

```bash
curl -X POST http://localhost:8080/api/v1/check-transaction \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "transaction_id": "crypto_tx_789",
    "user_id": "trader_123",
    "amount": 5000000,
    "transaction_type": "p2p_trade",
    "industry": "crypto",
    "device_id": "iphone_pro",
    "ip_address": "197.45.67.23",
    "account_age_days": 15,
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "blockchain": "ethereum",
    "is_new_wallet": true,
    "wallet_age_days": 2
  }'
```

### Key Fields
- `wallet_address`: Checked against blacklisted/suspicious wallet database
- `blockchain`: Bitcoin, Ethereum, USDT, etc.
- `is_new_wallet`: First time using this wallet
- `wallet_age_days`: How long wallet has existed

### Context Fields
```json
{
  "blacklisted_wallets": ["0xabc123...", "0xdef456..."],
  "velocity": {
    "p2p_count_24hour": 12
  }
}
```

### Triggered Rules
- New Wallet High Value (first-time wallet with ₦500k+ transaction)
- Suspicious Wallet (wallet flagged in fraud database)
- P2P Velocity (10+ P2P trades in 24 hours)

### Integration Tips
1. **Wallet intelligence**: Maintain blacklist of known scam wallets
2. **P2P monitoring**: Track P2P trade frequency
3. **Blockchain analysis**: Different rules for different chains
4. **KYC linking**: Link wallet addresses to KYC-verified users

---

## Online Marketplaces

### Common Fraud Types
- **Seller Fraud**: New sellers listing expensive items they don't have
- **Fake Listings**: Posting items with stock photos, collecting payments, disappearing
- **Payment Scams**: Fake payment confirmations
- **Account Takeover**: Hijacking established seller accounts
- **High-Risk Categories**: Electronics, phones, luxury goods most targeted

### API Example

```bash
curl -X POST http://localhost:8080/api/v1/check-transaction \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "transaction_id": "sale_456789",
    "user_id": "buyer_333",
    "amount": 450000,
    "transaction_type": "buyer_payment",
    "industry": "marketplace",
    "device_id": "android_xyz",
    "ip_address": "102.67.89.12",
    "account_age_days": 45,
    "seller_id": "seller_777",
    "seller_rating": 2.1,
    "seller_account_age_days": 3,
    "product_category": "phones",
    "is_high_value_item": true
  }'
```

### Key Fields
- `seller_id`: Seller identifier
- `seller_rating`: Seller rating (0-5 scale)
- `seller_account_age_days`: How old seller account is
- `product_category`: Electronics, phones, gift cards are high-risk
- `is_high_value_item`: Items >₦100k are flagged

### Triggered Rules
- New Seller High Value (seller <7 days old with expensive items)
- Low Rated Seller (rating <2.5 on ₦50k+ sale)
- High Risk Category (new buyers purchasing electronics/phones)

### Integration Tips
1. **Seller verification**: Require extra verification for new sellers
2. **Escrow protection**: Hold payments longer for new sellers
3. **Category monitoring**: Electronics and phones need stricter rules
4. **Rating system**: Low-rated sellers should have payment holds

---

## Cross-Vertical Features

### Velocity Tracking
All industries benefit from velocity tracking:

```json
{
  "velocity": {
    "transaction_count_1min": 2,
    "transaction_count_10min": 5,
    "transaction_count_1hour": 12,
    "transaction_count_24hour": 45,
    "total_amount_1hour": 2500000,
    "total_amount_24hour": 8900000,
    "failed_payment_count_1hour": 3,
    "p2p_count_24hour": 8
  }
}
```

### Device Intelligence
Track device usage across accounts:

```json
{
  "device_usage": {
    "account_count": 5,
    "is_shared": true
  }
}
```

### Consortium Intelligence
Share fraud patterns across your platform:

```json
{
  "consortium": {
    "client_count": 3,
    "fraud_count": 2,
    "total_amount_involved": 1200000,
    "lenders": ["Lender A", "Lender B", "Lender C"]
  }
}
```

---

## Response Format

All industries receive the same response format:

```json
{
  "transaction_id": "txn_12345",
  "risk_score": 75,
  "risk_level": "high",
  "decision": "decline",
  "flags": [
    {
      "type": "new_account_large_amount",
      "severity": "medium",
      "message": "Account only 3 days old requesting ₦500,000",
      "score": 30,
      "confidence": 0.87
    },
    {
      "type": "sim_swap_pattern",
      "severity": "critical",
      "message": "Phone changed + new device + withdrawal - classic SIM swap pattern",
      "score": 45,
      "confidence": 0.88
    }
  ],
  "recommendation": "Decline or request video verification",
  "processing_time_ms": 67
}
```

### Decision Logic
- **approve** (risk_score <40): Low risk, process normally
- **review** (risk_score 40-69): Medium risk, manual review recommended
- **decline** (risk_score ≥70): High risk, decline transaction

---

## Best Practices

### 1. Send Complete Data
The more fields you send, the better Sentinel can detect fraud:
- ✅ Always include: transaction_id, user_id, amount, transaction_type, industry
- ✅ Recommended: device_id, ip_address, account_age_days
- ✅ Industry-specific: card_bin (ecommerce), wallet_address (crypto), seller_id (marketplace)

### 2. Implement Feedback Loop
Submit actual outcomes to train the ML model:

```bash
curl -X POST http://localhost:8080/api/v1/feedback \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "transaction_id": "txn_12345",
    "actual_outcome": "fraud",
    "fraud_type": "loan_stacking",
    "notes": "Customer confirmed they didn't apply.",
    "amount_saved": 500000
  }'
```

### 3. Monitor Performance
Use the dashboard to track:
- False positive rate (legitimate transactions declined)
- False negative rate (fraud that got through)
- Rule accuracy (which rules are most effective)
- Industry-specific patterns

### 4. Customize Thresholds
Different industries may need different risk thresholds:
- **Lending**: Conservative (decline at 65+ risk score)
- **E-commerce**: Moderate (decline at 70+ risk score)
- **Crypto**: Aggressive (decline at 60+ risk score due to irreversibility)
- **Betting**: Liberal (decline at 75+ to avoid false positives on legitimate players)

### 5. Use Webhooks
Set up real-time alerts for critical fraud:

```json
{
  "webhook_url": "https://your-platform.com/api/fraud-alerts",
  "webhook_secret": "your-secret-key",
  "webhook_events": ["high_risk_transaction", "fraud_confirmed"]
}
```

---

## Migration Guide

### Adding Sentinel to Existing Platform

**Step 1: Shadow Mode (Week 1-2)**
- Integrate API but don't act on results
- Log all fraud scores for analysis
- Compare Sentinel decisions vs your current system

**Step 2: Review Mode (Week 3-4)**
- Use "review" decision to flag transactions for manual review
- Don't auto-decline yet
- Build confidence in the system

**Step 3: Full Integration (Week 5+)**
- Auto-decline high-risk transactions
- Auto-approve low-risk transactions
- Manual review medium-risk transactions

### Industry-Specific Rollout

**Fintech/Lending**: Start with loan stacking and SIM swap detection
**E-commerce**: Start with card BIN fraud and velocity checks
**Betting**: Start with bonus abuse and multi-accounting
**Crypto**: Start with suspicious wallet detection
**Marketplace**: Start with new seller fraud detection

---

## Support & Resources

- **Documentation**: https://docs.sentinel-fraud.com
- **API Reference**: http://localhost:8080/docs
- **Dashboard**: http://localhost:5173
- **Support**: support@sentinel-fraud.com
- **Status Page**: https://status.sentinel-fraud.com

## Pricing by Industry

Contact sales for industry-specific pricing:
- Fintech/Lending: Pay per loan check
- E-commerce: Pay per transaction
- Betting: Monthly flat fee based on user count
- Crypto: Pay per wallet check
- Marketplace: Pay per seller verification
