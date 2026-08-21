from datetime import datetime
from zoneinfo import ZoneInfo

from app.decision import decide_contact
from app.models import Lead


def test_meta_requires_opt_in(monkeypatch):
    from app import decision
    monkeypatch.setattr(decision.settings, "message_provider", "meta")
    lead = Lead(source="demo", source_lead_id="1", phone_e164="+51999999999", opted_in=False)
    result = decide_contact(lead, datetime(2026, 8, 20, 12, tzinfo=ZoneInfo("America/Lima")))
    assert result.action == "INELIGIBLE"


def test_control_is_bau(monkeypatch):
    from app import decision
    monkeypatch.setattr(decision.settings, "message_provider", "mock")
    monkeypatch.setattr(decision.settings, "experiment_control_pct", 100)
    lead = Lead(source="demo", source_lead_id="2")
    result = decide_contact(lead, datetime(2026, 8, 20, 12, tzinfo=ZoneInfo("America/Lima")))
    assert result.action == "BAU"
