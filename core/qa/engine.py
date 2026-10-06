from __future__ import annotations
from core.decision.models import DecisionRecommendation
from core.evidence.models import Evidence
from core.measurement.models import Measurement
from core.observation.models import Observation
from core.signal.models import Signal
from .models import QAResult, QAStage, QAStatus

def validate_source(url: str | None, reliability: float, coverage: float) -> QAResult:
    issues=[]
    if not url: issues.append("source URL is missing")
    if reliability < 0.5: issues.append("source reliability is below 0.5")
    if coverage < 0.5: issues.append("source coverage is below 0.5")
    score=max(0.0, 1.0 - 0.2*len(issues))
    return QAResult(stage=QAStage.SOURCE,status=QAStatus.FAIL if len(issues)>=2 else QAStatus.WARN if issues else QAStatus.PASS,score=score,checks=["url","reliability","coverage"],issues=issues)

def validate_evidence(evidence: Evidence) -> QAResult:
    issues=[]
    if not evidence.statement.strip(): issues.append("statement is empty")
    if evidence.confidence < 0.5: issues.append("evidence confidence is below 0.5")
    return QAResult(stage=QAStage.EXTRACTION,status=QAStatus.WARN if issues else QAStatus.PASS,score=max(0.0,1-0.3*len(issues)),checks=["statement","confidence"],issues=issues,evidence_ids=[evidence.id])

def validate_observation(observation: Observation) -> QAResult:
    issues=[]
    if observation.normalized_value is not None and not observation.unit: issues.append("normalized value requires a unit")
    if observation.confidence < 0.5: issues.append("observation confidence is below 0.5")
    return QAResult(stage=QAStage.NORMALIZATION,status=QAStatus.WARN if issues else QAStatus.PASS,score=max(0.0,1-0.3*len(issues)),checks=["normalized_value_unit","confidence"],issues=issues,observation_ids=[observation.id])

def validate_measurement(measurement: Measurement) -> QAResult:
    issues=[]
    if not measurement.formula.strip(): issues.append("formula is empty")
    if not measurement.observation_ids: issues.append("measurement has no observation lineage")
    if measurement.confidence < 0.5: issues.append("measurement confidence is below 0.5")
    return QAResult(stage=QAStage.MEASUREMENT,status=QAStatus.FAIL if "formula is empty" in issues or "measurement has no observation lineage" in issues else QAStatus.WARN if issues else QAStatus.PASS,score=max(0.0,1-0.3*len(issues)),checks=["formula","observation_lineage","confidence"],issues=issues,measurement_ids=[measurement.id])

def validate_signal(signal: Signal) -> QAResult:
    issues=[]
    if signal.signal_kind.value == "change" and signal.reference_value is None: issues.append("change signal requires a reference value")
    if signal.reference_value is not None and signal.delta is None: issues.append("reference value requires delta")
    if not signal.observation_ids and not signal.measurement_ids: issues.append("signal has no observation or measurement lineage")
    if signal.confidence < 0.5: issues.append("signal confidence is below 0.5")
    hard_fail={"change signal requires a reference value","reference value requires delta","signal has no observation or measurement lineage"}
    status=QAStatus.FAIL if any(issue in hard_fail for issue in issues) else QAStatus.WARN if issues else QAStatus.PASS
    return QAResult(stage=QAStage.SIGNAL,status=status,score=max(0.0,1-0.25*len(issues)),checks=["reference","delta","lineage","confidence"],issues=issues,observation_ids=signal.observation_ids,measurement_ids=signal.measurement_ids)

def validate_recommendation(recommendation: DecisionRecommendation) -> QAResult:
    issues=[]
    if not recommendation.business_id.strip(): issues.append("recommendation business_id is empty")
    if not recommendation.impact_id.strip(): issues.append("recommendation impact_id is empty")
    if not recommendation.signal_id.strip(): issues.append("recommendation signal_id is empty")
    if not recommendation.factor_key.strip(): issues.append("recommendation factor_key is empty")
    if not recommendation.action.strip(): issues.append("recommendation action is empty")
    if not recommendation.rationale.strip(): issues.append("recommendation rationale is empty")
    if recommendation.policy_id is None or not recommendation.policy_id.strip(): issues.append("recommendation policy_id is missing")
    hard_fail={"recommendation business_id is empty","recommendation impact_id is empty","recommendation signal_id is empty","recommendation factor_key is empty","recommendation action is empty","recommendation policy_id is missing"}
    status=QAStatus.FAIL if any(issue in hard_fail for issue in issues) else QAStatus.WARN if issues else QAStatus.PASS
    return QAResult(stage=QAStage.RECOMMENDATION,status=status,score=max(0.0,1-0.2*len(issues)),checks=["business","impact","signal","factor","action","rationale","policy"],issues=issues)
