import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import unquote_plus
from uuid import UUID

import boto3
from botocore.client import BaseClient


class InvalidS3Event(ValueError):
    pass


@dataclass(frozen=True)
class S3Document:
    bucket: str
    object_key: str
    tenant_id: UUID
    document_id: UUID


def write_document_metadata(
    document: S3Document,
    *,
    client: BaseClient | None = None,
) -> None:
    s3 = client or boto3.client("s3", region_name=os.getenv("AWS_REGION"))
    s3.put_object(
        Bucket=document.bucket,
        Key=f"{document.object_key}.metadata.json",
        ContentType="application/json",
        Body=json.dumps(
            {
                "metadataAttributes": {
                    "tenant_id": str(document.tenant_id),
                    "document_id": str(document.document_id),
                }
            }
        ).encode("utf-8"),
    )


def document_from_event(record: Mapping[str, object]) -> S3Document | None:
    """Parse an S3 PUT event; return None for non-PUT notifications."""
    if not str(record.get("eventName", "")).startswith("ObjectCreated:Put"):
        return None

    s3 = record.get("s3")
    if not isinstance(s3, Mapping):
        raise InvalidS3Event("S3 event is missing its bucket or object key")
    bucket_details = s3.get("bucket")
    object_details = s3.get("object")
    if not isinstance(bucket_details, Mapping) or not isinstance(
        object_details, Mapping
    ):
        raise InvalidS3Event("S3 event is missing its bucket or object key")

    bucket = bucket_details.get("name")
    encoded_key = object_details.get("key")
    if not isinstance(bucket, str) or not isinstance(encoded_key, str):
        raise InvalidS3Event("S3 event bucket and object key must be strings")

    expected_bucket = os.getenv("S3_BUCKET_NAME")
    if not expected_bucket:
        raise InvalidS3Event("S3_BUCKET_NAME must be configured")
    if bucket != expected_bucket:
        raise InvalidS3Event("S3 event bucket does not match S3_BUCKET_NAME")

    object_key = unquote_plus(encoded_key)
    parts = object_key.split("/")
    if len(parts) != 4 or parts[0] != "documents" or parts[3] != "original.pdf":
        return None

    try:
        tenant_id = UUID(parts[1])
        document_id = UUID(parts[2])
    except ValueError as exc:
        raise InvalidS3Event("S3 object key contains an invalid document identity") from exc

    return S3Document(
        bucket=bucket,
        object_key=object_key,
        tenant_id=tenant_id,
        document_id=document_id,
    )
