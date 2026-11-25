import os
import unittest
from unittest.mock import patch
from uuid import UUID

from integrations.s3_client import InvalidS3Event, document_from_event


class DocumentFromEventTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tenant_id = UUID("00000000-0000-0000-0000-000000000001")
        self.document_id = UUID("00000000-0000-0000-0000-000000000002")
        self.event = {
            "eventName": "ObjectCreated:Put",
            "s3": {
                "bucket": {"name": "documents-bucket"},
                "object": {
                    "key": (
                        f"documents/{self.tenant_id}/{self.document_id}/original.pdf"
                    )
                },
            },
        }

    @patch.dict(os.environ, {"S3_BUCKET_NAME": "documents-bucket"})
    def test_extracts_document_and_tenant_from_put_event(self) -> None:
        parsed = document_from_event(self.event)

        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.tenant_id, self.tenant_id)
        self.assertEqual(parsed.document_id, self.document_id)
        self.assertEqual(
            parsed.object_key,
            f"documents/{self.tenant_id}/{self.document_id}/original.pdf",
        )

    @patch.dict(os.environ, {"S3_BUCKET_NAME": "documents-bucket"})
    def test_decodes_url_encoded_key(self) -> None:
        self.event["s3"]["object"]["key"] = (
            f"documents%2F{self.tenant_id}%2F{self.document_id}%2Foriginal.pdf"
        )
        parsed = document_from_event(self.event)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(
            parsed.object_key,
            f"documents/{self.tenant_id}/{self.document_id}/original.pdf",
        )

    def test_ignores_non_put_notifications(self) -> None:
        self.event["eventName"] = "ObjectRemoved:Delete"
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(document_from_event(self.event))

    @patch.dict(os.environ, {"S3_BUCKET_NAME": "documents-bucket"})
    def test_ignores_metadata_sidecar_put_notifications(self) -> None:
        self.event["s3"]["object"]["key"] += ".metadata.json"
        self.assertIsNone(document_from_event(self.event))

    @patch.dict(os.environ, {"S3_BUCKET_NAME": "another-bucket"})
    def test_rejects_bucket_mismatch(self) -> None:
        with self.assertRaises(InvalidS3Event):
            document_from_event(self.event)
