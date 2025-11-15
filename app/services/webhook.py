"""Webhook service for real-time fraud alerts"""

import hmac
import hashlib
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import httpx
from sqlalchemy.orm import Session
from app.models.database import Client, Transaction
from app.core.config import settings


class WebhookService:
    """
    Webhook service for real-time notifications

    Features:
    - Real-time fraud alerts
    - Retry mechanism with exponential backoff
    - HMAC signature verification
    - Event types: transaction.high_risk, transaction.declined, fraud.confirmed
    """

    def __init__(self):
        self.max_retries = 3
        self.retry_delays = [2, 4, 8]  # Exponential backoff in seconds
        self.timeout = 10.0  # seconds

    async def send_fraud_alert(
        self,
        client: Client,
        transaction: Dict[str, Any],
        event_type: str = "transaction.high_risk"
    ) -> bool:
        """
        Send fraud alert webhook to client

        Args:
            client: Client object with webhook configuration
            transaction: Transaction data
            event_type: Type of event (transaction.high_risk, transaction.declined, etc.)

        Returns:
            True if webhook sent successfully
        """
        if not client.webhook_url:
            return False

        payload = self._build_payload(transaction, event_type)

        # Generate HMAC signature
        signature = self._generate_signature(payload, client.webhook_secret or "")

        headers = {
            "Content-Type": "application/json",
            "X-Sentinel-Signature": signature,
            "X-Sentinel-Event": event_type,
            "X-Sentinel-Timestamp": str(int(datetime.utcnow().timestamp()))
        }

        # Send with retry
        return await self._send_with_retry(
            url=client.webhook_url,
            payload=payload,
            headers=headers
        )

    async def send_feedback_notification(
        self,
        client: Client,
        transaction_id: str,
        actual_outcome: str,
        fraud_type: Optional[str] = None
    ) -> bool:
        """Send notification when fraud feedback is submitted"""
        if not client.webhook_url:
            return False

        payload = {
            "event": "fraud.confirmed" if actual_outcome == "fraud" else "fraud.false_positive",
            "transaction_id": transaction_id,
            "actual_outcome": actual_outcome,
            "fraud_type": fraud_type,
            "timestamp": datetime.utcnow().isoformat()
        }

        signature = self._generate_signature(payload, client.webhook_secret or "")

        headers = {
            "Content-Type": "application/json",
            "X-Sentinel-Signature": signature,
            "X-Sentinel-Event": payload["event"],
            "X-Sentinel-Timestamp": str(int(datetime.utcnow().timestamp()))
        }

        return await self._send_with_retry(
            url=client.webhook_url,
            payload=payload,
            headers=headers
        )

    async def send_batch_summary(
        self,
        client: Client,
        summary: Dict[str, Any]
    ) -> bool:
        """Send daily/hourly batch summary"""
        if not client.webhook_url:
            return False

        payload = {
            "event": "batch.summary",
            "period": summary.get("period", "daily"),
            "total_transactions": summary.get("total_transactions", 0),
            "high_risk_count": summary.get("high_risk_count", 0),
            "fraud_prevented_amount": summary.get("fraud_prevented_amount", 0),
            "timestamp": datetime.utcnow().isoformat()
        }

        signature = self._generate_signature(payload, client.webhook_secret or "")

        headers = {
            "Content-Type": "application/json",
            "X-Sentinel-Signature": signature,
            "X-Sentinel-Event": "batch.summary"
        }

        return await self._send_with_retry(
            url=client.webhook_url,
            payload=payload,
            headers=headers
        )

    def _build_payload(
        self,
        transaction: Dict[str, Any],
        event_type: str
    ) -> Dict[str, Any]:
        """Build webhook payload"""
        payload = {
            "event": event_type,
            "transaction_id": transaction.get("transaction_id"),
            "user_id": transaction.get("user_id"),
            "amount": transaction.get("amount"),
            "risk_score": transaction.get("risk_score"),
            "risk_level": transaction.get("risk_level"),
            "decision": transaction.get("decision"),
            "timestamp": datetime.utcnow().isoformat()
        }

        # Add flags for high risk transactions
        if event_type in ["transaction.high_risk", "transaction.declined"]:
            payload["flags"] = transaction.get("flags", [])
            payload["recommendation"] = transaction.get("recommendation")
            payload["consortium_alerts"] = transaction.get("consortium_alerts")

        return payload

    def _generate_signature(
        self,
        payload: Dict[str, Any],
        secret: str
    ) -> str:
        """
        Generate HMAC signature for payload

        Clients can verify this signature to ensure webhook authenticity
        """
        import json

        # Serialize payload
        payload_string = json.dumps(payload, sort_keys=True)

        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return signature

    async def _send_with_retry(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> bool:
        """
        Send webhook with exponential backoff retry

        Retries up to 3 times with delays: 2s, 4s, 8s
        """
        async with httpx.AsyncClient() as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.post(
                        url,
                        json=payload,
                        headers=headers,
                        timeout=self.timeout
                    )

                    # Success on 2xx status codes
                    if 200 <= response.status_code < 300:
                        return True

                    # Don't retry on 4xx errors (client errors)
                    if 400 <= response.status_code < 500:
                        print(f"Webhook failed with client error {response.status_code}: {url}")
                        return False

                    # Retry on 5xx errors (server errors)
                    print(f"Webhook attempt {attempt + 1} failed with status {response.status_code}")

                except (httpx.TimeoutException, httpx.ConnectError) as e:
                    print(f"Webhook attempt {attempt + 1} failed: {e}")

                # Wait before retry (except on last attempt)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delays[attempt])

        return False

    def verify_signature(
        self,
        payload: Dict[str, Any],
        signature: str,
        secret: str
    ) -> bool:
        """
        Verify webhook signature

        Use this on the client side to verify webhook authenticity
        """
        expected_signature = self._generate_signature(payload, secret)
        return hmac.compare_digest(signature, expected_signature)


# Helper function to send webhooks from endpoints
async def send_webhook_async(
    client: Client,
    transaction: Dict[str, Any],
    event_type: str
) -> None:
    """
    Async helper to send webhooks without blocking

    Usage in endpoints:
        asyncio.create_task(send_webhook_async(client, transaction, "transaction.high_risk"))
    """
    webhook_service = WebhookService()
    try:
        await webhook_service.send_fraud_alert(client, transaction, event_type)
    except Exception as e:
        print(f"Webhook error: {e}")
        # Don't fail the request if webhook fails


def get_webhook_service() -> WebhookService:
    """Get webhook service instance"""
    return WebhookService()
