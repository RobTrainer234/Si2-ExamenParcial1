from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.modules.reports.schemas import ReportAssistantIntent, ReportAssistantIntentKind, ReportFilters

logger = logging.getLogger(__name__)

_ALLOWED_KINDS: set[ReportAssistantIntentKind] = {
    "dashboard",
    "top_products",
    "sales_by_branch",
    "inventory",
    "reservations",
    "revenue_by_category",
}
_OPENAI_URL = "https://api.openai.com/v1/responses"
_TIMEOUT_SECONDS = 8.0
_TRANSCRIPTION_TIMEOUT_SECONDS = 35.0


def local_intent(prompt: str, filters: ReportFilters) -> ReportAssistantIntent:
    normalized = _normalize(prompt)

    # --------------------------------------------------------------------------
    # MATRIZ DE PONDERACIÓN INTELIGENTE (SCORING ENGINE)
    # Permite clasificar con alta precisión consultas complejas y evita que
    # sustantivos genéricos como 'producto' bloqueen intenciones de stock o sedes.
    # --------------------------------------------------------------------------
    scores: dict[ReportAssistantIntentKind, int] = {
        "inventory": 0,
        "top_products": 0,
        "sales_by_branch": 0,
        "reservations": 0,
        "revenue_by_category": 0,
        "dashboard": 0,
    }

    # 1. Señales de Inventario / Stock / Reposición
    inv_strong = (
        "bajo stock", "stock bajo", "sin stock", "poco stock", "escaso stock",
        "stock critico", "alerta de stock", "reposicion", "reponer",
        "reabastecimiento", "reabastecer", "surtir", "agotado", "agotados",
        "agotada", "agotadas", "por agotarse", "quedan pocos", "inventario bajo"
    )
    inv_medium = ("stock", "inventario", "existencia", "existencias", "bodega", "almacen", "disponible", "disponibles")
    inv_weak = ("urgente", "critico", "quedan", "falta", "faltan")

    for phrase in inv_strong:
        if phrase in normalized:
            scores["inventory"] += 4
    for token in inv_medium:
        if token in normalized:
            scores["inventory"] += 2
    for token in inv_weak:
        if token in normalized and any(k in normalized for k in ("stock", "producto", "prend", "articul", "inventari")):
            scores["inventory"] += 1

    # 2. Señales de Productos Más Vendidos / Ranking
    top_strong = (
        "mas vendido", "mas vendidos", "mas vendida", "mas vendidas",
        "menos vendido", "menos vendidos", "producto estrella", "productos estrella",
        "prenda estrella", "prendas estrella", "top productos", "ranking de productos",
        "ranking productos", "producto lider", "articulos mas vendidos", "prendas mas vendidas"
    )
    top_medium = ("vendido", "vendidos", "vendida", "vendidas", "ranking", "top 5", "top 10", "populares", "preferidos", "mas pedido")

    for phrase in top_strong:
        if phrase in normalized:
            scores["top_products"] += 4
    for token in top_medium:
        if token in normalized:
            scores["top_products"] += 2
    if any(token in normalized for token in ("producto", "productos", "prenda", "prendas")) and any(s in normalized for s in ("vent", "demanda", "pedid", "compr")):
        scores["top_products"] += 1

    # 3. Señales de Sucursales / Sedes
    branch_strong = (
        "ventas por sucursal", "ventas por sede", "ventas por tienda",
        "que sucursal vendio", "sucursal estrella", "ranking de sucursales",
        "sucursal mas", "mejor sucursal"
    )
    branch_medium = ("sucursal", "sucursales", "sede", "sedes")

    for phrase in branch_strong:
        if phrase in normalized:
            scores["sales_by_branch"] += 4
    for token in branch_medium:
        if token in normalized:
            scores["sales_by_branch"] += 2

    # 4. Señales de Reservas
    res_strong = ("reserva", "reservas", "reservacion", "reservaciones", "probador", "vestidor", "apartado", "apartados")
    res_medium = ("pendientes de retiro", "atendidas", "canceladas", "expiradas")

    for token in res_strong:
        if token in normalized:
            scores["reservations"] += 3
    for token in res_medium:
        if token in normalized:
            scores["reservations"] += 2

    # 5. Señales de Dashboard / Balance General / Comparativas Multicanal
    dash_strong = (
        "dashboard", "tablero", "resumen ejecutivo", "balance general", "kpi", "kpis",
        "resumen de ingresos", "ticket promedio", "tienda fisica vs online", "canales de venta",
        "estado general", "vision global"
    )
    dash_medium = ("resumen", "general", "balance", "ingresos", "descuentos", "margen", "comparativa", "canales")

    for phrase in dash_strong:
        if phrase in normalized:
            scores["dashboard"] += 4
    for token in dash_medium:
        if token in normalized:
            scores["dashboard"] += 1

    # 6. Señales de Ingresos por Categoría / Familias / Colecciones
    cat_strong = (
        "por categoria", "por categorias", "ingresos por categoria",
        "categoria mas", "categorias lideres", "que categoria", "que categorias",
        "ventas por categoria", "recaudacion por categoria", "categoria con mayor",
        "categorias con mayor", "categoria que mas"
    )
    cat_medium = ("categoria", "categorias", "familia", "familias", "linea de ropa", "lineas de ropa", "coleccion")
    for phrase in cat_strong:
        if phrase in normalized:
            scores["revenue_by_category"] += 4
    for token in cat_medium:
        if token in normalized:
            scores["revenue_by_category"] += 2

    # Si la consulta combina sucursal Y producto estrella simultáneamente, el dashboard brinda la respuesta consolidada
    if scores["sales_by_branch"] > 0 and scores["top_products"] > 0:
        scores["dashboard"] += 5

    best_kind: ReportAssistantIntentKind = "dashboard"
    max_score = 0
    for kind_candidate, score in scores.items():
        if score > max_score:
            max_score = score
            best_kind = kind_candidate

    if max_score == 0:
        if any(token in normalized for token in ("producto", "productos", "prendas")):
            best_kind = "top_products"
        elif any(token in normalized for token in ("categoria", "categorias")):
            best_kind = "revenue_by_category"
        else:
            best_kind = "dashboard"

    # Determinación adaptativa del gráfico visual recomendado
    chart_type: Literal["bar", "line", "pie", "table", "kpi"] = "bar"
    if any(k in normalized for k in ("torta", "pie", "circular", "porcentaje", "distribucion")) or best_kind == "revenue_by_category":
        chart_type = "pie"
    elif best_kind == "top_products":
        chart_type = "bar" if not any(k in normalized for k in ("linea", "lineas", "tendencia", "evolucion")) else "line"
    elif any(k in normalized for k in ("linea", "lineas", "temporal", "evolucion", "tendencia", "historico")):
        chart_type = "line"
    elif any(k in normalized for k in ("tabla", "detalle", "listado")) or best_kind == "inventory":
        chart_type = "table"
    elif best_kind == "dashboard" or "kpi" in normalized or "resumen" in normalized:
        chart_type = "kpi"
    else:
        chart_type = "bar"

    reasoning_map: dict[ReportAssistantIntentKind, str] = {
        "inventory": "Detección de consulta sobre inventario, nivel de existencias y urgencia de reposición de stock.",
        "top_products": "Análisis de volumen de ventas por artículo, ranking de popularidad y prendas con mayor demanda.",
        "sales_by_branch": "Evaluación del rendimiento comercial, facturación y transacciones distribuidas por sucursal.",
        "reservations": "Auditoría del flujo operativo de reservas de probador/vestidor y sus estados de atención.",
        "revenue_by_category": "Análisis comparativo de ingresos generados y rentabilidad desagregada por categorías de producto.",
        "dashboard": "Consolidado integral multidimensional de métricas financieras, canales y KPIs comerciales.",
    }

    return ReportAssistantIntent(
        kind=best_kind,
        filters=filters,
        chart_type=chart_type,
        reasoning=reasoning_map.get(best_kind, "Interpretación analítica local de la solicitud en lenguaje natural."),
    )


