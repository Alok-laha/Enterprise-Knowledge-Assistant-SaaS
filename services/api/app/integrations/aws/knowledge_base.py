import logging
import os
from functools import lru_cache
from typing import Any

import boto3
from botocore.client import BaseClient

logger = logging.getLogger(__name__)


class KnowledgeBaseConfigurationError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _client() -> BaseClient:
    return boto3.client(
        "bedrock-agent-runtime",
        region_name=os.getenv("AWS_REGION"),
    )


def _required_setting(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise KnowledgeBaseConfigurationError(f"{name} must be configured")
    return value


def query_knowledge_base(
    query: str,
    *,
    client: BaseClient | None = None,
) -> dict[str, Any]:
    knowledge_base_id = _required_setting("KB_ID")
    model_arn = _required_setting("BEDROCK_MODEL_ARN")
    logger.info(
        "Querying Bedrock Knowledge Base name=%s",
        os.getenv("KB_NAME", knowledge_base_id),
    )
    response = (client or _client()).retrieve_and_generate(
        input={"text": query},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": knowledge_base_id,
                "modelArn": model_arn,
            },
        },
    )

    output = response.get("output")
    if not isinstance(output, dict) or not isinstance(output.get("text"), str):
        raise RuntimeError("Bedrock did not return a generated answer")

    citations: list[dict[str, str | None]] = []
    for citation in response.get("citations", []):
        if not isinstance(citation, dict):
            continue
        references = citation.get("retrievedReferences", [])
        if not isinstance(references, list):
            continue
        for reference in references:
            if not isinstance(reference, dict):
                continue
            content = reference.get("content")
            location = reference.get("location")
            s3_location = (
                location.get("s3Location")
                if isinstance(location, dict)
                else None
            )
            citations.append(
                {
                    "source_uri": (
                        s3_location.get("uri")
                        if isinstance(s3_location, dict)
                        else None
                    ),
                    "excerpt": (
                        content.get("text")
                        if isinstance(content, dict)
                        else None
                    ),
                }
            )

    return {"answer": output["text"], "citations": citations}