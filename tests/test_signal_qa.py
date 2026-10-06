from core.qa.engine import validate_signal
from core.qa.models import QAStatus
from core.signal.models import Signal, SignalDirection, SignalKind

def test_signal_qa_requires_lineage():
    result=validate_signal(Signal(
        id="sig-qa",entity_id="biz-1",definition_key="fx_exposure",
        signal_kind=SignalKind.CHANGE,direction=SignalDirection.UP,
        current_value=1.1,reference_value=1.0,delta=.1,delta_pct=10,
        detected_at="2026-10-06T00:00:00Z",confidence=.9,
    ))
    assert result.status == QAStatus.FAIL

def test_signal_qa_passes_with_lineage():
    result=validate_signal(Signal(
        id="sig-qa-ok",entity_id="biz-1",definition_key="fx_exposure",
        signal_kind=SignalKind.CHANGE,direction=SignalDirection.UP,
        current_value=1.1,reference_value=1.0,delta=.1,delta_pct=10,
        detected_at="2026-10-06T00:00:00Z",measurement_ids=["m-1"],confidence=.9,
    ))
    assert result.status == QAStatus.PASS
