from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.models import Branch, Category, Product, Promotion
from app.modules.ai_chat.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    SuggestedAction,
    SuggestedProduct,
)

logger = logging.getLogger(__name__)

_OPENAI_URL = "https://api.openai.com/v1/chat/completions"
_TIMEOUT_SECONDS = 8.0


def _normalize(text: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return " ".join(cleaned.split())


def _primary_image(product: Product) -> str | None:
    if not product.images:
        return None
    images = sorted(product.images, key=lambda item: item.sort_order)
    primary = next((image for image in images if image.is_primary), None)
    return (primary or images[0]).image_url if images else None


def _get_active_catalog(db: Session) -> list[Product]:
    statement = (
        select(Product)
        .join(Category, Product.category_id == Category.id)
        .where(Product.is_active.is_(True), Category.is_active.is_(True))
        .options(selectinload(Product.category), selectinload(Product.images))
        .limit(30)
    )
    return db.scalars(statement).all()


def _get_active_promotions(db: Session) -> list[Promotion]:
    now = datetime.now(UTC)
    statement = select(Promotion).where(
        Promotion.is_active.is_(True),
        Promotion.starts_at <= now,
        Promotion.ends_at >= now,
    )
    return db.scalars(statement).all()


def _get_active_branches(db: Session) -> list[Branch]:
    statement = select(Branch).where(Branch.is_active.is_(True)).options(selectinload(Branch.city))
    return db.scalars(statement).all()


def _local_chat_response(
    db: Session, message: str, catalog: list[Product], promotions: list[Promotion], branches: list[Branch]
) -> ChatResponse:
    norm = _normalize(message)
    suggested_products: list[SuggestedProduct] = []
    suggested_actions: list[SuggestedAction] = []

    # 1. Intención: Reservas y Sucursales para prueba física
    if any(k in norm for k in ("reserva", "reservar", "apartar", "separar", "sucursal", "sucursales", "tienda", "tiendas", "horario", "direccion", "ubicacion")):
        branch_list = [f"• {b.name} ({b.city.name if b.city else 'Bolivia'}) - {b.address}" for b in branches]
        reply = (
            "Puedes reservar prendas en línea y acudir a probarlas en tu sucursal favorita sin costo alguno 🏬.\n"
            "Solo agrega las prendas a tu 'Bolsa de probador', selecciona fecha y sucursal, y nuestro equipo "
            "las tendrá listas en el probador esperándote.\n"
            "Nuestras sucursales disponibles son:\n" + ("\n".join(branch_list) if branch_list else "Consulta nuestras sucursales activas en la plataforma.")
        )
        suggested_actions.append(SuggestedAction(label="Bolsa de probador", action_type="navigate", payload={"url": "/fitting-bag"}))
        suggested_actions.append(SuggestedAction(label="Mis reservas", action_type="navigate", payload={"url": "/my-reservations"}))
        return ChatResponse(reply=reply, suggested_products=[], suggested_actions=suggested_actions, provider="local")

    # 2. Intención: Vestidor Virtual / Realidad Aumentada
    if any(k in norm for k in ("vestidor", "realidad aumentada", "ar", "camara", "probar virtual", "probador virtual", "pose")):
        reply = (
            "¡En FashionStore contamos con un Vestidor Virtual con Realidad Aumentada! 👗✨ "
            "Puedes usar la cámara de tu dispositivo móvil para que nuestra IA detecte tu postura y "
            "superponga la prenda seleccionada sobre ti, o usar nuestro simulador interactivo en web. "
            "Elige cualquier prenda del catálogo y pulsa 'Probar en vestidor'."
        )
        for prod in catalog[:3]:
            suggested_products.append(
                SuggestedProduct(
                    id=prod.id,
                    name=prod.name,
                    category_name=prod.category.name,
                    price=float(prod.price),
                    image_url=_primary_image(prod),
                    slug=prod.slug,
                )
            )
        suggested_actions.append(SuggestedAction(label="Ir al Catálogo", action_type="navigate", payload={"url": "/catalog"}))
        return ChatResponse(reply=reply, suggested_products=suggested_products, suggested_actions=suggested_actions, provider="local")

    # 2. Intención: Promociones y Descuentos
    if any(k in norm for k in ("promo", "promocion", "promociones", "descuento", "descuentos", "oferta", "ofertas")):
        if promotions:
            promo_texts = [f"• {p.name}: {p.discount_value}% de descuento" if p.discount_type == "PERCENT" else f"• {p.name}: BOB {p.discount_value} de descuento" for p in promotions]
            reply = (
                "¡Tenemos excelentes promociones activas para ti! 🎉\n"
                + "\n".join(promo_texts)
                + "\nLos descuentos se aplican automáticamente en tu carrito y al momento de pagar."
            )
        else:
            reply = "Actualmente nuestros precios de temporada están vigentes con la mejor relación calidad-precio. ¡Explora nuestras colecciones recién llegadas!"
        
        for prod in catalog[:3]:
            suggested_products.append(
                SuggestedProduct(
                    id=prod.id,
                    name=prod.name,
                    category_name=prod.category.name,
                    price=float(prod.price),
                    image_url=_primary_image(prod),
                    slug=prod.slug,
                )
            )
        suggested_actions.append(SuggestedAction(label="Ver Promociones", action_type="navigate", payload={"url": "/catalog"}))
        return ChatResponse(reply=reply, suggested_products=suggested_products, suggested_actions=suggested_actions, provider="local")

    # 3. Intención: Búsqueda / Recomendación de Prendas
    matched: list[Product] = []
    keywords = [w for w in norm.split() if len(w) > 3]
    for prod in catalog:
        prod_text = _normalize(f"{prod.name} {prod.category.name} {prod.description or ''}")
        if any(k in prod_text for k in keywords):
            matched.append(prod)

    if matched:
        reply = f"Encontré estas prendas en FashionStore que combinan perfecto con lo que buscas ({', '.join(keywords[:2])}):"
        for prod in matched[:4]:
            suggested_products.append(
                SuggestedProduct(
                    id=prod.id,
                    name=prod.name,
                    category_name=prod.category.name,
                    price=float(prod.price),
                    image_url=_primary_image(prod),
                    slug=prod.slug,
                )
            )
        suggested_actions.append(SuggestedAction(label="Explorar Catálogo", action_type="navigate", payload={"url": "/catalog"}))
        return ChatResponse(reply=reply, suggested_products=suggested_products, suggested_actions=suggested_actions, provider="local")

    # 5. Saludo o Consulta General
    greeting_tokens = ("hola", "buenos", "buenas", "que tal", "asesor", "ayuda", "sofia", "recomendame", "recomienda")
    if any(k in norm for k in greeting_tokens) or len(norm) < 10:
        reply = (
            "¡Hola! Soy Sofía, tu asistente de moda inteligente en FashionStore 👗✨. "
            "Puedo recomendarte prendas según tu estilo u ocasión, mostrarte cómo usar el Vestidor Virtual con Realidad Aumentada, "
            "informarte sobre nuestras promociones vigentes o ayudarte a reservar prendas para probarte en cualquiera de nuestras sucursales. "
            "¿Qué estás buscando hoy?"
        )
    else:
        reply = (
            "Entiendo tu consulta. En FashionStore tenemos una amplia variedad de prendas de temporada, "
            "disponibles para compra digital con entrega o retiro, y reserva para prueba en probadores físicos. "
            "Aquí te presento algunas de nuestras opciones más populares:"
        )

    for prod in catalog[:3]:
        suggested_products.append(
            SuggestedProduct(
                id=prod.id,
                name=prod.name,
                category_name=prod.category.name,
                price=float(prod.price),
                image_url=_primary_image(prod),
                slug=prod.slug,
            )
        )
    suggested_actions.append(SuggestedAction(label="Ver Catálogo Completo", action_type="navigate", payload={"url": "/catalog"}))
    return ChatResponse(reply=reply, suggested_products=suggested_products, suggested_actions=suggested_actions, provider="local")


def _call_gemini(system_prompt: str, history: list[ChatMessage], message: str) -> str | None:
    if not settings.gemini_api_key:
        return None
    models_to_try = [settings.gemini_model]
    if "gemini-flash-latest" not in models_to_try:
        models_to_try.append("gemini-flash-latest")

    contents = []
    for h in history[-4:]:
        role = "user" if h.role == "user" else "model"
        contents.append({"role": role, "parts": [{"text": h.content}]})
    contents.append({"role": "user", "parts": [{"text": message}]})

    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 500,
        },
    }
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={settings.gemini_api_key}"
        try:
            with httpx.Client(timeout=_TIMEOUT_SECONDS) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
                elif res.status_code == 404:
                    continue
                else:
                    logger.info("Gemini call for %s returned %s: %s", model_name, res.status_code, res.text[:120])
                    break
        except Exception as exc:
            logger.info("Gemini chat call failed: %s", exc)
            break
    return None


