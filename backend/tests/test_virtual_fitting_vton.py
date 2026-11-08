import base64
import io
import os
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from PIL import Image

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "test-secret")

from app.core.models import Product, ProductImage
from app.modules.virtual_fitting import vton_service
from app.modules.virtual_fitting.vton_service import VtonService


def _image_data_uri(color: tuple[int, int, int] = (80, 120, 200), size: tuple[int, int] = (16, 16)) -> str:
    image = Image.new("RGB", size, color)
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"


@pytest.fixture
def product_with_image(tmp_path):
    garment_path = tmp_path / "garment.png"
    Image.new("RGBA", (24, 32), (200, 40, 90, 255)).save(garment_path)
    product = Product(
        id=7,
        category_id=1,
        code="VTON-1",
        name="Camisa test",
        slug="camisa-test",
        price=Decimal("99.90"),
    )
    product.images = [ProductImage(image_url=str(garment_path), is_primary=True, sort_order=0)]
    product.variants = []
    return product


def test_process_try_on_uses_gemini_interactions_when_capture_and_key_exist(monkeypatch, product_with_image) -> None:
    captured = _image_data_uri()
    generated = base64.b64encode(b"generated-image").decode("utf-8")
    captured_requests = []

    class FakeResponse:
        status_code = 200
        text = "ok"

        def json(self):
            return {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"inlineData": {"mimeType": "image/png", "data": generated}}
                            ]
                        }
                    }
                ]
            }

    class FakeClient:
        def __init__(self, timeout):
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, headers, json):
            captured_requests.append(SimpleNamespace(url=url, headers=headers, json=json))
            return FakeResponse()

    monkeypatch.setattr(vton_service, "get_catalog_product", lambda db, product_id: product_with_image)
    monkeypatch.setattr(vton_service.settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(vton_service.settings, "gemini_vton_model", "test-image-model")
    monkeypatch.setattr(vton_service.httpx, "Client", FakeClient)

    result = VtonService.process_try_on(db=object(), product_id=7, image_base64=captured)

    assert result["composite_image_base64"] == f"data:image/png;base64,{generated}"
    details = result["detalles_tecnicos"]
    assert details["engine"] == "Gemini Image API"
    assert details["confidence"] is None
    assert result["calce_porcentaje"] is None
    assert result["calce_status"] == "GENERADO_POR_GEMINI"
    assert len(captured_requests) == 1
    request = captured_requests[0]
    assert "models/test-image-model:generateContent" in request.url
    assert "key=test-key" in request.url
    assert request.headers["x-goog-api-key"] == "test-key"
    assert request.json["generationConfig"] == {"responseModalities": ["IMAGE"]}
    parts = request.json["contents"][0]["parts"]
    assert len(parts) == 3
    assert "Virtual Try-On" in parts[0]["text"]
    assert parts[1]["inlineData"]["mimeType"] == "image/jpeg"
    assert isinstance(parts[1]["inlineData"]["data"], str)
    assert parts[2]["inlineData"]["mimeType"] == "image/jpeg"
    assert isinstance(parts[2]["inlineData"]["data"], str)


def test_process_try_on_returns_studio_pending_without_capture(monkeypatch, product_with_image) -> None:
    monkeypatch.setattr(vton_service, "get_catalog_product", lambda db, product_id: product_with_image)

    result = VtonService.process_try_on(db=object(), product_id=7)

    assert result["composite_image_base64"].startswith("data:image/jpeg;base64,")
    response_without_image = {key: value for key, value in result.items() if key != "composite_image_base64"}
    assert result["calce_porcentaje"] is None
    assert "99" not in str(response_without_image)
    assert "EXCELENTE" not in str(response_without_image)
    details = result["detalles_tecnicos"]
    assert details["engine"] == "Studio-Pending"
    assert details["engine_mode"] == "studio_pending"
    assert details["confidence"] is None
    assert details["landmarks_detected"] == []


def test_process_try_on_returns_503_without_key(monkeypatch, product_with_image) -> None:
    monkeypatch.setattr(vton_service, "get_catalog_product", lambda db, product_id: product_with_image)
    monkeypatch.setattr(vton_service.settings, "gemini_api_key", None)

    with pytest.raises(HTTPException) as exc_info:
        VtonService.process_try_on(db=object(), product_id=7, image_base64=_image_data_uri())

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail["code"] == "VTON_PROVIDER_UNAVAILABLE"


def test_process_try_on_raises_502_when_provider_is_unavailable(monkeypatch, product_with_image) -> None:
    class FakeResponse:
        status_code = 503
        text = "unavailable"

        def json(self):
            return {"error": {"message": "unavailable"}}

    class FakeClient:
        def __init__(self, timeout):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, headers, json):
            return FakeResponse()

    monkeypatch.setattr(vton_service, "get_catalog_product", lambda db, product_id: product_with_image)
    monkeypatch.setattr(vton_service.settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(vton_service.httpx, "Client", FakeClient)

    with pytest.raises(HTTPException) as exc_info:
        VtonService.process_try_on(db=object(), product_id=7, image_base64=_image_data_uri())

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail["code"] == "VTON_PROVIDER_OUTPUT_UNAVAILABLE"


def test_process_try_on_rejects_invalid_captured_image(monkeypatch, product_with_image) -> None:
    monkeypatch.setattr(vton_service, "get_catalog_product", lambda db, product_id: product_with_image)

    with pytest.raises(HTTPException) as exc_info:
        VtonService.process_try_on(db=object(), product_id=7, image_base64="not-base64")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "VTON_IMAGE_INVALID"
