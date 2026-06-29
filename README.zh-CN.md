# StableOps Python SDK

[![PyPI version](https://img.shields.io/pypi/v/stableops)](https://pypi.org/project/stableops/) [![PyPI downloads](https://img.shields.io/pypi/dm/stableops)](https://pypi.org/project/stableops/) [![License](https://img.shields.io/pypi/l/stableops)](./LICENSE) [![Python](https://img.shields.io/badge/Python-%3E%3D3.8-3776AB)](https://www.python.org)

[English](./README.md)

StableOps 把链上稳定币转账封装成熟悉的支付原语：支付订单、确定性状态流转、签名
Webhook、自动重试与确认数跟踪。StableOps 负责扫描支持的链、匹配转账、跟踪确认数、
校验 reorg，并把 Webhook 事件投递到你的应用。

本 SDK 面向服务端 Python 应用：创建支付订单与 Checkout Session、管理 Webhook 端点、
校验 Webhook 签名。

## 特性

- 类型安全客户端（Pydantic v2 模型），覆盖支付订单、Checkout Session、Webhook。
- 同步（`StableOps`）与异步（`AsyncStableOps`）客户端，API 一致。
- 内置请求重试，写操作显式幂等。
- 常数时间的 Webhook 签名校验。

## 要求

- Python 3.8 及以上。
- 一个 StableOps API Key。
- 服务端环境。不要在浏览器代码中暴露 API Key。

## 安装

```bash
pip install stableops
```

## 快速开始

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

环境（sandbox / live）由 API Key 前缀（`sk_sandbox_…` / `sk_live_…`）决定。前端只接收
订单 id、金额和 `payment_instructions`，API Key 始终留在你的服务端。

## 文档

完整的指南、配置、Checkout Session、Webhook 校验与 API 参考，请查阅官网文档：

- 中文文档：https://stableops.dev/zh/docs/sdk/python-api-sdk
- English docs：https://stableops.dev/en/docs/sdk/python-api-sdk

## 支持的链与资产

- 链：Ethereum、Base、Arbitrum、Polygon、Optimism、BSC、TRON、Solana 及对应测试网。
- 资产：USDC、USDT。

## 许可证

本 SDK 使用 `Apache-2.0` 许可证，详见 [LICENSE](./LICENSE)。
