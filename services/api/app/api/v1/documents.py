import os
from uuid import UUID, uuid4

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.integrations.aws import s3_client
from app.models.document import Document
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.document import (
    MAX_PDF_SIZE_BYTES,
    DocumentItem,
    DocumentListResponse,
    DocumentUploadRequest,
    DocumentUploadUrlResponse,
)

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_URL_EXPIRES_IN = 300
DEMO_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
DEMO_USER_ID = UUID("00000000-0000-0000-0000-000000000002")


def _demo_identity(db: Session) -> tuple[UUID, UUID]:
    if os.getenv("ENABLE_DEMO_UPLOADS", "").lower() != "true":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Set ENABLE_DEMO_UPLOADS=true to enable the unauthenticated "
            "development document API",
        )

    tenant = db.get(Tenant, DEMO_TENANT_ID)
    user = db.get(User, DEMO_USER_ID)
    needs_commit = False
    if tenant is None:
        tenant = Tenant(
            id=DEMO_TENANT_ID,
            name="Local development demo",
            type="Start-up",
        )
        db.add(tenant)
        needs_commit = True
    if user is None:
        user = User(
            id=DEMO_USER_ID,
            cognito_sub="local-development-demo",
            email="local-development-demo@example.invalid",
            name="Local development demo",
        )
        db.add(user)
        needs_commit = True

    if needs_commit:
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            tenant = db.get(Tenant, DEMO_TENANT_ID)
            user = db.get(User, DEMO_USER_ID)
            if tenant is None or user is None:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Unable to initialize the development tenant",
                ) from exc

    return tenant.id, user.id


def _s3_failure() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Unable to access document storage",
    )


@router.post(
    "/upload-url",
    response_model=DocumentUploadUrlResponse,
)
def create_upload_url(
    payload: DocumentUploadRequest,
    db: Session = Depends(get_db),
) -> DocumentUploadUrlResponse:
    tenant_id, user_id = _demo_identity(db)
    document_id = uuid4()
    s3_key = s3_client.document_object_key(tenant_id, document_id)

    try:
        upload_url = s3_client.generate_upload_url(
            s3_key,
            payload.content_type,
            expires_in=UPLOAD_URL_EXPIRES_IN,
        )
    except s3_client.S3ConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document storage is not configured",
        ) from exc
    except (BotoCoreError, ClientError) as exc:
        raise _s3_failure() from exc

    document = Document(
        id=document_id,
        tenant_id=tenant_id,
        uploaded_by=user_id,
        filename=payload.filename,
        s3_key=s3_key,
        content_type=payload.content_type,
        file_size=payload.file_size,
        status="pending_upload",
    )
    db.add(document)
    db.commit()

    return DocumentUploadUrlResponse(
        document_id=document_id,
        upload_url=upload_url,
        expires_in=UPLOAD_URL_EXPIRES_IN,
    )


@router.post(
    "/{document_id}/complete-upload",
    response_model=DocumentItem,
)
def complete_upload(
    document_id: UUID,
    db: Session = Depends(get_db),
) -> DocumentItem:
    tenant_id, _ = _demo_identity(db)
    document = db.scalar(
        select(Document)
        .where(
            Document.id == document_id,
            Document.tenant_id == tenant_id,
        )
        .with_for_update()
    )
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    if document.status != "pending_upload":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is not awaiting upload",
        )

    try:
        object_metadata = s3_client.head_object(document.s3_key)
    except s3_client.S3ConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document storage is not configured",
        ) from exc
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        status_code = exc.response.get("ResponseMetadata", {}).get(
            "HTTPStatusCode"
        )
        if error_code in {"404", "NoSuchKey", "NotFound"} or status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Uploaded object was not found",
            ) from exc
        raise _s3_failure() from exc
    except BotoCoreError as exc:
        raise _s3_failure() from exc

    if (
        object_metadata.get("ContentLength") != document.file_size
        or object_metadata.get("ContentType") != document.content_type
        or document.file_size > MAX_PDF_SIZE_BYTES
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded object size or content type does not match the request",
        )

    document.status = "uploaded"
    db.commit()
    db.refresh(document)
    return DocumentItem.model_validate(document)


@router.get("", response_model=DocumentListResponse)
def list_documents(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    tenant_id, _ = _demo_identity(db)
    tenant_filter = Document.tenant_id == tenant_id
    total = db.scalar(
        select(func.count()).select_from(Document).where(tenant_filter)
    )
    documents = db.scalars(
        select(Document)
        .where(tenant_filter)
        .order_by(Document.created_at.desc(), Document.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return DocumentListResponse(
        items=[DocumentItem.model_validate(document) for document in documents],
        total=total or 0,
    )