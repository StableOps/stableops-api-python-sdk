"""Tests for SDK response type contracts."""

from typing import get_args

from stableops.types import (
    AcceptedAssetInput,
    ChainId,
    PaymentOrder,
    PaymentOrderInstruction,
    PaymentOrderStatus,
)


def test_type_aliases_match_current_api_contract() -> None:
    """Public Literal aliases should expose the same enum values as the API."""
    assert "solana" in get_args(ChainId)
    assert "optimism" in get_args(ChainId)
    assert "bsc-testnet" in get_args(ChainId)
    assert "tron-nile" in get_args(ChainId)
    assert "created" in get_args(PaymentOrderStatus)
    assert "CREATED" not in get_args(PaymentOrderStatus)


def test_payment_order_accepts_current_api_wire_values() -> None:
    """Python SDK types should match values returned by the API."""
    order = PaymentOrder(
        id="po_123",
        merchant_order_id="merchant_123",
        amount="1000000",
        settlement_asset="USDC",
        status="created",
        expires_at=None,
        metadata=None,
        created_at="2026-05-31T00:00:00.000Z",
        accepted_assets=[AcceptedAssetInput(chain="solana-devnet", asset="USDC")],
        payment_instructions=[
            PaymentOrderInstruction(chain="solana-devnet", asset="USDC", address="RecipientWallet123")
        ],
    )

    assert order.status == "created"
    assert len(order.payment_instructions) == 1
    assert order.payment_instructions[0].chain == "solana-devnet"
