import os
from functools import lru_cache
from typing import Any
from uuid import UUID

import boto3
from botocore.client import BaseClient
from botocore.config import Config


class S3ConfigurationError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _client() -> BaseClient:
    session = boto3.Session()
    region = (
        os.getenv("AWS_REGION")
    )
    if not region:
        raise S3ConfigurationError("An AWS region must be configured")

    return session.client(
        "s3",
        region_name=region,
        endpoint_url=f"https://s3.{region}.amazonaws.com",
        config=Config(s3={"addressing_style": "virtual"}),
    )


def _bucket_name() -> str:
    bucket_name = os.getenv("S3_BUCKET_NAME")
    if not bucket_name:
        raise S3ConfigurationError("S3_BUCKET_NAME must be configured")
    return bucket_name


def document_object_key(tenant_id: UUID, document_id: UUID) -> str:
    return f"documents/{tenant_id}/{document_id}/original.pdf"


def generate_upload_url(
    s3_key: str,
    content_type: str,
    expires_in: int = 300,
) -> str:
    return _client().generate_presigned_url(
        "put_object",
        Params={
            "Bucket": _bucket_name(),
            "Key": s3_key,
            "ContentType": content_type,
        },
        ExpiresIn=expires_in,
        HttpMethod="PUT",
    )


def generate_download_url(s3_key: str, expires_in: int = 300) -> str:
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": _bucket_name(), "Key": s3_key},
        ExpiresIn=expires_in,
        HttpMethod="GET",
    )


def delete_object(s3_key: str) -> None:
    _client().delete_object(Bucket=_bucket_name(), Key=s3_key)


def head_object(s3_key: str) -> dict[str, Any]:
    return _client().head_object(Bucket=_bucket_name(), Key=s3_key)