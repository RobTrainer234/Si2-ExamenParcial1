from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest


def test_exchange_request_requires_server_quote_binding():
    from app.modules.commerce.schemas import ItemExchangeRequest

    with pytest.raises(Exception):
        ItemExchangeRequest(
            returned_variant_id=1,
            new_variant_id=2,
            idempotency_key="exchange-quote-1",
        )

    request = ItemExchangeRequest(
        returned_variant_id=1,
        new_variant_id=2,
        idempotency_key="exchange-quote-1",
        quote_fingerprint="a" * 64,
        quote_expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    assert request.quote_fingerprint == "a" * 64


def test_quote_binding_includes_all_mutable_pricing_inventory_and_tender_inputs():
    from app.modules.commerce import service

    user = SimpleNamespace(tenant_id=7)
    sale = SimpleNamespace(id=11, branch_id=3)
    item = SimpleNamespace(id=19, product_variant_id=101, quantity=3, line_total=Decimal("120.00"))
    expires_at = datetime(2026, 1, 1, tzinfo=UTC)
    binding = service._quote_binding(
        current_user=user,
        sale=sale,
        sale_item=item,
        returned_quantity=1,
        new_variant_id=202,
        new_quantity=2,
        consumed=1,
        replacement_price=Decimal("80.00"),
        available_stock=4,
        reserved_stock=1,
        cash_settlement_eligible=True,
        quote_expires_at=expires_at,
    )

    assert binding == {
        "tenant_id": 7,
        "branch_id": 3,
        "sale_id": 11,
        "sale_item_id": 19,
        "source_variant_id": 101,
        "returned_quantity": 1,
        "purchased_quantity": 3,
        "consumed_exchange_quantity": 1,
        "source_paid_line_total": "120.00",
        "replacement_variant_id": 202,
        "replacement_quantity": 2,
        "replacement_catalog_price": "80.00",
        "available_stock": 4,
        "reserved_stock": 1,
        "cash_settlement_eligible": True,
        "quote_expires_at": "2026-01-01T00:00:00+00:00",
    }


def test_exchange_quote_signature_changes_when_stock_price_or_quantity_changes():
    from app.modules.commerce import service

    base = dict(
        tenant_id=7,
        branch_id=3,
        sale_id=11,
        sale_item_id=19,
        source_variant_id=101,
        returned_quantity=1,
        purchased_quantity=3,
        consumed=0,
        source_paid_line_total="120.00",
        new_variant_id=202,
        new_quantity=1,
        replacement_price=Decimal("80.00"),
        available_stock=4,
        reserved_stock=0,
        cash_settlement_eligible=True,
    )
    user = SimpleNamespace(tenant_id=7)
    sale = SimpleNamespace(id=11, branch_id=3)
    item = SimpleNamespace(id=19, product_variant_id=101, quantity=3, line_total=Decimal("120.00"))

    expires_at = datetime(2026, 1, 1, tzinfo=UTC)
    first = service._sign_quote(service._quote_binding(current_user=user, sale=sale, sale_item=item, returned_quantity=base["returned_quantity"], new_variant_id=base["new_variant_id"], new_quantity=base["new_quantity"], consumed=base["consumed"], replacement_price=base["replacement_price"], available_stock=base["available_stock"], reserved_stock=base["reserved_stock"], cash_settlement_eligible=True, quote_expires_at=expires_at))
    changed = service._quote_binding(current_user=user, sale=sale, sale_item=item, returned_quantity=1, new_variant_id=202, new_quantity=1, consumed=0, replacement_price=Decimal("81.00"), available_stock=4, reserved_stock=0, cash_settlement_eligible=True, quote_expires_at=expires_at)
    assert first != service._sign_quote(changed)

    changed_expiry = service._quote_binding(current_user=user, sale=sale, sale_item=item, returned_quantity=1, new_variant_id=202, new_quantity=1, consumed=0, replacement_price=Decimal("80.00"), available_stock=4, reserved_stock=0, cash_settlement_eligible=True, quote_expires_at=datetime(2026, 1, 1, 0, 5, tzinfo=UTC))
    assert first != service._sign_quote(changed_expiry)