def process_chat(db: Session, request: ChatRequest) -> ChatResponse:
    catalog = _get_active_catalog(db)
    promotions = _get_active_promotions(db)
    branches = _get_active_branches(db)

    # Preparar contexto para modelos LLM (Gemini / OpenAI)
    catalog_summary = [
        f"ID {p.id}: {p.name} (Categoría: {p.category.name}, Precio: BOB {p.price})"
        for p in catalog[:15]
    ]
    promotions_summary = [f"{p.name} ({p.discount_type}: {p.discount_value})" for p in promotions]
    branches_summary = [f"{b.name} en {b.city.name if b.city else 'Bolivia'}" for b in branches]

    system_prompt = (
        "Eres Sofía, la asistente virtual inteligente de comercio electrónico de FashionStore Atelier. "
        "Responde de forma amable, concisa y elegante en español (máximo 3 párrafos). "
        "FashionStore ofrece: catálogo de ropa exclusiva, vestidor virtual con realidad aumentada (cámara del móvil), "
        "reserva de prendas para prueba física en sucursales, compra digital con Simple QR / Tarjeta y compras presenciales en caja.\n\n"
        f"Catálogo actual: {'; '.join(catalog_summary)}\n"
        f"Promociones activas: {'; '.join(promotions_summary) if promotions_summary else 'Ninguna activa'}\n"
        f"Sucursales: {'; '.join(branches_summary)}\n\n"
        "Si recomiendas productos del catálogo, menciona su nombre exacto para que el cliente pueda identificarlos."
    )

    # 1. Prioridad: Google Gemini si está configurado
    if settings.gemini_api_key:
        gemini_reply = _call_gemini(system_prompt, request.history, request.message)
        if gemini_reply:
            suggested: list[SuggestedProduct] = []
            for p in catalog:
                if p.name.lower() in gemini_reply.lower() or p.name.lower() in request.message.lower():
                    suggested.append(
                        SuggestedProduct(
                            id=p.id,
                            name=p.name,
                            category_name=p.category.name,
                            price=float(p.price),
                            image_url=_primary_image(p),
                            slug=p.slug,
                        )
                    )
            if not suggested:
                for p in catalog[:2]:
                    suggested.append(
                        SuggestedProduct(
                            id=p.id,
                            name=p.name,
                            category_name=p.category.name,
                            price=float(p.price),
                            image_url=_primary_image(p),
                            slug=p.slug,
                        )
                    )
            return ChatResponse(
                reply=gemini_reply,
                suggested_products=suggested[:4],
                suggested_actions=[SuggestedAction(label="Ver en catálogo", action_type="navigate", payload={"url": "/catalog"})],
                provider="gemini",
            )

    # 2. Alternativa: OpenAI si está configurado
    if settings.openai_api_key:
        try:
            messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
            for h in request.history[-4:]:
                messages.append({"role": h.role, "content": h.content})
            messages.append({"role": "user", "content": request.message})

            headers = {
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": settings.openai_model,
                "messages": messages,
                "max_tokens": 400,
                "temperature": 0.7,
            }
            with httpx.Client(timeout=_TIMEOUT_SECONDS) as client:
                res = client.post(_OPENAI_URL, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    reply_text = data["choices"][0]["message"]["content"].strip()
                    
                    suggested = []
                    for p in catalog:
                        if p.name.lower() in reply_text.lower() or p.name.lower() in request.message.lower():
                            suggested.append(
                                SuggestedProduct(
                                    id=p.id,
                                    name=p.name,
                                    category_name=p.category.name,
                                    price=float(p.price),
                                    image_url=_primary_image(p),
                                    slug=p.slug,
                                )
                            )
                    if not suggested:
                        for p in catalog[:2]:
                            suggested.append(
                                SuggestedProduct(
                                    id=p.id,
                                    name=p.name,
                                    category_name=p.category.name,
                                    price=float(p.price),
                                    image_url=_primary_image(p),
                                    slug=p.slug,
                                )
                            )

                    return ChatResponse(
                        reply=reply_text,
                        suggested_products=suggested[:4],
                        suggested_actions=[SuggestedAction(label="Ver en catálogo", action_type="navigate", payload={"url": "/catalog"})],
                        provider="openai",
                    )
        except Exception as exc:
            logger.info("OpenAI chat assistant fallback triggered: %s", exc)

    # 3. Fallback Determinista Local Inteligente
    return _local_chat_response(db, request.message, catalog, promotions, branches)

