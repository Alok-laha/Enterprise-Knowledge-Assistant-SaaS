import json
from typing import Any

from integrations.s3_client import InvalidS3Event, S3Document, document_from_event


class InvalidSqsMessage(ValueError):
    pass


def parse_sqs_message(record: dict[str, Any]) -> list[S3Document]:
    try:
        body = json.loads(record["body"])
        s3_records = body["Records"]
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise InvalidSqsMessage("SQS body is not a valid S3 notification") from exc

    if not isinstance(s3_records, list):
        raise InvalidSqsMessage("S3 notification Records must be a list")

    documents: list[S3Document] = []
    try:
        for s3_record in s3_records:
            if not isinstance(s3_record, dict):
                raise InvalidS3Event("S3 notification record must be an object")
            document = document_from_event(s3_record)
            if document is not None:
                documents.append(document)
    except InvalidS3Event as exc:
        raise InvalidSqsMessage(str(exc)) from exc
    return documents
