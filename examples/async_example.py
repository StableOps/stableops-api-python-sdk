"""Example: Async usage with FastAPI."""

import asyncio
import os
from datetime import datetime, timedelta, timezone

from stableops import AsyncStableOps


async def main():
    """Async example."""
    # Initialize async client
    async with AsyncStableOps(
        api_key=os.getenv("STABLEOPS_API_KEY"),
    ) as client:
        # Create payment order
        print("Creating payment order...")
        order = await client.payment_orders.create(
            merchant_order_id="async_order_123",
            amount="25.00",
            accepted_assets=[{"chain": "base-sepolia", "asset": "USDC"}],
            expires_at=(datetime.now(timezone.utc) + timedelta(minutes=25)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        print(f"✓ Order created: {order.id}")
        print(f"  Status: {order.status}")

        if order.payment_instructions:
            print(f"  Address: {order.payment_instructions[0].address}")

        # List all orders
        print("\nListing orders...")
        orders = await client.payment_orders.list(limit=5)
        print(f"✓ Found {len(orders)} orders")

        for o in orders:
            print(f"  - {o.id}: {o.status} ({o.amount} {o.settlement_asset})")

        # List address pools
        print("\nListing address pools...")
        pools = await client.addresses.get_pools()
        print(f"✓ Found {len(pools)} pools")

        for p in pools:
            print(f"  - {p['chain']}: {p['available']} available / {p['total']} total")


if __name__ == "__main__":
    asyncio.run(main())
