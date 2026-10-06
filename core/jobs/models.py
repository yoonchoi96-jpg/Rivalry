from __future__ import annotations
from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4
from pydantic import BaseModel, Field

class JobStatus(StrEnum):
    QUEUED="queued"; RUNNING="running"; SUCCEEDED="succeeded"; FAILED="failed"

class JobType(StrEnum):
    COLLECT_COMPETITOR="collect_competitor"; PROCESS_INTELLIGENCE="process_intelligence"
    BUILD_ALERT="build_alert"; ANALYZE_REVIEWS="analyze_reviews"; GENERATE_PREDICTION="generate_prediction"
    EXECUTE_RESEARCH="execute_research"; INGEST_RESEARCH="ingest_research"; GENERATE_DECISION="generate_decision"; DISPATCH_ACTION="dispatch_action"

class Job(BaseModel):
    id:str=Field(default_factory=lambda:str(uuid4()))
    type:JobType
    payload:dict[str,object]=Field(default_factory=dict)
    idempotency_key:str|None=None
    status:JobStatus=JobStatus.QUEUED
    created_at:str=Field(default_factory=lambda:datetime.now(timezone.utc).isoformat())
    started_at:str|None=None; finished_at:str|None=None; error:str|None=None
    result:dict[str,object]|None=None
    attempts:int=Field(default=0,ge=0); max_attempts:int=Field(default=3,ge=1,le=10)
    next_attempt_at:str|None=None; enqueue_version:int=Field(default=0,ge=0)
