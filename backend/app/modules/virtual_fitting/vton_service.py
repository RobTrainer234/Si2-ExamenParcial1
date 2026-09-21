import base64
import io
import logging
import math
import os
from pathlib import Path
from typing import Any
import urllib.request

import httpx
from fastapi import HTTPException, status
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.models import Product, User
from app.modules.catalog.service import get_catalog_product

logger = logging.getLogger(__name__)

_GEMINI_GENERATE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_VTON_HTTP_TIMEOUT_SECONDS = 60.0
_MAX_CAPTURED_IMAGE_BYTES = 10 * 1024 * 1024
_MAX_CAPTURED_IMAGE_PIXELS = 16_000_000
_ALLOWED_CAPTURED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


class VtonService:
    @staticmethod
    def _get_primary_image_path(product: Product) -> str | None:
        images = sorted(product.images, key=lambda item: item.sort_order)
        primary = next((image for image in images if image.is_primary), None)
        return (primary or images[0]).image_url if images else None

    @staticmethod
    def _load_garment_image(image_url: str | None) -> Image.Image | None:
        if not image_url:
            return None
        try:
            # Check local media path first
            if image_url.startswith("/media/"):
                rel_path = image_url.replace("/media/", "")
                local_file = Path(settings.media_dir) / rel_path
                if local_file.exists():
                    return Image.open(local_file).convert("RGBA")

            # Check if full path on host
            direct_path = Path(image_url)
            if direct_path.exists():
                return Image.open(direct_path).convert("RGBA")

            # Check HTTP/HTTPS
            if image_url.startswith("http://") or image_url.startswith("https://"):
                req = urllib.request.Request(image_url, headers={"User-Agent": "FashionStore-VTON/1.0"})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    data = resp.read()
                    return Image.open(io.BytesIO(data)).convert("RGBA")
        except Exception as e:
            logger.warning("Could not load garment image from %s: %s", image_url, e)
        return None

    @staticmethod
    def _decode_captured_image(image_base64: str) -> tuple[bytes, str]:
        if not isinstance(image_base64, str) or not image_base64.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "VTON_IMAGE_INVALID", "message": "La imagen capturada no es vÃ¡lida."},
            )

        clean_b64 = image_base64.strip()
        declared_mime = "image/jpeg"
        if clean_b64.startswith("data:"):
            header, _, payload = clean_b64.partition(",")
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "VTON_IMAGE_INVALID", "message": "La imagen capturada no es base64 vÃ¡lida."},
                )
            declared_mime = header[5:].split(";", 1)[0] or declared_mime
            clean_b64 = payload

        try:
            img_bytes = base64.b64decode(clean_b64, validate=True)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "VTON_IMAGE_INVALID", "message": "La imagen capturada no es base64 vÃ¡lida."},
            ) from exc

        if len(img_bytes) > _MAX_CAPTURED_IMAGE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "code": "VTON_IMAGE_TOO_LARGE",
                    "message": "La imagen capturada excede el tamaÃ±o mÃ¡ximo permitido.",
                    "max_bytes": _MAX_CAPTURED_IMAGE_BYTES,
                },
            )

        try:
            with Image.open(io.BytesIO(img_bytes)) as raw_image:
                fmt = raw_image.format
                if fmt not in _ALLOWED_CAPTURED_IMAGE_FORMATS:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={"code": "VTON_IMAGE_UNSUPPORTED", "message": "La imagen capturada debe ser JPEG, PNG o WEBP."},
                    )
                # Correct EXIF rotation (cell phones take portrait photos with EXIF rotation tags)
                transposed = ImageOps.exif_transpose(raw_image)
                rgb_img = transposed.convert("RGB")
                if max(rgb_img.width, rgb_img.height) > 1280:
                    rgb_img.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                rgb_img.save(buf, format="JPEG", quality=90, optimize=True)
                processed_bytes = buf.getvalue()
                declared_mime = "image/jpeg"
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "VTON_IMAGE_INVALID", "message": "La imagen capturada no es una imagen soportada."},
            ) from exc

        return processed_bytes, declared_mime

    @staticmethod
    def _image_to_base64(image: Image.Image) -> tuple[str, str]:
        rgb_image = image.convert("RGB")
        buf = io.BytesIO()
        rgb_image.save(buf, format="JPEG", quality=92, optimize=True)
        return base64.b64encode(buf.getvalue()).decode("utf-8"), "image/jpeg"

    @staticmethod
    def _extract_interactions_image(data: Any) -> str | None:
        def walk(value: Any) -> str | None:
            if isinstance(value, dict):
                inline_data = value.get("inline_data") or value.get("inlineData")
                if isinstance(inline_data, dict) and inline_data.get("data"):
                    mime = inline_data.get("mime_type") or inline_data.get("mimeType") or "image/png"
                    return f"data:{mime};base64,{inline_data['data']}"

                for key in ("data", "bytesBase64Encoded", "b64_json", "base64"):
                    candidate = value.get(key)
                    mime = value.get("mime_type") or value.get("mimeType") or value.get("content_type") or value.get("contentType")
                    if isinstance(candidate, str) and mime and str(mime).startswith("image/"):
                        return f"data:{mime};base64,{candidate}"

                image = value.get("image")
                if isinstance(image, str) and image.startswith("data:image/"):
                    return image
                if isinstance(image, dict):
                    found = walk(image)
                    if found:
                        return found

                for child in value.values():
                    found = walk(child)
                    if found:
                        return found
            elif isinstance(value, list):
                for child in value:
                    found = walk(child)
                    if found:
                        return found
            return None

        return walk(data)

    @classmethod
    def _generate_gemini_try_on(
        cls,
        *,
        product: Product,
        person_image_bytes: bytes,
        person_mime_type: str,
        garment: Image.Image,
    ) -> str | None:
        garment_b64, garment_mime = cls._image_to_base64(garment)
        person_b64 = base64.b64encode(person_image_bytes).decode("utf-8")
        
        prompt_text = (
            "Task: Virtual Try-On / Clothes Fitting.\n"
            "You are an expert AI fashion stylist. "
            "The first image is a person. The second image is a clothing garment from our store catalog.\n"
            "Generate a realistic virtual try-on image where the person is naturally wearing this exact garment.\n"
            "- Retain the person's exact face, identity, hair, skin tone, body shape, pose, and original background.\n"
            "- Naturally replace the person's current clothing with the provided clothing garment.\n"
            "- The garment must seamlessly fit the person's body contours, shoulders, chest, and arms with realistic drapery, fabric folds, and accurate lighting/shadows.\n"
            "- Do not add any text, watermark, labels, or graphical artifacts.\n"
            f"Product to fit: {product.name}."
        )

        model = settings.gemini_vton_model or "gemini-2.5-flash-image"
        api_url = _GEMINI_GENERATE_URL.format(model=model)
        api_url_with_key = f"{api_url}?key={settings.gemini_api_key}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt_text},
                        {"inlineData": {"mimeType": person_mime_type, "data": person_b64}},
                        {"inlineData": {"mimeType": garment_mime, "data": garment_b64}},
                    ]
                }
            ],
            "generationConfig": {
                "responseModalities": ["IMAGE"]
            },
        }
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": settings.gemini_api_key or "",
        }
        try:
            with httpx.Client(timeout=_VTON_HTTP_TIMEOUT_SECONDS) as client:
                response = client.post(api_url_with_key, headers=headers, json=payload)
            if response.status_code >= 400:
                logger.warning("Gemini VTON returned %s: %s", response.status_code, response.text[:200])
                return None
            
            data = response.json()
            # Extract from candidates -> content -> parts -> inlineData
            for candidate in data.get("candidates", []):
                for part in candidate.get("content", {}).get("parts", []):
                    inline_data = part.get("inlineData") or part.get("inline_data")
                    if inline_data and inline_data.get("data"):
                        mime = inline_data.get("mimeType") or inline_data.get("mime_type") or "image/png"
                        return f"data:{mime};base64,{inline_data['data']}"
            
            return cls._extract_interactions_image(data)
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            logger.warning("Gemini VTON call failed: %s", exc)
            return None

    @classmethod
    def generate_neutral_studio_placeholder(cls) -> str:
        width, height = 720, 960
        canvas = Image.new("RGBA", (width, height), (18, 18, 20, 255))
        draw = ImageDraw.Draw(canvas)

        for r in range(480, 0, -20):
            alpha = int(45 * (1 - r / 480))
            draw.ellipse(
                [(width // 2 - r, 120 - r // 2), (width // 2 + r, 120 + r)],
                fill=(65, 50, 30, alpha),
            )

        draw.line([(width // 2, 80), (width // 2, 180)], fill=(197, 168, 128, 180), width=4)
        draw.ellipse(
            [(width // 2 - 40, 160), (width // 2 + 40, 210)],
            fill=(32, 32, 36, 255),
            outline=(197, 168, 128, 200),
            width=2,
        )
        torso_points = [
            (width // 2 - 40, 195),
            (width // 2 - 190, 260),
            (width // 2 - 165, 520),
            (width // 2 - 130, 720),
            (width // 2 + 130, 720),
            (width // 2 + 165, 520),
            (width // 2 + 190, 260),
            (width // 2 + 40, 195),
        ]
        draw.polygon(torso_points, fill=(28, 28, 32, 255), outline=(197, 168, 128, 120))
        draw.rectangle([(width // 2 - 10, 720), (width // 2 + 10, 900)], fill=(197, 168, 128, 220))
        draw.ellipse(
            [(width // 2 - 90, 890), (width // 2 + 90, 930)],
            fill=(28, 28, 32, 255),
            outline=(197, 168, 128, 220),
            width=3,
        )

        rgb_canvas = canvas.convert("RGB")
        buf = io.BytesIO()
        rgb_canvas.save(buf, format="JPEG", quality=88, optimize=True)
        encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{encoded}"

    @classmethod
    def process_try_on(
        cls,
        db: Session,
        product_id: int,
        user: User | None = None,
        image_base64: str | None = None,
        metrics: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        product = get_catalog_product(db, product_id)

        variants = product.variants or []
        talla_sug = "Pendiente"
        if variants:
            primary_var = variants[0]
            if primary_var.size:
                talla_sug = primary_var.size.name

        if not image_base64:
            return {
                "product_id": product.id,
                "product_name": product.name,
                "calce_porcentaje": None,
                "calce_status": "PENDIENTE_DE_CAPTURA",
                "alineacion_hombros": "Pendiente: capturá una foto para generar VTON real.",
                "proporcion_torso": "Pendiente: sin análisis corporal hasta contar con una captura.",
                "talla_sugerida": "Pendiente",
                "veredicto_estilista": (
                    "Estudio neutral listo. Todavía no hay prueba virtual ni evaluación de calce: "
                    "capturá una foto para enviar la prenda al proveedor VTON."
                ),
                "composite_image_base64": cls.generate_neutral_studio_placeholder(),
                "detalles_tecnicos": {
                    "engine": "Studio-Pending",
                    "engine_mode": "studio_pending",
                    "landmarks_detected": [],
                    "confidence": None,
                    "shoulder_tilt_degrees": None,
                    "anatomical_symmetry": None,
                    "mode": "studio_pending",
                    "provider": "gemini_interactions",
                },
            }

        captured_image = cls._decode_captured_image(image_base64)

        if not settings.gemini_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "VTON_PROVIDER_UNAVAILABLE",
                    "message": "El motor VTON no está disponible en este momento. Intentá nuevamente más tarde.",
                },
            )

        primary_url = cls._get_primary_image_path(product)
        garment = cls._load_garment_image(primary_url)
        if garment is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "VTON_PRODUCT_IMAGE_UNAVAILABLE",
                    "message": "No hay una imagen de prenda disponible para generar la prueba virtual.",
                },
            )

        composite_b64 = cls._generate_gemini_try_on(
            product=product,
            person_image_bytes=captured_image[0],
            person_mime_type=captured_image[1],
            garment=garment,
        )
        if composite_b64 is None:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "code": "VTON_PROVIDER_OUTPUT_UNAVAILABLE",
                    "message": "El proveedor VTON no devolvió una imagen utilizable. Intentá nuevamente con otra captura.",
                },
            )

        return {
            "product_id": product.id,
            "product_name": product.name,
            "calce_porcentaje": None,
            "calce_status": "IMAGEN_GENERADA_SIN_METRICA_DE_CALCE",
            "alineacion_hombros": "Imagen VTON generada; sin medición de hombros validada por el backend.",
            "proporcion_torso": "Sin métrica corporal validada por el backend.",
            "talla_sugerida": talla_sug,
            "veredicto_estilista": (
                f"Se generó una visualización VTON para '{product.name}' con la captura enviada. "
                "No se calculó porcentaje de calce ni confianza anatómica automática."
            ),
            "composite_image_base64": composite_b64,
            "detalles_tecnicos": {
                "engine": "Gemini-VTON",
                "engine_mode": "gemini_interactions",
                "landmarks_detected": [],
                "confidence": None,
                "shoulder_tilt_degrees": None,
                "anatomical_symmetry": None,
                "mode": "camera_capture",
                "provider": "gemini_interactions",
            },
        }
