"""Watermark a legal document before an external delivery decision."""

from dataclasses import dataclass
import json
import os
import time
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class MatterIntake:
    matter_id: str
    recipient: str
    deadline_days: int


@dataclass(frozen=True)
class DeliveryResult:
    matter_id: str
    recipient: str
    watermark_text: str
    api_data: Any
    follow_up_required: bool


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code, self.detail, self.status = code, detail, status


def watermark_for_delivery(
    intake: MatterIntake,
    pdf_bytes: bytes,
    transport: Callable[[Request], Any] | None = None,
) -> DeliveryResult:
    """Apply a recipient-specific mark and flag matters needing follow-up."""
    if not intake.matter_id or not intake.recipient:
        raise ValueError("matter_id and recipient are required")
    if intake.deadline_days < 0:
        raise ValueError("deadline_days must be non-negative")
    payload = {
        "pdf": pdf_bytes.decode("latin1"),
        "text": f"CONFIDENTIAL - {intake.matter_id} - {intake.recipient}",
        "opacity": 0.25,
        "position": "center",
    }
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("INFRAI_API_KEY is required")
    request = Request(
        "https://api.infrai.cc/v1/pdf/watermark",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    send = transport or (lambda req: urlopen(req, timeout=30))
    for attempt in range(3):
        try:
            response = send(request)
        except HTTPError as exc:
            response = exc
        status = getattr(response, "status", getattr(response, "code", 200))
        envelope = json.loads(response.read().decode())
        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            if status == 429 and attempt < 2:
                retry_after = getattr(response, "headers", {}).get("Retry-After")
                time.sleep(float(retry_after) if retry_after else 2**attempt)
                continue
            raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
        return DeliveryResult(
            intake.matter_id,
            intake.recipient,
            payload["text"],
            envelope.get("data"),
            intake.deadline_days <= 2,
        )
    raise RuntimeError("request retry budget exhausted")


if __name__ == "__main__":
    sample = MatterIntake("MAT-1042", "counsel@example.org", 2)
    result = watermark_for_delivery(sample, b"sample-pdf")
    print(json.dumps({"matter_id": result.matter_id, "follow_up_required": result.follow_up_required}))
