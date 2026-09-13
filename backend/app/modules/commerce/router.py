from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.database import get_db
from app.core.models import User
from app.modules.auth.dependencies import require_branch_access, require_permission
from app.modules.commerce import service
from app.modules.commerce.schemas import CartItemRequest, CartItemUpdateRequest, CartResponse, CashPaymentRequest, DigitalPurchaseRequest, ElectronicNotificationRequest, ElectronicPaymentRequest, PaymentResponse, PhysicalSaleRequest, SaleResponse


router = APIRouter(tags=["commerce"])
Client = Annotated[User, Depends(require_permission("cart.manage"))]
Cashier = Annotated[User, Depends(require_permission("sales.create"))]
CashPaymentUser = Annotated[User, Depends(require_permission("payments.cash"))]
ElectronicPayer = Annotated[User, Depends(require_permission("payments.electronic"))]


@router.get("/cart", response_model=CartResponse)
def get_cart(current_user: Client, db=Depends(get_db)):
    return service.serialize_cart(service.get_cart(db, current_user.id), db)


@router.post("/cart/items", response_model=CartResponse)
def add_cart_item(data: CartItemRequest, current_user: Client, db=Depends(get_db)):
    result = service.add_cart_item(db, current_user.id, data)
    db.commit()
    return service.serialize_cart(result, db)


@router.patch("/cart/items/{item_id}", response_model=CartResponse)
def update_cart_item(item_id: int, data: CartItemUpdateRequest, current_user: Client, db=Depends(get_db)):
    result = service.update_cart_item(db, current_user.id, item_id, data)
    db.commit()
    return service.serialize_cart(result, db)


@router.delete("/cart/items/{item_id}", response_model=CartResponse)
def remove_cart_item(item_id: int, current_user: Client, db=Depends(get_db)):
    result = service.remove_cart_item(db, current_user.id, item_id)
    db.commit()
    return service.serialize_cart(result, db)


@router.delete("/cart", response_model=CartResponse)
def clear_cart(current_user: Client, db=Depends(get_db)):
    result = service.clear_cart(db, current_user.id)
    db.commit()
    return service.serialize_cart(result, db)


@router.post("/sales/physical", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def create_physical_sale(data: PhysicalSaleRequest, current_user: Cashier, db=Depends(get_db)):
    require_branch_access(current_user, data.branch_id)
    result = service.create_physical_sale(db, data, current_user)
    db.commit()
    return service.serialize_sale(result)


@router.post("/sales/{sale_id}/cash-payment", response_model=SaleResponse)
def cash_payment(sale_id: int, data: CashPaymentRequest, current_user: CashPaymentUser, db=Depends(get_db)):
    sale = service.get_sale(db, sale_id)
    if sale.branch_id is None:
        raise service.error("SALE_BRANCH_REQUIRED", "La venta no tiene sucursal.")
    require_branch_access(current_user, sale.branch_id)
    result = service.process_cash_payment(db, sale, data, current_user)
    db.commit()
    return service.serialize_sale(result)


@router.post("/purchases/digital", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def create_digital_purchase(data: DigitalPurchaseRequest, current_user: ElectronicPayer, db=Depends(get_db)):
    result = service.create_digital_purchase(db, data, current_user)
    db.commit()
    return service.serialize_sale(result)


@router.post("/payments/electronic", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def electronic_payment(data: ElectronicPaymentRequest, _: ElectronicPayer, db=Depends(get_db)):
    payment = service.initiate_electronic_payment(db, data)
    db.commit()
    return service.serialize_payment(payment)


@router.post("/payments/electronic/notification", response_model=PaymentResponse)
def electronic_notification(data: ElectronicNotificationRequest, db=Depends(get_db)):
    payment = service.process_electronic_notification(db, data)
    db.commit()
    return service.serialize_payment(payment)


@router.get("/sales/{sale_id}", response_model=SaleResponse)
def get_sale(sale_id: int, current_user: User = Depends(require_permission("sales.read")), db=Depends(get_db)):
    sale = service.get_sale(db, sale_id)
    if current_user.role.code == "CLIENT" and sale.customer_id != current_user.id:
        raise service.error("SALE_FORBIDDEN", "No puedes consultar esta venta.", status.HTTP_403_FORBIDDEN)
    if current_user.role.code != "ADMIN" and sale.branch_id is not None and current_user.role.code != "CLIENT":
        require_branch_access(current_user, sale.branch_id)
    return service.serialize_sale(sale)
