import json
import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.models import AIRecommendation, Category, Collection, Inventory, Product, ProductVariant, Sale, SaleItem, Season, User

logger = logging.getLogger(__name__)


def _visible_products_statement():
    today = datetime.now(UTC).date()
    current_season = or_(Season.id.is_(None), and_(Season.is_active.is_(True), Season.starts_on.is_(None) | (Season.starts_on <= today), Season.ends_on.is_(None) | (Season.ends_on >= today)))
    current_collection = or_(Collection.id.is_(None), Collection.is_active.is_(True))
    available = select(ProductVariant.product_id).join(Inventory, Inventory.product_variant_id == ProductVariant.id).where(ProductVariant.is_active.is_(True), Inventory.stock_quantity - Inventory.reserved_quantity > 0).distinct()
    return select(Product).join(Category, Product.category_id == Category.id).outerjoin(Season, Product.season_id == Season.id).outerjoin(Collection, Product.collection_id == Collection.id).where(Product.is_active.is_(True), Category.is_active.is_(True), current_season, current_collection, Product.id.in_(available)).options(selectinload(Product.category), selectinload(Product.images))


def _primary_image(product: Product) -> str | None:
    images = sorted(product.images, key=lambda item: item.sort_order)
    primary = next((image for image in images if image.is_primary), None)
    return (primary or images[0]).image_url if images else None


def _customer_category_affinity(db: Session, user_id: int) -> set[int]:
    rows = db.execute(select(Product.category_id).join(ProductVariant, Product.id == ProductVariant.product_id).join(SaleItem, SaleItem.product_variant_id == ProductVariant.id).join(Sale, SaleItem.sale_id == Sale.id).where(Sale.customer_id == user_id, Sale.status == "CONFIRMED").group_by(Product.category_id).order_by(func.count(SaleItem.id).desc()).limit(5)).all()
    return {row[0] for row in rows}


def _purchased_product_ids(db: Session, user_id: int) -> set[int]:
    return set(db.scalars(select(Product.id).join(ProductVariant, Product.id == ProductVariant.product_id).join(SaleItem, SaleItem.product_variant_id == ProductVariant.id).join(Sale, SaleItem.sale_id == Sale.id).where(Sale.customer_id == user_id)).all())


def _popular_counts(db: Session) -> dict[int, int]:
    return dict(db.execute(select(Product.id, func.coalesce(func.sum(SaleItem.quantity), 0)).join(ProductVariant, Product.id == ProductVariant.product_id).join(SaleItem, SaleItem.product_variant_id == ProductVariant.id).join(Sale, SaleItem.sale_id == Sale.id).where(Sale.status == "CONFIRMED").group_by(Product.id)).all())


def _gemini_enrich_reasons(items: list[tuple[Decimal, str, Product]], affinities: list[str]) -> dict[int, str]:
    if not settings.gemini_api_key or not items:
        return {}
    models_to_try = [settings.gemini_model]
    if "gemini-flash-latest" not in models_to_try:
        models_to_try.append("gemini-flash-latest")

    prod_lines = [f"ID {p.id}: '{p.name}' ({p.category.name})" for _, _, p in items]
    affinity_str = f"Categorías preferidas del cliente: {', '.join(affinities)}." if affinities else "Cliente nuevo buscando prendas destacadas."
    system_prompt = (
        "Eres el personal stylist de alta costura de FashionStore Atelier. "
        "Para cada prenda sugerida al cliente, redacta una justificación de estilo atractiva y concisa (máximo 15 palabras) "
        "en español elegante explicando por qué le conviene vestirla o combinarla. "
        "Devuelve exclusivamente un JSON con formato: {\"<id_producto>\": \"justificación\"}."
    )
    user_prompt = f"{affinity_str}\nPrendas a justificar:\n" + "\n".join(prod_lines)
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "responseMimeType": "application/json",
        },
    }
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={settings.gemini_api_key}"
        try:
            with httpx.Client(timeout=3.5) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            parsed = json.loads(parts[0].get("text", "{}"))
                            return {int(k): str(v) for k, v in parsed.items() if str(k).isdigit()}
                elif res.status_code == 404:
                    continue
                else:
                    break
        except Exception as exc:
            logger.info("Gemini recommendations enrichment fallback: %s", exc)
            break
    return {}


def recommend(db: Session, user: User, limit: int = 8) -> dict[str, object]:
    category_affinity = _customer_category_affinity(db, user.id)
    purchased = _purchased_product_ids(db, user.id)
    popularity = _popular_counts(db)
    products = db.scalars(_visible_products_statement()).all()
    scored: list[tuple[Decimal, str, Product]] = []
    for product in products:
        if product.id in purchased and len(products) > 1:
            continue
        score = Decimal("0.35")
        count = popularity.get(product.id, 0)
        has_affinity = product.category_id in category_affinity
        if has_affinity:
            score += Decimal("0.35")
        if count:
            score += min(Decimal("0.25"), Decimal(count) / Decimal("20"))
        if product.season_id is not None:
            score += Decimal("0.10")
        has_pop = bool(count)
        has_season = product.season_id is not None

        if has_affinity and has_pop:
            stylist_reason = f"Estilo recomendado: Coincide con tu preferencia en {product.category.name} y es una de las prendas con mayor tendencia esta temporada."
        elif has_affinity:
            stylist_reason = f"Selección para tu perfil: Armoniza con tus compras previas en la categoría {product.category.name}."
        elif has_pop and has_season:
            stylist_reason = "Colección destacada: Prenda de temporada actual con excelente valoración y alta demanda entre clientes."
        elif has_pop:
            stylist_reason = "Favorito de la tienda: Artículo popular de alta rotación con existencias disponibles para entrega inmediata."
        elif has_season:
            stylist_reason = "Temporada activa: Prenda seleccionada de nuestra colección vigente con disponibilidad confirmada."
        else:
            stylist_reason = "Disponibilidad garantizada: Prenda exclusiva disponible para reserva en probador o compra directa."

        scored.append((min(score, Decimal("0.9900")), stylist_reason, product))
    scored.sort(key=lambda item: item[0], reverse=True)

    top_candidates = scored[:limit]
    gemini_reasons = {}
    if settings.gemini_api_key and top_candidates:
        affinity_names = [p.category.name for _, _, p in scored if p.category_id in category_affinity]
        gemini_reasons = _gemini_enrich_reasons(top_candidates, list(set(affinity_names)))

    items = []
    expires_at = datetime.now(UTC) + timedelta(hours=6)
    for score, reason, product in top_candidates:
        final_reason = gemini_reasons.get(product.id, reason)
        source = "GEMINI_AI" if product.id in gemini_reasons else "RULE_BASED_SCORING"
        db.add(AIRecommendation(customer_id=user.id, product_id=product.id, source=source, reason=final_reason, score=score, context={"category_affinity": product.category_id in category_affinity}, expires_at=expires_at))
        items.append({"product_id": product.id, "product_name": product.name, "category_name": product.category.name, "price": product.price, "image_url": _primary_image(product), "score": score, "reason": final_reason})
    db.flush()
    return {"items": items}
