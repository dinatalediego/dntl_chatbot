from dataclasses import dataclass
from uuid import uuid4

import httpx

from .config import get_settings

settings = get_settings()


@dataclass(frozen=True)
class SendResult:
    provider_message_id: str
    status: str
    rendered_text: str


class MockProvider:
    name = "mock"

    def send_initial(self, phone: str | None, name: str | None, project: str | None) -> SendResult:
        text = f"Hola {name or ''}. Gracias por tu interés{f' en {project}' if project else ''}. ¿Buscas precio, disponibilidad o visita?".strip()
        return SendResult(f"mock-{uuid4()}", "SENT", text)

    def send_text(self, phone: str | None, text: str) -> SendResult:
        return SendResult(f"mock-{uuid4()}", "SENT", text)


class MetaProvider:
    name = "meta"

    def _post(self, payload: dict) -> SendResult:
        url = f"{settings.meta_graph_base.rstrip('/')}/{settings.meta_graph_version}/{settings.meta_phone_number_id}/messages"
        headers = {"Authorization": f"Bearer {settings.meta_access_token}"}
        response = httpx.post(url, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        message_id = (data.get("messages") or [{}])[0].get("id", f"meta-{uuid4()}")
        return SendResult(message_id, "ACCEPTED", str(payload.get("type")))

    def send_initial(self, phone: str | None, name: str | None, project: str | None) -> SendResult:
        if not phone:
            raise RuntimeError("phone required")
        return self._post({
            "messaging_product": "whatsapp",
            "to": phone.lstrip("+"),
            "type": "template",
            "template": {"name": settings.meta_template_name, "language": {"code": settings.meta_template_language}},
        })

    def send_text(self, phone: str | None, text: str) -> SendResult:
        if not phone:
            raise RuntimeError("phone required")
        return self._post({"messaging_product": "whatsapp", "to": phone.lstrip("+"), "type": "text", "text": {"body": text}})


def get_provider():
    return MetaProvider() if settings.message_provider == "meta" else MockProvider()
