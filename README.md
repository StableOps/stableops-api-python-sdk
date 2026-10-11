# StableOps Python SDK

[![PyPI version](https://img.shields.io/pypi/v/stableops)](https://pypi.org/project/stableops/) [![PyPI downloads](https://img.shields.io/pypi/dm/stableops)](https://pypi.org/project/stableops/) [![License](https://img.shields.io/pypi/l/stableops)](./LICENSE) [![Python](https://img.shields.io/badge/Python-%3E%3D3.8-3776AB)](https://www.python.org)

[中文文档](./README.zh-CN.md)

StableOps turns on-chain stablecoin transfers into familiar payment primitives:
payment orders, deterministic status transitions, signed webhooks, retries, and
confirmation tracking. StableOps watches supported chains, matches transfers,
tracks confirmations, checks reorgs, and delivers webhook events to your app.

This SDK is for server-side Python applications that create payment orders and
checkout sessions, manage merchant subscriptions, refunds, payment links, webhooks and agent audit
resources, and verify webhook signatures.

## Features

- Type-safe client (Pydantic v2 models) for payment orders, checkout sessions,
  merchant subscriptions, refunds, payment links, and webhooks.
- Sync (`StableOps`) and async (`AsyncStableOps`) clients with an identical API.
- Conservative retries for reads plus explicitly idempotent payment-order and
  checkout-session creation; other writes are never retried automatically.
- Constant-time webhook signature verification.

## Requirements

- Python 3.8 or newer.
- A StableOps API key.
- A server-side environment. Do not expose your API key in browser code.

## Installation

```bash
pip install stableops
```

## Quick Start

```python
import os
from datetime import datetime, timedelta, timezone

from stableops import StableOps

client = StableOps(api_key=os.environ["STABLEOPS_API_KEY"])

order = client.payment_orders.create(
    merchant_order_id="order_123",
    amount="49.00",
    accepted_assets=[
        {"chain": "base-sepolia", "asset": "USDC"},
        {"chain": "tron-nile", "asset": "USDT"},
    ],
    expires_at=(datetime.now(timezone.utc) + timedelta(minutes=25)).isoformat(),
)

print(order.payment_instructions)
```

The environment (sandbox / live) is determined by the API key prefix
(`sk_sandbox_…` / `sk_live_…`). Return only the order id, amount, and
`payment_instructions` to your frontend; the API key stays on your server.

## Refunds and payment links

Both sync and async clients expose `refunds` and `payment_links`. Refunds support
creation, retrieval, pagination, transaction submission, and cancellation.
Payment links support creation, pagination, updates, and associated-order queries.

```python
from stableops import AcceptedAssetInput, CreatePaymentLinkInput, UpdatePaymentLinkInput

refund = client.refunds.create(
    payment_order_id="po_123", amount="5.00",
    destination_address="0x0000000000000000000000000000000000000001",
)
# Sign and broadcast with your own wallet, then register the transaction hash.
client.refunds.submit(refund.id, tx_hash=merchant_signed_transaction_hash)

link = client.payment_links.create(CreatePaymentLinkInput(
    title="Pro plan", amount="49.00",
    accepted_assets=[AcceptedAssetInput(chain="base-sepolia", asset="USDC")],
    payer_fields=["email", "reference"],
))
client.payment_links.update(link.id, UpdatePaymentLinkInput(description=None))
page = client.payment_links.orders(link.id, limit=20)
```

`list_page()` returns `items`, `has_more`, and `total`. Updates send only explicitly
provided fields. `None` clears nullable fields. Refund requests do not move funds,
and writes to these new resources are not retried automatically.

Webhooks support payment, refund, subscription, invoice, agent audit, and Agent
Payments events. The package includes `py.typed` for installed-package type checking.

## Documentation

For complete guides, configuration, checkout sessions, webhook verification, and
the full API reference, see the official documentation:

- English docs: https://stableops.dev/en/docs/sdk/python-api-sdk
- Chinese docs: https://stableops.dev/zh/docs/sdk/python-api-sdk

## Supported Chains and Assets

- Chains: Ethereum, Base, Arbitrum, Polygon, Optimism, BSC, TRON, Solana, and supported testnets.
- Assets: USDC and USDT.

## License

This SDK is licensed under `Apache-2.0`. See [LICENSE](./LICENSE).
