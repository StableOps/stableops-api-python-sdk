"""Example: Create and monitor a payment order."""

import os
import time
from datetime import datetime, timedelta, timezone

from stableops import StableOps

# Initialize client
client = StableOps(
    api_key=os.getenv("STABLEOPS_API_KEY"),
)

# Create a payment order
print("Creating payment order...")
order = client.payment_orders.create(
    merchant_order_id=f"order_{int(time.time())}",
    amount="10.00",
    accepted_assets=[
        {"chain": "base-sepolia", "asset": "USDC"},
        {"chain": "ethereum-sepolia", "asset": "USDC"},
    ],
    # 必传:≤30min(sandbox)/≤24h(live)。
    expires_at=(datetime.now(timezone.utc) + timedelta(minutes=25)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    metadata={
        "user_id": "user_123",
        "product_id": "prod_456",
    },
)

print(f"\n✓ Order created: {order.id}")
print(f"  Status: {order.status}")
print(f"  Amount: {order.amount} {order.settlement_asset}")

if order.payment_instructions:
    instruction = order.payment_instructions[0]
    print("\n📍 Payment Address:")
    print(f"  Chain: {instruction.chain}")
    print(f"  Asset: {instruction.asset}")
    print(f"  Address: {instruction.address}")
    print(f"  Candidates: {len(order.payment_instructions)}")
    print(f"\n💡 Send exactly {order.amount} {instruction.asset}")
    print(f"   to {instruction.address}")
    print(f"   on {instruction.chain} network")

# Poll for status updates
print("\n⏳ Monitoring order status...")
print("   (Press Ctrl+C to stop)")

try:
    while True:
        time.sleep(5)

        # Retrieve latest status
        updated_order = client.payment_orders.retrieve(order.id)

        if updated_order.status != order.status:
            print(f"\n🔄 Status changed: {order.status} → {updated_order.status}")
            order = updated_order

            if order.status == "finalized":
                print("\n✅ Payment finalized! Safe to fulfill order.")
                break
            elif order.status == "expired":
                print("\n⏰ Payment expired. Create a new order if needed.")
                break
            elif order.status == "reverted":
                print("\n❌ Payment reverted. Contact customer.")
                break

except KeyboardInterrupt:
    print("\n\n👋 Monitoring stopped")

# Retrieve order details with timeline
print("\n📊 Order Timeline:")
detail = client.payment_orders.retrieve(order.id)
for entry in detail.timeline:
    from_status = entry.from_status or "START"
    print(f"  {from_status} → {entry.to}")
    if entry.reason:
        print(f"    Reason: {entry.reason}")
    print(f"    At: {entry.at}")

client.close()
