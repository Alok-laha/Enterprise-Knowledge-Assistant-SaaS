import logging
from typing import Any

from integrations.sqs_client import InvalidSqsMessage, parse_sqs_message
from services.document_status_service import (
    DocumentNotReadyError,
    process_document,
)
from services.ingestion_service import handoff_document

logger = logging.getLogger(__name__)


def lambda_handler(
    event: dict[str, Any],
    context: Any,
) -> dict[str, list[dict[str, str]]]:
    records = event.get("Records")
    if not isinstance(records, list):
        raise ValueError("Lambda event must contain an SQS Records list")

    failures: list[dict[str, str]] = []

    for record in records:
        if (
            not isinstance(record, dict)
            or not isinstance(record.get("messageId"), str)
            or not record["messageId"]
        ):
            raise ValueError("SQS record must contain a messageId")
        message_id = record.get("messageId")
        try:
            s3_objects = parse_sqs_message(record)
            for s3_object in s3_objects:
                process_document(s3_object, handoff=handoff_document)
        except (InvalidSqsMessage, DocumentNotReadyError):
            logger.exception(
                "Unable to process SQS message messageId=%s",
                message_id,
            )
            failures.append({"itemIdentifier": message_id})
        except Exception:
            logger.exception(
                "Unexpected error processing SQS message messageId=%s",
                message_id,
            )
            failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": failures}
