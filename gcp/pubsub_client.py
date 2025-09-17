"""
GCP Pub/Sub helper for DataMCP

Purpose:
- Focused wrapper for Google Cloud Pub/Sub operations used by MCP tools and AI agents.
- Exposes publisher and subscriber helpers with clear, one-purpose methods:
  - publish(topic, data, attributes) -> message_id
  - pull(subscription, max_messages) -> List[Dict] (messages)
  - ack(subscription, ack_ids)
- Designed so the AI/MCP tools can call these discrete operations safely.

Usage:
    from gcp.pubsub_client import PubSubClient
    ps = PubSubClient(project="my-project")
    msg_id = ps.publish("projects/my-project/topics/my-topic", b'payload', {"k":"v"})
    msgs = ps.pull("projects/my-project/subscriptions/my-sub", max_messages=5)
    ps.ack("projects/my-project/subscriptions/my-sub", [m["ackId"] for m in msgs])

Design notes:
- This wrapper uses google-cloud-pubsub. The runtime environment must have google-cloud-pubsub installed and credentials available.
- pull returns a list of dicts containing 'message_id', 'data' (bytes), 'attributes' (dict), and 'ackId'.
- Exceptions from the underlying library propagate; calling tools should catch, audit, and sanitize outputs before exposing to agents.
"""

from __future__ import annotations
import logging
from typing import Optional, Dict, Any, List

# google pubsub libs (ensure installed in runtime)
try:
    from google.cloud import pubsub_v1  # type: ignore
    from google.auth.exceptions import DefaultCredentialsError  # type: ignore
except Exception:  # pragma: no cover
    pubsub_v1 = None  # type: ignore
    DefaultCredentialsError = Exception  # type: ignore

LOG = logging.getLogger(__name__)


class PubSubClient:
    """
    Minimal Pub/Sub wrapper.

    Methods:
    - publish(topic: str, data: bytes, attributes: Optional[Dict[str,str]] = None) -> str
    - pull(subscription: str, max_messages: int = 10, timeout: Optional[float] = None) -> List[Dict[str, Any]]
    - ack(subscription: str, ack_ids: List[str]) -> None
    """

    def __init__(self, project: Optional[str] = None, publisher_client: Optional[Any] = None, subscriber_client: Optional[Any] = None):
        """
        Args:
            project: optional default GCP project id
            publisher_client/subscriber_client: optional google client instances for testing
        """
        if pubsub_v1 is None:
            raise RuntimeError("google-cloud-pubsub is not available. Install google-cloud-pubsub package.")
        try:
            self.publisher = publisher_client or pubsub_v1.PublisherClient()
            self.subscriber = subscriber_client or pubsub_v1.SubscriberClient()
        except DefaultCredentialsError:
            LOG.exception("Failed to initialize Pub/Sub clients - credentials not found")
            raise
        self.project = project

    def publish(self, topic: str, data: bytes, attributes: Optional[Dict[str, str]] = None) -> str:
        """
        Publish a message to a topic.

        Args:
            topic: full topic path 'projects/<proj>/topics/<topic>' or short name if project configured
            data: message payload bytes
            attributes: optional message attributes

        Returns:
            message_id (str)
        """
        if not topic.startswith("projects/") and self.project:
            topic = f"projects/{self.project}/topics/{topic}"
        try:
            future = self.publisher.publish(topic, data, **(attributes or {}))
            message_id = future.result()
            return message_id
        except Exception:
            LOG.exception("Pub/Sub publish failed for topic %s", topic)
            raise

    def pull(self, subscription: str, max_messages: int = 10, timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Pull messages from a subscription (synchronous pull).

        Returns list of message dicts with keys: message_id, data (bytes), attributes, ackId
        """
        if not subscription.startswith("projects/") and self.project:
            subscription = f"projects/{self.project}/subscriptions/{subscription}"
        try:
            response = self.subscriber.pull(subscription=subscription, max_messages=max_messages, timeout=timeout or None)
            messages = []
            ack_ids = []
            for r in response.received_messages:
                msg = r.message
                messages.append({
                    "message_id": msg.message_id,
                    "data": msg.data,
                    "attributes": dict(msg.attributes),
                    "ackId": r.ack_id,
                })
                ack_ids.append(r.ack_id)
            return messages
        except Exception:
            LOG.exception("Pub/Sub pull failed for subscription %s", subscription)
            raise

    def ack(self, subscription: str, ack_ids: List[str]) -> None:
        """
        Acknowledge messages by ack IDs.
        """
        if not subscription.startswith("projects/") and self.project:
            subscription = f"projects/{self.project}/subscriptions/{subscription}"
        try:
            self.subscriber.acknowledge(subscription=subscription, ack_ids=ack_ids)
        except Exception:
            LOG.exception("Pub/Sub ack failed for subscription %s", subscription)
            raise
