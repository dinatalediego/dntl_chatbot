import hashlib
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import get_settings
from .models import Lead

settings = get_settings()
POLICY_VERSION = "immediate-contact-v1"


@dataclass(frozen=True)
class ContactDecision:
    action: str
    reason: str
    score: float
    experiment_group: str


def experiment_group(source_lead_id: str) -> str:
    pct = settings.experiment_control_pct
    if pct <= 0:
        return "TREATMENT"
    bucket = int(hashlib.sha256(source_lead_id.encode()).hexdigest()[:8], 16) % 100
    return "CONTROL" if bucket < pct else "TREATMENT"


def decide_contact(lead: Lead, now: datetime | None = None) -> ContactDecision:
    group = experiment_group(lead.source_lead_id)
    if lead.opted_out:
        return ContactDecision("INELIGIBLE", "lead_opted_out", 0.0, group)
    if settings.message_provider == "meta" and (not lead.opted_in or not lead.phone_e164):
        reason = "missing_opt_in" if not lead.opted_in else "missing_phone"
        return ContactDecision("INELIGIBLE", reason, 0.0, group)
    current = now or datetime.now(ZoneInfo(settings.timezone))
    local = current.astimezone(ZoneInfo(settings.timezone)) if current.tzinfo else current.replace(tzinfo=ZoneInfo(settings.timezone))
    if not settings.contact_start_hour <= local.hour < settings.contact_end_hour:
        return ContactDecision("DEFER", "outside_contact_hours", 0.25, group)
    if group == "CONTROL":
        return ContactDecision("BAU", "experiment_control_bau", 0.5, group)
    return ContactDecision("CONTACT_NOW", "eligible_new_lead", 0.8, group)
