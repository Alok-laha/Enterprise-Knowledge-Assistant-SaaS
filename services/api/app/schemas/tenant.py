from datetime import datetime
from enum import Enum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints


class TenantType(str, Enum):
    START_UP = "Start-up"
    ENTERPRISE = "Enterprise"
    NON_PROFIT = "Non-profit"
    GOVERNMENT = "Government"
    MID_SIZE = "Mid-size"
    SMALL_BUSINESS = "Small Business"


class TenantCreate(BaseModel):
    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)
    ]
    type: TenantType


class TenantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    type: TenantType
    created_at: datetime
