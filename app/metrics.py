import math

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from .config import get_settings
from .models import Decision, Outcome

settings = get_settings()


def metrics(db: Session) -> dict:
    tn = db.scalar(select(func.count(distinct(Decision.lead_id))).where(Decision.experiment_group == "TREATMENT")) or 0
    cn = db.scalar(select(func.count(distinct(Decision.lead_id))).where(Decision.experiment_group == "CONTROL")) or 0
    tr = db.scalar(select(func.count(distinct(Outcome.lead_id))).join(Decision, Decision.lead_id == Outcome.lead_id).where(Decision.experiment_group == "TREATMENT", Outcome.kind == "REPLIED_24H")) or 0
    cr = db.scalar(select(func.count(distinct(Outcome.lead_id))).join(Decision, Decision.lead_id == Outcome.lead_id).where(Decision.experiment_group == "CONTROL", Outcome.kind == "REPLIED_24H")) or 0
    p1 = tr / tn if tn else None
    p0 = cr / cn if cn else None
    lift = p1 - p0 if p1 is not None and p0 is not None else None
    low = high = None
    if lift is not None:
        se = math.sqrt(p1 * (1 - p1) / tn + p0 * (1 - p0) / cn)
        low, high = lift - 1.96 * se, lift + 1.96 * se
    if cn and not settings.control_outcome_observable:
        status = "MEASUREMENT_NOT_READY"
    elif not tn or not cn:
        status = "NO_COMPARABLE_CONTROL"
    elif min(tn, cn) < 30:
        status = "COLLECTING_EVIDENCE"
    elif low is not None and low > 0:
        status = "SUPPORTS_IMPROVEMENT"
    elif high is not None and high < 0:
        status = "SUPPORTS_HARM"
    else:
        status = "INCONCLUSIVE"
    return {"treatment_n": tn, "control_n": cn, "treatment_rate": p1, "control_rate": p0, "lift_pp": lift, "ci95": [low, high], "evidence_status": status}
