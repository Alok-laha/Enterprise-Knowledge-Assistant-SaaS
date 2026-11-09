from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate, TenantRead

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
def register_tenant(
    payload: TenantCreate,
    db: Session = Depends(get_db),
) -> Tenant:
    existing_tenant = db.scalar(select(Tenant).where(Tenant.name == payload.name))
    if existing_tenant is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tenant with this name already exists",
        )

    tenant = Tenant(name=payload.name, type=payload.type.value)
    db.add(tenant)

    try:
        db.commit()
        db.refresh(tenant)
    except IntegrityError as exc:
        db.rollback()
        constraint_name = getattr(
            getattr(exc.orig, "diag", None), "constraint_name", None
        )
        if constraint_name == "uq_tenants_name":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A tenant with this name already exists",
            ) from exc
        raise

    return tenant
