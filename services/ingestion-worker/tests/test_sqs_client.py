import json
import os
import unittest
from unittest.mock import patch
from uuid import UUID

from integrations.sqs_client import InvalidSqsMessage, parse_sqs_message


class ParseSqsMessageTests(unittest.TestCase):
    @patch.dict(os.environ, {"S3_BUCKET_NAME": "documents-bucket"})
    def test_parses_s3_notification_inside_sqs_body(self) -> None:
        tenant_id = UUID("00000000-0000-0000-0000-000000000001")
        document_id = UUID("00000000-0000-0000-0000-000000000002")
        record = {
            "body": json.dumps(
                {
                    "Records": [
                        {
                            "eventName": "ObjectCreated:Put",
                            "s3": {
                                "bucket": {"name": "documents-bucket"},
                                "object": {
                                    "key": (
                                        f"documents/{tenant_id}/{document_id}/"
                                        "original.pdf"
                                    )
                                },
                            },
                        }
                    ]
                }
            )
        }

        parsed = parse_sqs_message(record)

        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].tenant_id, tenant_id)
        self.assertEqual(parsed[0].document_id, document_id)

    def test_rejects_non_s3_message_body(self) -> None:
        with self.assertRaises(InvalidSqsMessage):
            parse_sqs_message({"body": "not-json"})
