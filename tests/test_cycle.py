from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import Action, Outcome
from app.service import evaluate_and_contact, process_inbound, upsert_lead


def test_closed_loop(monkeypatch):
    from app import decision
    monkeypatch.setattr(decision.settings, "message_provider", "mock")
    monkeypatch.setattr(decision.settings, "contact_start_hour", 0)
    monkeypatch.setattr(decision.settings, "contact_end_hour", 24)
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as db:
        lead = upsert_lead(db, {"source_lead_id": "lead-1", "person_name": "Ana", "project": "Matera", "opted_in": True}, "demo")
        decision_row = evaluate_and_contact(db, lead)
        assert decision_row.decision == "CONTACT_NOW"
        assert db.scalar(select(Action).where(Action.lead_id == lead.id)).status == "SENT"
        process_inbound(db, lead, "Quiero precio")
        db.commit()
        assert db.scalar(select(Outcome).where(Outcome.lead_id == lead.id, Outcome.kind == "REPLIED_24H"))
