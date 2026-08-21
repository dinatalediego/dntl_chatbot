from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .decision import POLICY_VERSION, decide_contact
from .models import Action, Decision, Lead, Message, Outcome
from .providers import get_provider


def upsert_lead(db: Session, snapshot: dict, source: str = "medallio") -> Lead:
    lead = db.scalar(
        select(Lead).where(
            Lead.source == source,
            Lead.source_lead_id == snapshot["source_lead_id"],
        )
    )
    if lead is None:
        lead = Lead(source=source, source_lead_id=snapshot["source_lead_id"])
        db.add(lead)
    for field in [
        "person_name",
        "phone_e164",
        "project",
        "opted_in",
        "source_updated_at",
        "source_snapshot",
    ]:
        if field in snapshot:
            setattr(lead, field, snapshot[field])
    db.flush()
    return lead


def evaluate_and_contact(db: Session, lead: Lead) -> Decision:
    existing = db.scalar(
        select(Decision).where(
            Decision.lead_id == lead.id,
            Decision.policy_version == POLICY_VERSION,
        )
    )
    if existing:
        return existing
    result = decide_contact(lead)
    decision = Decision(
        lead_id=lead.id,
        policy_version=POLICY_VERSION,
        experiment_group=result.experiment_group,
        decision=result.action,
        reason=result.reason,
        score=result.score,
    )
    db.add(decision)
    db.flush()
    if result.action != "CONTACT_NOW":
        return decision
    provider = get_provider()
    action = Action(
        lead_id=lead.id,
        decision_id=decision.id,
        action_type="CONTACT_WHATSAPP",
        provider=provider.name,
        status="ATTEMPTED",
    )
    db.add(action)
    db.flush()
    try:
        sent = provider.send_initial(lead.phone_e164, lead.person_name, lead.project)
        action.provider_message_id = sent.provider_message_id
        action.status = sent.status
        action.executed_at = datetime.now(UTC)
        db.add(
            Message(
                lead_id=lead.id,
                direction="OUTBOUND",
                provider=provider.name,
                text=sent.rendered_text,
                provider_message_id=sent.provider_message_id,
                status=sent.status,
            )
        )
    except Exception as exc:
        action.status = "FAILED"
        action.error_message = str(exc)[:2000]
        raise
    return decision


def process_inbound(
    db: Session,
    lead: Lead,
    text: str,
    provider_message_id: str | None = None,
) -> str:
    provider = get_provider()
    db.add(
        Message(
            lead_id=lead.id,
            direction="INBOUND",
            provider=provider.name,
            text=text,
            provider_message_id=provider_message_id,
            status="RECEIVED",
        )
    )
    elapsed = datetime.now(UTC) - lead.eligible_at
    kinds = ["REPLIED", "REPLIED_24H"] if elapsed <= timedelta(hours=24) else ["REPLIED"]
    for kind in kinds:
        if not db.scalar(
            select(Outcome).where(Outcome.lead_id == lead.id, Outcome.kind == kind)
        ):
            db.add(
                Outcome(
                    lead_id=lead.id,
                    kind=kind,
                    value=1,
                    metadata_json={"elapsed_seconds": elapsed.total_seconds()},
                )
            )
    if any(x in text.lower() for x in ["stop", "no contactar", "no me escrib"]):
        lead.opted_out = True
    reply = (
        "Gracias. Puedo ayudarte con precio, disponibilidad o coordinar una visita. "
        "¿Qué prefieres revisar primero?"
    )
    sent = provider.send_text(lead.phone_e164, reply)
    db.add(
        Message(
            lead_id=lead.id,
            direction="OUTBOUND",
            provider=provider.name,
            text=reply,
            provider_message_id=sent.provider_message_id,
            status=sent.status,
        )
    )
    return reply
