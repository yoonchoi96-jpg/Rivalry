from fastapi import APIRouter, HTTPException
from core.jobs.runtime import signal_repository
from core.signal.models import Signal
from core.qa.engine import validate_signal
from core.qa.models import QAResult

router=APIRouter(prefix="/signals",tags=["signals"])

@router.post("",response_model=Signal,status_code=201)
def create_signal(signal: Signal):
    qa=validate_signal(signal)
    if qa.status.value == "fail":
        raise HTTPException(status_code=400,detail=qa.issues)
    return signal_repository.save(signal)

@router.post("/qa",response_model=QAResult)
def signal_qa(signal: Signal):
    return validate_signal(signal)
