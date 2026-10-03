from fastapi import APIRouter
from engines.change_detection.models import Change
from engines.change_detection.service import ChangeService
router=APIRouter(prefix="/changes",tags=["changes"])
service=ChangeService()
@router.get("",response_model=list[Change])
def list_changes(): return service.list()
