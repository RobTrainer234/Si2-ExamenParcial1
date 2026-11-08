from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Header, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.models import Devolucion, User
from app.modules.auth.dependencies import require_branch_access, require_permission
from app.modules.commerce import qr_service, service, stripe_service
from app.modules.commerce.schemas import (
    CartItemRequest,
    CartItemUpdateRequest,
    CartResponse,
    CashPaymentRequest,
    CreditNoteLookupRequest,
    CreditNoteLookupResponse,
    CreditNoteSettlementRequest,
    CreditNoteSettlementResponse,
    ExchangeLookupResponse,
    ReturnLookupResponse,
    ExchangeQuoteRequest,
    ExchangeQuoteResponse,
    DigitalPurchaseRequest,
    ElectronicNotificationRequest,
    ElectronicPaymentRequest,
    ItemExchangeRequest,
    ItemExchangeResponse,
    PaymentResponse,
    PhysicalSaleRequest,
    PurchaseHistoryPage,
    QRPaymentGenerateRequest,
    QRPaymentResponse,
    QRPaymentSimulateRequest,
    QRPaymentStatusResponse,
    QRTransferConfirmRequest,
    SaleResponse,
    SaleReturnRequest,
    SaleReturnResponse,
    StripePaymentConfirmRequest,
    StripePaymentIntentRequest,
    StripePaymentIntentResponse,
)


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


@router.post("/credit-notes/lookup", response_model=CreditNoteLookupResponse)
def lookup_credit_note(data: CreditNoteLookupRequest, current_user: CashPaymentUser, db=Depends(get_db)):
    require_branch_access(current_user, data.branch_id)
    return service.lookup_credit_note(db, data, current_user)


@router.post("/sales/{sale_id}/credit-note-settlement", response_model=CreditNoteSettlementResponse)
def credit_note_settlement(sale_id: int, data: CreditNoteSettlementRequest, current_user: CashPaymentUser, db=Depends(get_db)):
    try:
        sale = service.get_sale(db, sale_id)
        if sale.branch_id is None:
            raise service.error("SALE_BRANCH_REQUIRED", "La venta no tiene sucursal.")
        require_branch_access(current_user, sale.branch_id)
        result = service.settle_credit_note(db, sale_id, data, current_user)
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise


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
def electronic_notification(data: ElectronicNotificationRequest, db=Depends(get_db), x_sandbox_signature: str | None = Header(default=None)):
    if x_sandbox_signature != settings.sandbox_payment_webhook_secret:
        raise service.error("INVALID_PAYMENT_NOTIFICATION_SIGNATURE", "La notificación de pago no está autenticada.", status.HTTP_401_UNAUTHORIZED)
    payment = service.process_electronic_notification(db, data)
    db.commit()
    return service.serialize_payment(payment)


@router.post("/payments/stripe/intent", response_model=StripePaymentIntentResponse, status_code=status.HTTP_201_CREATED)
def create_stripe_intent(data: StripePaymentIntentRequest, current_user: ElectronicPayer, db=Depends(get_db)):
    result = stripe_service.create_payment_intent(db, data, current_user)
    db.commit()
    return result


@router.post("/payments/stripe/confirm", response_model=SaleResponse)
def confirm_stripe_payment(data: StripePaymentConfirmRequest, current_user: ElectronicPayer, db=Depends(get_db)):
    sale = stripe_service.confirm_stripe_payment(db, data.payment_intent_id, current_user)
    db.commit()
    return service.serialize_sale(sale)


@router.post("/payments/stripe/webhook")
async def stripe_webhook(request: Request, db=Depends(get_db), stripe_signature: str | None = Header(default=None, alias="stripe-signature")):
    payload = await request.body()
    return stripe_service.handle_stripe_webhook(db, payload, stripe_signature)


@router.post("/payments/qr/generate", response_model=QRPaymentResponse, status_code=status.HTTP_201_CREATED)
def generate_qr_payment(data: QRPaymentGenerateRequest, current_user: ElectronicPayer, db=Depends(get_db)):
    result = qr_service.generate_qr_payment(db, data.sale_id, current_user, data.client_base_url)
    db.commit()
    return result


@router.get("/payments/qr/status/{transaction_reference}", response_model=QRPaymentStatusResponse)
def get_qr_payment_status(transaction_reference: str, db=Depends(get_db)):
    return qr_service.check_qr_payment_status(db, transaction_reference)


