from __future__ import annotations
from core.evidence.models import Evidence
from core.measurement.models import Measurement
from core.observation.models import Observation
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
