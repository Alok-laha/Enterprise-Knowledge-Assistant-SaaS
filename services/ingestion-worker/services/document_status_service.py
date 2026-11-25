import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable
from uuid import UUID

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from integrations.s3_client import S3Document

logger = logging.getLogger(__name__)

load_dotenv(Path(__file__).resolve().parents[2] / "api" / ".env")


class DocumentNotReadyError(RuntimeError):
    """Raised when an S3 event arrives before upload completion is recorded."""


@dataclass(frozen=True)
class DocumentReference:
    document_id: UUID
    tenant_id: UUID
    bucket: str
    object_key: str


@lru_cache(maxsize=1)
def _engine() -> Engine:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be configured")
    return create_engine(database_url, pool_pre_ping=True, pool_recycle=300)


def _locked_document(
    connection: Connection,
    s3_document: S3Document,
) -> dict[str, object] | None:
    result = connection.execute(
        text(
            """
            SELECT id, tenant_id, s3_key, status
            FROM documents
            WHERE id = :document_id
              AND tenant_id = :tenant_id
              AND s3_key = :object_key
            FOR UPDATE
            """
        ),
        {
            "document_id": s3_document.document_id,
            "tenant_id": s3_document.tenant_id,
            "object_key": s3_document.object_key,
        },
    )
    row = result.mappings().one_or_none()
    return dict(row) if row is not None else None


def process_document(
    s3_document: S3Document,
    handoff: Callable[[DocumentReference], str],
    *,
    engine: Engine | None = None,
) -> str:
    """Claim an uploaded document and hand it off within the same DB transaction."""
    db_engine = engine or _engine()
    with db_engine.begin() as connection:
        document = _locked_document(connection, s3_document)
        if document is None:
            logger.warning("Ignoring S3 event for a document not found in PostgreSQL")
            return "not_found"

        status = document["status"]
        if status == "pending_upload":
            raise DocumentNotReadyError(
                "Document upload completion has not been recorded yet"
            )
        if status != "uploaded":
            logger.info("Ignoring S3 event for a document with status=%s", status)
            return "ineligible"

        ingestion_job_id = handoff(
            DocumentReference(
                document_id=s3_document.document_id,
                tenant_id=s3_document.tenant_id,
                bucket=s3_document.bucket,
                object_key=s3_document.object_key,
            )
        )
        connection.execute(
            text(
                """
                UPDATE documents
                SET status = 'processing'
                WHERE id = :document_id
                  AND tenant_id = :tenant_id
                  AND status = 'uploaded'
                """
            ),
            {
                "document_id": s3_document.document_id,
                "tenant_id": s3_document.tenant_id,
            },
        )
        logger.info(
            "Started Bedrock ingestion job=%s document_id=%s",
            ingestion_job_id,
            s3_document.document_id,
        )
    return "handed_off"
