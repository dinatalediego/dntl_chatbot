import json
import secrets

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db, init_db
from .medallio import fetch_updated_leads
from .metrics import metrics
from .models import Action, Event, Lead, SourceCursor
from .schemas import DirectLeadEvent, MedallioRefreshEvent
from .security import verify_internal
from .service import evaluate_and_contact, process_inbound, upsert_lead

settings = get_settings()
app = FastAPI(title="NIDO", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "provider": settings.message_provider}


@app.get("/metrics")
def get_metrics(db: Session = Depends(get_db)) -> dict:
    return metrics(db)


@app.post("/webhooks/medallio")
async def medallio_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    verify_internal(request.headers.get("X-NIDO-Timestamp"), request.headers.get("X-NIDO-Signature"), body)
    event = MedallioRefreshEvent.model_validate_json(body)
    expected = f"{settings.medallio_schema}.{settings.medallio_table}"
    if event.source_table != expected:
        raise HTTPException(422, "Unexpected source_table")
    if db.scalar(select(Event).where(Event.event_id == event.event_id)):
        return {"status": "duplicate"}
    db.add(Event(event_id=event.event_id, event_type=event.event_type, payload=event.model_dump(mode="json")))
    cursor = db.get(SourceCursor, expected)
    snapshots = fetch_updated_leads(cursor.watermark if cursor else None, event.watermark)
    for snapshot in snapshots:
        evaluate_and_contact(db, upsert_lead(db, snapshot))
    if cursor is None:
        cursor = SourceCursor(source_key=expected, watermark=event.watermark)
        db.add(cursor)
    elif event.watermark:
        cursor.watermark = event.watermark
    db.commit()
    return {"status": "ok", "processed": len(snapshots)}


@app.post("/webhooks/crm/lead")
def crm_lead(event: DirectLeadEvent, db: Session = Depends(get_db)):
    lead = upsert_lead(db, event.model_dump(), source="crm")
    decision = evaluate_and_contact(db, lead)
    db.commit()
    return {"lead_id": lead.id, "decision": decision.decision}


@app.get("/webhooks/meta")
def meta_verify(request: Request):
    if request.query_params.get("hub.mode") == "subscribe" and secrets.compare_digest(request.query_params.get("hub.verify_token") or "", settings.meta_verify_token):
        return PlainTextResponse(request.query_params.get("hub.challenge") or "")
    raise HTTPException(403, "verification failed")


@app.post("/webhooks/meta")
async def meta_inbound(request: Request, db: Session = Depends(get_db)):
    payload = json.loads(await request.body())
    handled = 0
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for status in value.get("statuses", []):
                if action := db.scalar(select(Action).where(Action.provider_message_id == status.get("id"))):
                    action.status = str(status.get("status") or action.status).upper()
            for msg in value.get("messages", []):
                phone = "+" + str(msg.get("from", "")).lstrip("+")
                text = ((msg.get("text") or {}).get("body") or "").strip()
                if not phone or not text:
                    continue
                lead = db.scalar(select(Lead).where(Lead.phone_e164 == phone).order_by(Lead.id.desc()))
                if lead is None:
                    lead = upsert_lead(db, {"source_lead_id": f"wa:{phone}", "phone_e164": phone, "opted_in": True}, source="whatsapp")
                process_inbound(db, lead, text, msg.get("id"))
                handled += 1
    db.commit()
    return {"status": "ok", "handled": handled}
