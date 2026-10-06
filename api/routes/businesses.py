from __future__ import annotations

from fastapi import APIRouter, HTTPException

from core.business.entity import BusinessEntity
from core.jobs.runtime import business_repository

router = APIRouter(prefix="/businesses", tags=["businesses"])



@router.post("", response_model=BusinessEntity, status_code=201)
def create_business(business: BusinessEntity) -> BusinessEntity:
    if business_repository.get(business.id) is not None:
        raise HTTPException(status_code=409, detail="business already exists")
    return business_repository.save(business)


@router.get("/{business_id}", response_model=BusinessEntity)
def get_business(business_id: str) -> BusinessEntity:
    business = business_repository.get(business_id)
    if business is None:
        raise HTTPException(status_code=404, detail="business not found")
    return business