def interpret_intent(prompt: str, filters: ReportFilters) -> tuple[ReportAssistantIntent, str, bool]:
    if settings.gemini_api_key:
        try:
            intent = _gemini_interpret_intent(prompt, filters)
            if intent and intent.kind in _ALLOWED_KINDS:
                intent.filters = _merge_filters(filters, intent.filters)
                return intent, "gemini", False
        except Exception as exc:
            logger.info("Gemini report assistant intent fallback activated: %s", exc)

    if settings.openai_api_key:
        try:
            payload = _openai_intent_payload(prompt, filters)
            result = _post_openai(payload)
            parsed = _extract_json(result)
            intent = ReportAssistantIntent.model_validate(parsed)
            if intent.kind not in _ALLOWED_KINDS:
                raise ValueError("unsupported intent kind")
            intent.filters = _merge_filters(filters, intent.filters)
            return intent, "openai", False
        except (httpx.HTTPError, ValidationError, ValueError, TypeError, json.JSONDecodeError) as exc:
            logger.info("Report assistant intent fallback activated: %s", exc.__class__.__name__)

    return local_intent(prompt, filters), "local", True


def build_narrative(intent: ReportAssistantIntent, data: Any, provider: str, prompt: str = "") -> tuple[str, bool]:
    fallback_used = False
    if provider == "gemini" and settings.gemini_api_key:
        try:
            text = _gemini_narrative(intent, data, prompt=prompt)
            if text:
                return text[:1500], False
        except Exception as exc:
            logger.info("Gemini report assistant narrative fallback activated: %s", exc)
            fallback_used = True

    if provider == "openai" and settings.openai_api_key:
        try:
            payload = _openai_narrative_payload(intent, data, prompt=prompt)
            result = _post_openai(payload)
            text = _extract_text(result).strip()
            if text:
                return text[:1500], False
        except (httpx.HTTPError, ValueError, TypeError, json.JSONDecodeError) as exc:
            logger.info("Report assistant narrative fallback activated: %s", exc.__class__.__name__)
            fallback_used = True

    return _local_narrative(intent, data, prompt=prompt), fallback_used