@router.post("/payments/qr/confirm-transfer", response_model=SaleResponse)
def confirm_qr_transfer(data: QRTransferConfirmRequest, db=Depends(get_db)):
    sale = qr_service.confirm_qr_transfer(db, data.transaction_reference, data.amount)
    db.commit()
    return service.serialize_sale(sale)


@router.post("/payments/qr/simulate", response_model=SaleResponse)
def simulate_qr_payment(data: QRPaymentSimulateRequest, current_user: ElectronicPayer, db=Depends(get_db)):
    sale = qr_service.simulate_or_confirm_qr_payment(db, data.transaction_reference, data.amount, current_user)
    db.commit()
    return service.serialize_sale(sale)


@router.get("/purchases/mine", response_model=PurchaseHistoryPage)
def purchase_history(current_user: User = Depends(require_permission("sales.read")), page: int = 1, page_size: int = 20, db=Depends(get_db)):
    return service.list_customer_purchases(db, current_user.id, page, min(page_size, 100))


@router.get("/purchases/mine/{sale_id}", response_model=SaleResponse)
def purchase_detail(sale_id: int, current_user: User = Depends(require_permission("sales.read")), db=Depends(get_db)):
    return service.serialize_sale(service.get_customer_purchase(db, current_user.id, sale_id))


@router.get("/returns/lookup/{order_number}", response_model=ReturnLookupResponse)
def lookup_return_sale(order_number: str, current_user: User = Depends(require_permission("sales.read")), db=Depends(get_db)):
    return service.lookup_return_sale(db, order_number, current_user)


@router.get("/sales/lookup/{order_number}", response_model=ExchangeLookupResponse)
def lookup_exchange_sale(order_number: str, current_user: User = Depends(require_permission("sales.read")), db=Depends(get_db)):
    return service.lookup_exchange_sale(db, order_number, current_user)


@router.post("/sales/{sale_id}/exchange/quote", response_model=ExchangeQuoteResponse)
def exchange_quote(sale_id: int, data: ExchangeQuoteRequest, current_user: User = Depends(require_permission("sales.create")), db=Depends(get_db)):
    result = service.create_exchange_quote(db, sale_id, data, current_user)
    return result


@router.get("/sales/{sale_id}", response_model=SaleResponse)
def get_sale(sale_id: int, current_user: User = Depends(require_permission("sales.read")), db=Depends(get_db)):
    sale = service.get_sale(db, sale_id)
    if current_user.role.code == "CLIENT" and sale.customer_id != current_user.id:
        raise service.error("SALE_FORBIDDEN", "No puedes consultar esta venta.", status.HTTP_403_FORBIDDEN)
    if current_user.role.code != "ADMIN" and sale.branch_id is not None and current_user.role.code != "CLIENT":
        require_branch_access(current_user, sale.branch_id)
    return service.serialize_sale(sale)


@router.get("/returns/customers", response_model=list[dict[str, object]])
def lookup_return_customers(current_user: User = Depends(require_permission("sales.read")), db=Depends(get_db), q: str = ""):
    statement = select(User).where(User.tenant_id == current_user.tenant_id, User.role.has(code="CLIENT"), User.is_active.is_(True))
    if q.strip():
        term = f"%{q.strip()}%"
        statement = statement.where((User.first_name.ilike(term)) | (User.last_name.ilike(term)) | (User.email.ilike(term)))
    return [{"id": item.id, "first_name": item.first_name, "last_name": item.last_name, "email": item.email} for item in db.scalars(statement.order_by(User.last_name, User.first_name).limit(20)).all()]


@router.post("/sales/{sale_id}/return", response_model=SaleReturnResponse)
def return_sale(
    sale_id: int,
    data: SaleReturnRequest,
    current_user: User = Depends(require_permission("sales.create")),
    db=Depends(get_db),
):
    sale = service.get_sale(db, sale_id)
    if sale.branch_id is not None and current_user.role.code != "ADMIN":
        require_branch_access(current_user, sale.branch_id)
    try:
        result = service.process_sale_return(db, sale_id, data, current_user)
        db.commit()
    except Exception:
        db.rollback()
        raise
    response = service.serialize_sale(result)
    ledger = db.scalar(select(Devolucion).where(Devolucion.tenant_id == current_user.tenant_id, Devolucion.venta_id == sale_id, Devolucion.idempotency_key == data.idempotency_key))
    if ledger is None:
        raise service.error("RETURN_NOT_FOUND", "No se encontró el registro de devolución.", status.HTTP_409_CONFLICT)
    response["credit_note_code"] = ledger.codigo_nota_credito
    response["return_id"] = ledger.id
    response["credit_note_amount"] = ledger.total_devuelto
    return response


