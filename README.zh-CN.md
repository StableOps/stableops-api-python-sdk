# StableOps Python SDK

[![PyPI version](https://img.shields.io/pypi/v/stableops)](https://pypi.org/project/stableops/) [![PyPI downloads](https://img.shields.io/pypi/dm/stableops)](https://pypi.org/project/stableops/) [![License](https://img.shields.io/pypi/l/stableops)](./LICENSE) [![Python](https://img.shields.io/badge/Python-%3E%3D3.8-3776AB)](https://www.python.org)

[查看英文说明](./README.md)

StableOps 把链上稳定币转账封装成熟悉的支付原语：支付订单、确定性状态流转、签名
Webhook、自动重试与确认数跟踪。StableOps 负责扫描支持的链、匹配转账、跟踪确认数、
校验链重组，并把 Webhook 事件投递到你的应用。

本 SDK 面向服务端 Python 应用：创建支付订单与收银台会话、管理商户订阅、
管理退款、支付链接、Webhook 端点与代理审计资源，并校验 Webhook 签名。

## 特性

- 类型安全客户端（Pydantic v2 模型），覆盖支付订单、收银台会话、退款、支付链接、商户订阅和 Webhook。
- 同步（`StableOps`）与异步（`AsyncStableOps`）客户端，API 一致。
- 读取请求自动重试。支付订单和收银台会话创建依靠幂等键安全重试，其他写操作不自动重试。
- 常数时间的 Webhook 签名校验。

## 要求

- Python 3.8 及以上。
- 一个 StableOps API 密钥。
- 服务端环境。不要在浏览器代码中暴露 API 密钥。

## 安装

```bash
pip install stableops
```

## 快速开始

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

环境（沙盒或正式环境）由 API 密钥前缀（`sk_sandbox_…` / `sk_live_…`）决定。前端只接收
订单编号、金额和 `payment_instructions`，API 密钥始终留在你的服务端。

## 退款与支付链接

同步与异步客户端均提供 `refunds` 和 `payment_links`。退款支持创建、查询、分页列出、登记交易和取消。支付链接支持创建、分页列出、更新和查询关联订单。

```python
from stableops import AcceptedAssetInput, CreatePaymentLinkInput, UpdatePaymentLinkInput

refund = client.refunds.create(
    payment_order_id="po_123", amount="5.00",
    destination_address="0x0000000000000000000000000000000000000001",
)
# 商户使用自己的钱包完成签名与广播后，登记交易哈希。
client.refunds.submit(refund.id, tx_hash=merchant_signed_transaction_hash)

link = client.payment_links.create(CreatePaymentLinkInput(
    title="专业版套餐", amount="49.00",
    accepted_assets=[AcceptedAssetInput(chain="base-sepolia", asset="USDC")],
    payer_fields=["email", "reference"],
))
client.payment_links.update(link.id, UpdatePaymentLinkInput(description=None))
page = client.payment_links.orders(link.id, limit=20)
```

`list_page()` 返回 `items`、`has_more` 和 `total`。更新支付链接时，仅发送显式提供的字段，`None` 用于清空可空字段。退款请求不会直接转账，新资源的写操作不会自动重试。

Webhook 支持付款、退款、订阅、账单、代理审计和 Agent Payments 事件。本包包含 `py.typed`，安装后可供 mypy 等工具检查公开类型。

## 文档

完整的指南、配置、收银台会话、Webhook 校验与 API 参考，请查阅官网文档：

- 中文文档：https://stableops.dev/zh/docs/sdk/python-api-sdk
- 英文文档：https://stableops.dev/en/docs/sdk/python-api-sdk

## 支持的链与资产

- 链：Ethereum、Base、Arbitrum、Polygon、Optimism、BSC、TRON、Solana 及对应测试网。
- 资产：USDC、USDT。

## 许可证

本 SDK 使用 `Apache-2.0` 许可证，详见 [LICENSE](./LICENSE)。