def _gemini_interpret_intent(prompt: str, filters: ReportFilters) -> ReportAssistantIntent | None:
    if not settings.gemini_api_key:
        return None
    models_to_try = [settings.gemini_model]
    if "gemini-flash-latest" not in models_to_try:
        models_to_try.append("gemini-flash-latest")

    system_prompt = (
        "Clasifica pedidos de reportes de FashionStore Atelier. "
        "Devuelve exclusivamente un objeto JSON válido con los campos:\n"
        '- "kind": uno de ["dashboard", "top_products", "sales_by_branch", "inventory", "reservations", "revenue_by_category"]\n'
        '- "filters": {"date_from": null o string ISO, "date_to": null o string ISO, "branch_id": null o int}\n'
        '- "chart_type": uno de ["bar", "line", "pie", "table", "kpi"]\n'
        '- "reasoning": breve texto explicando la clasificación analítica.\n'
        "No incluyas markdown adicional ni explicaciones fuera del JSON."
    )
    user_content = json.dumps({"prompt": prompt, "explicit_filters": _jsonable(filters)}, ensure_ascii=False)
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_content}]}],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
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
                            raw_text = parts[0].get("text", "").strip()
                            parsed = json.loads(raw_text)
                            return ReportAssistantIntent.model_validate(parsed)
                elif res.status_code == 404:
                    continue
                else:
                    break
        except Exception as exc:
            logger.info("Gemini interpret_intent failed: %s", exc)
            break
    return None


def _gemini_narrative(intent: ReportAssistantIntent, data: Any, prompt: str = "") -> str | None:
    if not settings.gemini_api_key:
        return None
    models_to_try = [settings.gemini_model]
    if "gemini-flash-latest" not in models_to_try:
        models_to_try.append("gemini-flash-latest")

    system_prompt = (
        "Redacta un diagnóstico y recomendación ejecutiva concisa en español para FashionStore. "
        "Responde directamente a lo que solicita el usuario basándote exclusivamente en los hechos JSON suministrados. "
        "Si preguntan por canales (física vs online), compara los totales y porcentajes y sugiere acciones estratégicas. "
        "No inventes cifras externas ni uses formato Markdown innecesario."
    )
    facts = {"intent": _jsonable(intent), "data": _jsonable(data), "user_prompt": prompt}
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": json.dumps(facts, ensure_ascii=False)}]}],
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 600,
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
                    break
        except Exception as exc:
            logger.info("Gemini narrative failed: %s", exc)
            break
    return None


def _post_openai(payload: dict[str, Any]) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"}
    with httpx.Client(timeout=_TIMEOUT_SECONDS) as client:
        response = client.post(_OPENAI_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


def _openai_intent_payload(prompt: str, filters: ReportFilters) -> dict[str, Any]:
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "kind": {"type": "string", "enum": sorted(_ALLOWED_KINDS)},
            "filters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "date_from": {"type": ["string", "null"]},
                    "date_to": {"type": ["string", "null"]},
                    "branch_id": {"type": ["integer", "null"]},
                },
                "required": ["date_from", "date_to", "branch_id"],
            },
            "reasoning": {"type": "string"},
        },
        "required": ["kind", "filters", "reasoning"],
    }
    return {
        "model": settings.openai_model,
        "input": [
            {
                "role": "system",
                "content": "Clasifica pedidos de reportes de FashionStore. Devuelve solo JSON válido que cumpla el esquema. No propongas SQL, llamadas a herramientas ni números de negocio.",
            },
            {
                "role": "user",
                "content": json.dumps({"prompt": prompt, "explicit_filters": _jsonable(filters)}, ensure_ascii=False),
            },
        ],
        "text": {"format": {"type": "json_schema", "name": "report_assistant_intent", "strict": True, "schema": schema}},
    }


