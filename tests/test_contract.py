import pytest
from pydantic import ValidationError

from app.schemas import MedallioRefreshEvent


def test_success_only_contract():
    event = MedallioRefreshEvent(event_id="medallio:run-1", run_id="run-1")
    assert event.event_type == "medallio.table.refreshed.v1"
    with pytest.raises(ValidationError):
        MedallioRefreshEvent(event_id="medallio:run-2", run_id="run-2", status="FAILED")
