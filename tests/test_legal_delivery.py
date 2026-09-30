import json
import os
import sys
from pathlib import Path
from io import BytesIO
from urllib.error import HTTPError

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.legal_delivery import InfraiError, MatterIntake, watermark_for_delivery


class FakeResponse:
    status = 200
    headers = {}

    def read(self):
        return json.dumps({"ok": True, "data": {"document": "watermarked"}, "error": None, "metadata": {}}).encode()


def test_deadline_decision_and_request_boundary(monkeypatch):
    monkeypatch.setenv("INFRAI_API_KEY", "test-key")
    seen = {}

    def transport(request):
        seen["method"] = request.method
        seen["body"] = json.loads(request.data.decode())
        return FakeResponse()

    result = watermark_for_delivery(MatterIntake("MAT-7", "client@example.org", 2), b"pdf", transport)
    assert result.follow_up_required is True
    assert seen["method"] == "POST"
    assert seen["body"]["text"].startswith("CONFIDENTIAL - MAT-7")


def test_http_error_envelope_is_reported(monkeypatch):
    monkeypatch.setenv("INFRAI_API_KEY", "test-key")

    def transport(request):
        body = json.dumps({"ok": False, "error": {"code": "INVALID_PDF"}}).encode()
        raise HTTPError(request.full_url, 400, "Bad Request", {}, BytesIO(body))

    with pytest.raises(InfraiError) as caught:
        watermark_for_delivery(MatterIntake("MAT-7", "client@example.org", 2), b"pdf", transport)
    assert caught.value.code == "INVALID_PDF"
    assert caught.value.status == 400


def test_http_rate_limit_retries(monkeypatch):
    monkeypatch.setenv("INFRAI_API_KEY", "test-key")
    attempts = []

    def transport(request):
        attempts.append(request)
        if len(attempts) == 1:
            body = json.dumps({"ok": False, "error": {"code": "RATE_LIMITED"}}).encode()
            raise HTTPError(request.full_url, 429, "Too Many Requests", {"Retry-After": "0"}, BytesIO(body))
        return FakeResponse()

    result = watermark_for_delivery(MatterIntake("MAT-7", "client@example.org", 2), b"pdf", transport)
    assert result.api_data == {"document": "watermarked"}
    assert len(attempts) == 2