def _openai_narrative_payload(intent: ReportAssistantIntent, data: Any, prompt: str = "") -> dict[str, Any]:
    facts = {"intent": _jsonable(intent), "data": _jsonable(data), "user_prompt": prompt}
    return {
        "model": settings.openai_model,
        "input": [
            {
                "role": "system",
                "content": (
                    "Redacta un diagnóstico y recomendación ejecutiva concisa en español para FashionStore. "
                    "Responde directamente a lo que solicita el usuario basándote exclusivamente en los hechos JSON suministrados. "
                    "Si preguntan por canales (física vs online), compara los totales y porcentajes y sugiere acciones estratégicas. "
                    "No inventes cifras externas."
                ),
            },
            {"role": "user", "content": json.dumps(facts, ensure_ascii=False)},
        ],
    }


def _extract_json(response: dict[str, Any]) -> dict[str, Any]:
    text = _extract_text(response)
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("provider JSON is not an object")
    return parsed


def _extract_text(response: dict[str, Any]) -> str:
    if isinstance(response.get("output_text"), str):
        return response["output_text"]
    fragments: list[str] = []
    for output in response.get("output", []):
        for content in output.get("content", []):
            if isinstance(content.get("text"), str):
                fragments.append(content["text"])
    if not fragments:
        raise ValueError("provider response did not include text")
    return "".join(fragments)


def _merge_filters(explicit_filters: ReportFilters, provider_filters: ReportFilters | None) -> ReportFilters:
    provider_filters = provider_filters or ReportFilters()
    return ReportFilters(
        date_from=explicit_filters.date_from or provider_filters.date_from,
        date_to=explicit_filters.date_to or provider_filters.date_to,
        branch_id=explicit_filters.branch_id if explicit_filters.branch_id is not None else provider_filters.branch_id,
    )


