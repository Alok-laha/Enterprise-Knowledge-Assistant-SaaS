import os
from functools import lru_cache
from typing import Any
from uuid import UUID

import boto3
from botocore.client import BaseClient


class BedrockConfigurationError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _client() -> BaseClient:
    return boto3.client("bedrock-agent", region_name=os.getenv("AWS_REGION"))


def _knowledge_base_id() -> str:
    knowledge_base_id = os.getenv("KB_ID")
    if not knowledge_base_id:
        raise BedrockConfigurationError("KB_ID must be configured")
    return knowledge_base_id


def _data_source_id(client: BaseClient, knowledge_base_id: str) -> str:
    configured_id = os.getenv("KB_DATA_SOURCE_ID")
    if configured_id:
        return configured_id

    data_source_ids: list[str] = []
    next_token: str | None = None
    while True:
        params: dict[str, Any] = {
            "knowledgeBaseId": knowledge_base_id,
            "maxResults": 100,
        }
        if next_token:
            params["nextToken"] = next_token
        response = client.list_data_sources(**params)
        data_source_ids.extend(
            item["dataSourceId"]
            for item in response.get("dataSourceSummaries", [])
            if item.get("dataSourceId")
        )
        next_token = response.get("nextToken")
        if not next_token:
            break

    if len(data_source_ids) != 1:
        raise BedrockConfigurationError(
            "Set KB_DATA_SOURCE_ID when the Knowledge Base has zero or multiple "
            "data sources"
        )
    return data_source_ids[0]


def start_ingestion_job(document_id: UUID) -> str:
    knowledge_base_id = _knowledge_base_id()
    client = _client()
    data_source_id = _data_source_id(client, knowledge_base_id)
    response = client.start_ingestion_job(
        knowledgeBaseId=knowledge_base_id,
        dataSourceId=data_source_id,
        clientToken=str(document_id),
        description=f"Ingest uploaded document {document_id}",
    )
    job = response.get("ingestionJob")
    if not isinstance(job, dict) or not isinstance(job.get("ingestionJobId"), str):
        raise RuntimeError("Bedrock did not return an ingestion job ID")
    return job["ingestionJobId"]
