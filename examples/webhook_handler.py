"""Example: Flask webhook handler."""

import os

from flask import Flask, request

from stableops.webhooks import EVENT_ID_HEADER, SIGNATURE_HEADER, verify_webhook_signature

app = Flask(__name__)

WEBHOOK_SECRET = os.getenv("STABLEOPS_WEBHOOK_SECRET", "whsec_test123")


@app.route("/webhooks/stableops", methods=["POST"])
def handle_webhook():
    """Handle StableOps webhook."""
    # Get headers
    signature_header = request.headers.get(SIGNATURE_HEADER, "")
    event_id = request.headers.get(EVENT_ID_HEADER, "")

    # Get raw body
    body = request.get_data(as_text=True)

    # Verify signature
    verification = verify_webhook_signature(
        body=body,
        header=signature_header,
        secret=WEBHOOK_SECRET,
    )

    if not verification.valid:
        print(f"❌ Invalid webhook signature: {verification.reason}")
        return {"error": verification.reason}, 401

    # Parse event
    event = request.get_json()
    event_type = event.get("type")
    data = event.get("data", {})

    print(f"✓ Received webhook: {event_type} (ID: {event_id})")

    # Handle different event types
    if event_type == "payment.detected":
        order_id = data.get("payment_order_id")
        print(f"  💰 Payment detected for order {order_id}")
        print("     Status: Confirming...")

    elif event_type == "payment.confirmed":
        order_id = data.get("payment_order_id")
        confirmations = data.get("confirmations")
        print(f"  ✓ Payment confirmed for order {order_id}")
        print(f"     Confirmations: {confirmations}")

    elif event_type == "payment.finalized":
        order_id = data.get("payment_order_id")
        print(f"  ✅ Payment finalized for order {order_id}")
        print("     Safe to fulfill!")

        # TODO: Fulfill order
        fulfill_order(order_id)

    elif event_type == "payment.expired":
        order_id = data.get("payment_order_id")
        print(f"  ⏰ Payment expired for order {order_id}")

    elif event_type == "payment.reverted":
        order_id = data.get("payment_order_id")
        reason = data.get("reason")
        print(f"  ❌ Payment reverted for order {order_id}")
        print(f"     Reason: {reason}")

    else:
        print(f"  ℹ️  Unhandled event type: {event_type}")

    # Return 200 to acknowledge receipt
    return "", 200


def fulfill_order(order_id: str) -> None:
    """Fulfill order after payment finalized."""
    print(f"  🚀 Fulfilling order {order_id}...")

    # TODO: Implement your fulfillment logic
    # - Grant access to digital product
    # - Ship physical goods
    # - Activate subscription
    # - etc.

    print(f"  ✓ Order {order_id} fulfilled")


if __name__ == "__main__":
    print("🚀 Starting webhook server...")
    print("   Listening on http://localhost:5000/webhooks/stableops")
    print("   Use ngrok to expose: ngrok http 5000")
    app.run(port=5000, debug=True)