def _local_narrative(intent: ReportAssistantIntent, data: Any, prompt: str = "") -> str:
    norm_prompt = _normalize(prompt) if prompt else ""
    if intent.kind == "top_products":
        items = data if isinstance(data, list) else []
        if not items:
            return "No se encontraron productos vendidos para los filtros seleccionados."
        first = items[0]
        total_rev = sum(Decimal(str(i.get("revenue", 0))) for i in items)
        first_pct = (Decimal(str(first.get("revenue", 0))) / total_rev * 100) if total_rev > 0 else Decimal(0)
        runner_up = f", seguido de '{items[1]['product_name']}' ({items[1]['units_sold']} prendas)" if len(items) > 1 else ""
        return (
            f"Diagnóstico comercial de prendas: El producto líder en demanda es '{first['product_name']}' con {first['units_sold']} unidad(es) vendida(s) "
            f"generando Bs {first['revenue']} ({first_pct:.1f}% de la facturación destacada){runner_up}. "
            f"Recomendación estratégica: Destacar la prenda estrella en vitrinas principales de sucursal y banners web para capitalizar la temporada."
        )
    if intent.kind == "sales_by_branch":
        items = data if isinstance(data, list) else []
        if not items:
            return "No se registran transacciones por sucursal para los filtros seleccionados."
        top_b = max(items, key=lambda x: Decimal(str(x.get("total", 0)))) if items else None
        tot_branches = sum(Decimal(str(b.get("total", 0))) for b in items)
        top_pct = (Decimal(str(top_b.get("total", 0))) / tot_branches * 100) if (top_b and tot_branches > 0) else Decimal(0)
        return (
            f"Rendimiento territorial: Se analizaron {len(items)} sucursal(es). La sede de mayor facturación es '{top_b['branch_name']}' con Bs {top_b['total']} "
            f"({top_pct:.1f}% del volumen consolidado en {top_b.get('sales_count', 0)} transacciones). "
            f"Recomendación estratégica: Replicar las mejores prácticas de merchandising y promociones locales de '{top_b['branch_name']}' en las demás sedes."
        )
    if intent.kind == "inventory":
        items = data if isinstance(data, list) else []
        if not items:
            return "El inventario se encuentra en niveles saludables; no se registran artículos con quiebre ni stock crítico para los filtros actuales."
        critical = [item for item in items if int(item.get("available_quantity", 0)) <= 2]
        first = items[0]
        critical_count = len(critical)
        if critical_count > 0:
            return (
                f"Alerta de inventario: Se detectaron {len(items)} artículo(s) con stock bajo o comprometido, de los cuales {critical_count} están en nivel crítico (≤ 2 unidades). "
                f"El caso más urgente es '{first['product_name']}' (SKU: {first.get('sku', 'N/D')}) en {first.get('branch_name', 'sucursal')} con solo {first['available_quantity']} unidad(es) disponible(s). "
                f"Se requiere emitir orden de reposición prioritaria para evitar desabastecimiento en tienda."
            )
        return (
            f"Se detectaron {len(items)} artículo(s) con bajo stock según los filtros aplicados. "
            f"El artículo con menor disponibilidad es '{first['product_name']}' (SKU: {first.get('sku', 'N/D')}) en {first.get('branch_name', 'sucursal')} con {first['available_quantity']} unidad(es) disponible(s). "
            f"Se recomienda programar abastecimiento preventivo con proveedores o coordinar traslados internos."
        )
    if intent.kind == "reservations":
        items = data if isinstance(data, list) else []
        total = sum(int(item.get("count", 0)) for item in items)
        pending = sum(int(item.get("count", 0)) for item in items if str(item.get("status", "")).upper() in ("PENDING", "CONFIRMED", "PENDIENTE"))
        return f"Auditoría de vestidores: {total} reserva(s) registradas, con {pending} apartados pendientes o activos que requieren atención en sucursal."

    if intent.kind == "revenue_by_category":
        items = data if isinstance(data, list) else []
        if not items:
            return "No se registran ventas categorizadas para los filtros seleccionados."
        top_cat = items[0]
        total_rev = sum(Decimal(str(i.get("total_revenue", 0))) for i in items)
        top_pct = top_cat.get("percentage", 0.0)
        return (
            f"Análisis de ingresos por categoría: La categoría dominante es '{top_cat['category_name']}' con Bs {top_cat['total_revenue']} "
            f"({top_pct}% de los ingresos del período a través de {top_cat['units_sold']} prendas vendidas). "
            f"Recomendación estratégica: Fortalecer la disponibilidad y reposición de la línea '{top_cat['category_name']}' y lanzar promociones cruzadas con categorías de menor rotación."
        )

    # intent.kind == "dashboard"
    dash = data if isinstance(data, dict) else {}
    rev = dash.get("revenue", {}) if isinstance(dash.get("revenue"), dict) else {}
    tot_val = Decimal(str(rev.get("total", 0)))
    sales_cnt = int(rev.get("sales_count", 0))
    channels = dash.get("sales_by_channel", []) if isinstance(dash.get("sales_by_channel"), list) else []
    branches = dash.get("sales_by_branch", []) if isinstance(dash.get("sales_by_branch"), list) else []
    products = dash.get("top_products", []) if isinstance(dash.get("top_products"), list) else []
    low_stock_items = dash.get("low_stock", []) if isinstance(dash.get("low_stock"), list) else []

    # 1. Comparativa multicanal (Tienda física vs Online / Canales de venta)
    if any(k in norm_prompt for k in ("canal", "canales", "online", "fisica", "digital", "pos")) and channels:
        ch_rev_total = sum(Decimal(str(c.get("total", 0))) for c in channels)
        sorted_ch = sorted(channels, key=lambda c: Decimal(str(c.get("total", 0))), reverse=True)
        ch_parts = []
        for c in sorted_ch:
            c_raw = str(c.get("channel", "")).upper()
            c_name = "Online/Digital" if c_raw in ("DIGITAL", "ONLINE", "WEB") else "Tienda física (POS)"
            c_tot = Decimal(str(c.get("total", 0)))
            c_cnt = int(c.get("sales_count", 0))
            c_pct = (c_tot / ch_rev_total * 100) if ch_rev_total > 0 else Decimal(0)
            ch_parts.append(f"{c_name}: Bs {c_tot:.2f} ({c_pct:.1f}% con {c_cnt} ventas)")
        lead_raw = str(sorted_ch[0].get("channel", "")).upper()
        lead_name = "Online/Digital" if lead_raw in ("DIGITAL", "ONLINE", "WEB") else "Tienda física"
        comparison_str = " vs ".join(ch_parts)
        return (
            f"Comparativa multicanal ({comparison_str}). El canal {lead_name} lidera la recaudación comercial. "
            f"Recomendación estratégica: Para balancear la facturación y potenciar el canal físico, implementar retiro en sucursal gratuito (Click & Collect) "
            f"que impulse visitas presenciales, junto con beneficios de venta cruzada en caja para compras presenciales."
        )

    # 2. Análisis cruzado de sucursal destacada y producto estrella
    if any(k in norm_prompt for k in ("sucursal", "sede", "tienda")) and any(k in norm_prompt for k in ("producto", "estrella", "lider", "vendido")):
        top_b = max(branches, key=lambda b: Decimal(str(b.get("total", 0)))) if branches else None
        top_p = products[0] if products else None
        b_text = f"la sucursal con mayor volumen es '{top_b['branch_name']}' con Bs {Decimal(str(top_b['total'])):.2f} ({top_b['sales_count']} ventas)" if top_b else "sin ventas por sucursal"
        p_text = f"el artículo líder es '{top_p['product_name']}' con {top_p['units_sold']} prendas vendidas (Bs {Decimal(str(top_p['revenue'])):.2f})" if top_p else "sin productos destacados"
        return (
            f"Diagnóstico cruzado: En el periodo analizado, {b_text}, mientras que {p_text}. "
            f"Recomendación estratégica: Mantener inventario de seguridad prioritario del producto estrella en la sucursal líder para maximizar la conversión comercial."
        )

    # 3. Resumen financiero (ingresos, descuentos, ticket promedio)
    if any(k in norm_prompt for k in ("ticket", "ticket promedio", "descuento", "descuentos", "balance")):
        dsc = Decimal(str(rev.get("discount", 0)))
        avg_t = (tot_val / sales_cnt) if sales_cnt > 0 else Decimal(0)
        return (
            f"Balance financiero ejecutivo: Se confirmaron {sales_cnt} ventas por un total de Bs {tot_val:.2f}, "
            f"con un ticket promedio de Bs {avg_t:.2f} por transacción y Bs {dsc:.2f} otorgados en descuentos promocionales. "
            f"Recomendación estratégica: Activar promociones con monto mínimo de compra (ej. 10% en compras > Bs 300) para elevar el ticket promedio."
        )

    # 4. Default para dashboard general
    crit_count = len([i for i in low_stock_items if int(i.get("available_quantity", 0)) <= 2])
    top_p_name = f", destacando '{products[0]['product_name']}' en ventas" if products else ""
    alert_suffix = f". Alerta: {crit_count} artículo(s) en stock crítico" if crit_count > 0 else ""
    return (
        f"El dashboard ejecutivo consolida {sales_cnt} venta(s) confirmada(s) por un total de Bs {tot_val:.2f}{top_p_name}{alert_suffix}. "
        f"Se sugiere mantener abastecimiento continuo en las tiendas de mayor rotación."
    )


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return _jsonable(value.model_dump())
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def _normalize(value: str) -> str:
    lowered = value.lower()
    replacements = str.maketrans("áéíóúüñ", "aeiouun")
    return re.sub(r"\s+", " ", lowered.translate(replacements)).strip()


def transcribe_audio_prompt(audio_base64: str, mime_type: str = "audio/webm") -> str | None:
    """Transcribe audio with Gemini when configured, without fabricated fallback text."""
    if not settings.gemini_api_key:
        return None

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": "Transcribe exactamente las palabras habladas en este audio en español. Devuelve únicamente el texto transcripto sin comentarios."},
                        {"inlineData": {"mimeType": mime_type, "data": audio_base64}},
                    ],
                }
            ]
        }
        with httpx.Client(timeout=_TRANSCRIPTION_TIMEOUT_SECONDS) as client:
            response = client.post(url, json=payload)
            if response.status_code != 200:
                return None
            data = response.json()
            candidates = data.get("candidates", [])
            if not isinstance(candidates, list) or not candidates:
                return None
            parts = candidates[0].get("content", {}).get("parts", [])
            if not isinstance(parts, list) or not parts:
                return None
            text = parts[0].get("text")
            return text.strip() if isinstance(text, str) and text.strip() else None
    except Exception as exc:
        logger.info("Gemini audio transcription unavailable: %s", exc.__class__.__name__)
        return None