@router.post("/sales/{sale_id}/exchange", response_model=ItemExchangeResponse)
def exchange_sale(
    sale_id: int,
    data: ItemExchangeRequest,
    current_user: User = Depends(require_permission("sales.create")),
    db=Depends(get_db),
):
    sale = service.get_sale(db, sale_id)
    if sale.branch_id is not None and current_user.role.code != "ADMIN":
        require_branch_access(current_user, sale.branch_id)
    result = service.exchange_sale_item(db, sale_id, data, current_user)
    db.commit()
    return result



_SCANNER_RELAY_QUEUE: dict[tuple[int, int], list[dict[str, str]]] = {}


@router.post("/scanner-relay")
def push_scanner_relay(
    payload: dict[str, object],
    current_user: User = Depends(require_permission("sales.create")),
):
    branch_id = int(payload.get("branch_id") or 0)
    barcode = str(payload.get("barcode") or "").strip()
    if not barcode or branch_id <= 0:
        return {"queued": False}
    key = (int(current_user.tenant_id or 0), branch_id)
    queue = _SCANNER_RELAY_QUEUE.setdefault(key, [])
    queue.append({"barcode": barcode})
    if len(queue) > 30:
        del queue[:-30]
    return {"queued": True, "barcode": barcode}


@router.get("/scanner-relay")
def pop_scanner_relay(
    branch_id: int = 0,
    current_user: User = Depends(require_permission("sales.create")),
):
    if branch_id <= 0:
        return {"items": []}
    key = (int(current_user.tenant_id or 0), branch_id)
    items = _SCANNER_RELAY_QUEUE.pop(key, [])
    return {"items": items}


@router.get("/barcode-svg")
def get_barcode_svg(text: str = "SKU-001", format: str = "qr"):
    from fastapi.responses import Response
    try:
        import zxingcpp
    except ImportError:
        zxingcpp = None

    clean = text.strip() or "SKU-001"
    if zxingcpp:
        try:
            if format.lower() in ("code128", "barcode", "1d"):
                bc = zxingcpp.create_barcode(clean, zxingcpp.BarcodeFormat.Code128)
            else:
                bc = zxingcpp.create_barcode(clean, zxingcpp.BarcodeFormat.QRCode)
            svg_data = zxingcpp.write_barcode_to_svg(bc)
            return Response(content=svg_data, media_type="image/svg+xml")
        except Exception:
            pass

    fallback_svg = f'<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><text x="10" y="50" font-size="12">{clean}</text></svg>'
    return Response(content=fallback_svg, media_type="image/svg+xml")



@router.post("/scan-image")
async def scan_image(
    file: UploadFile = File(...),
    branch_id: int = Form(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("sales.create")),
):
    import io
    from PIL import Image
    from app.core.models import ProductVariant
    from app.modules.commerce.barcode_pipeline import decode_barcode_robust

    contents = await file.read()
    if not contents:
        return {"success": False, "error": "No se recibió ninguna imagen."}

    try:
        img = Image.open(io.BytesIO(contents))
    except Exception as e:
        return {"success": False, "error": f"Formato de imagen inválido: {str(e)}"}

    # Fetch active skus for OCR/fuzzy matching
    try:
        active_skus = [
            r[0] for r in db.query(ProductVariant.sku).filter(ProductVariant.is_active == True).all()
            if r[0]
        ]
    except Exception:
        active_skus = []

    detected_code, barcode_format = decode_barcode_robust(img, active_skus)

    if not detected_code:
        return {
            "success": False,
            "error": "No se detectó un código de barras o texto legible en la foto. Enfoca más cerca y con buena iluminación.",
        }

    # If branch_id > 0, enqueue to relay queue so the PC POS picks it up automatically
    if branch_id > 0:
        key = (int(current_user.tenant_id or 0), branch_id)
        queue = _SCANNER_RELAY_QUEUE.setdefault(key, [])
        queue.append({"barcode": detected_code})
        if len(queue) > 30:
            del queue[:-30]

    return {
        "success": True,
        "barcode": detected_code,
        "format": barcode_format,
        "queued": branch_id > 0,
    }

