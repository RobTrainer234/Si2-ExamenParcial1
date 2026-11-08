from types import SimpleNamespace

import pytest


def test_exchange_return_is_quarantined_without_restock_or_return_movement():
    from app.modules.commerce import service

    inventory = SimpleNamespace(id=11, branch_id=8, product_variant_id=33, stock_quantity=7)
    exchange_item = SimpleNamespace(id=22, returned_quantity=2)
    user = SimpleNamespace(id=9, tenant_id=3)
    db = SimpleNamespace(added=[], flush=lambda: None, add=lambda value: db.added.append(value))

    quarantine = service.create_exchange_quarantine(db, exchange_item, inventory, user)

    assert inventory.stock_quantity == 7
    assert quarantine.status == "PENDING"
    assert quarantine.quantity == 2
    assert quarantine.inventory_id == 11
    assert not any(getattr(value, "movement_type", None) == "RETURN" for value in db.added)


def test_inspection_release_is_once_and_reject_never_restock():
    from app.modules.inventory import service

    quarantine = SimpleNamespace(
        id=5,
        tenant_id=3,
        branch_id=8,
        inventory_id=11,
        quantity=2,
        status="PENDING",
        inspected_by=None,
        inspection_reason=None,
        inspected_at=None,
    )
    inventory = SimpleNamespace(id=11, stock_quantity=7, reserved_quantity=0)
    user = SimpleNamespace(id=9, tenant_id=3)

    class DB:
        def __init__(self):
            self.added = []

        def add(self, value):
            self.added.append(value)

        def flush(self):
            return None

    db = DB()
    service.inspect_quarantine(db, quarantine, inventory, "RELEASE", "Passed inspection", user)
    assert quarantine.status == "RELEASED"
    assert inventory.stock_quantity == 9
    assert sum(getattr(value, "quantity", 0) for value in db.added if getattr(value, "movement_type", None) == "IN") == 2

    db = DB()
    quarantine.status = "PENDING"
    inventory.stock_quantity = 7
    service.inspect_quarantine(db, quarantine, inventory, "REJECT", "Damaged", user)
    assert quarantine.status == "REJECTED"
    assert inventory.stock_quantity == 7
    assert not any(getattr(value, "movement_type", None) == "IN" for value in db.added)


def test_opposite_terminal_inspection_conflicts():
    from app.modules.inventory import service

    quarantine = SimpleNamespace(status="RELEASED")
    with pytest.raises(Exception):
        service.inspect_quarantine(None, quarantine, None, "REJECT", "Damaged", SimpleNamespace(id=1, tenant_id=3))
