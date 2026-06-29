# StableOps Python SDK

[![PyPI version](https://img.shields.io/pypi/v/stableops)](https://pypi.org/project/stableops/) [![PyPI downloads](https://img.shields.io/pypi/dm/stableops)](https://pypi.org/project/stableops/) [![License](https://img.shields.io/pypi/l/stableops)](./LICENSE) [![Python](https://img.shields.io/badge/Python-%3E%3D3.8-3776AB)](https://www.python.org)

[中文文档](./README.zh-CN.md)

StableOps turns on-chain stablecoin transfers into familiar payment primitives:
payment orders, deterministic status transitions, signed webhooks, retries, and
confirmation tracking. StableOps watches supported chains, matches transfers,
tracks confirmations, checks reorgs, and delivers webhook events to your app.

This SDK is for server-side Python applications that create payment orders and
checkout sessions, manage webhook endpoints, and verify webhook signatures.

## Features

- Type-safe client (Pydantic v2 models) for payment orders, checkout sessions, and webhooks.
- Sync (`StableOps`) and async (`AsyncStableOps`) clients with an identical API.
- Built-in request retries and explicit idempotency for write operations.
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

from stableops import StableOps

client = StableOps(api_key=os.environ["STABLEOPS_API_KEY"])

order = client.payment_orders.create(
    merchant_order_id="order_123",
    amount="49.00",
    accepted_assets=[
        {"chain": "base", "asset": "USDC"},
        {"chain": "tron", "asset": "USDT"},
    ],
    expires_at="2026-12-31T23:59:59Z",
)

print(order.payment_instructions)
```

The environment (sandbox / live) is determined by the API key prefix
(`sk_sandbox_…` / `sk_live_…`). Return only the order id, amount, and
`payment_instructions` to your frontend; the API key stays on your server.

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
