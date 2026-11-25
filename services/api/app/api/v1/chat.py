import logging

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.documents import _demo_identity
from app.db.database import get_db
from app.integrations.aws.knowledge_base import (
    KnowledgeBaseConfigurationError,
    query_knowledge_base,
)
from app.schemas.chat import QueryRequest, QueryResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/query", response_model=QueryResponse)
def query(
    payload: QueryRequest,
    db: Session = Depends(get_db),
) -> QueryResponse:
    _demo_identity(db)
    try:
        result = query_knowledge_base(payload.query)
    except KnowledgeBaseConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Knowledge Base query is not configured",
        ) from exc
    except (BotoCoreError, ClientError) as exc:
        logger.exception("Bedrock Knowledge Base query failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to query the Knowledge Base",
        ) from exc

    return QueryResponse.model_validate(result)