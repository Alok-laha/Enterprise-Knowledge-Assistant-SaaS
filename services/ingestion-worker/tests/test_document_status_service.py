import unittest
from unittest.mock import Mock
from uuid import UUID

from services.document_status_service import (
    DocumentNotReadyError,
    process_document,
)
from integrations.s3_client import S3Document


class DocumentStatusServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = S3Document(
            bucket="documents-bucket",
            object_key=(
                "documents/00000000-0000-0000-0000-000000000001/"
                "00000000-0000-0000-0000-000000000002/original.pdf"
            ),
            tenant_id=UUID("00000000-0000-0000-0000-000000000001"),
            document_id=UUID("00000000-0000-0000-0000-000000000002"),
        )
        self.connection = Mock()
        self.engine = Mock()
        self.engine.begin.return_value.__enter__ = Mock(
            return_value=self.connection
        )
        self.engine.begin.return_value.__exit__ = Mock(return_value=False)
        self.handoff = Mock()

    def _select_row(self, status: str) -> None:
        result = Mock()
        result.mappings.return_value.one_or_none.return_value = {
            "id": self.document.document_id,
            "tenant_id": self.document.tenant_id,
            "s3_key": self.document.object_key,
            "status": status,
        }
        self.connection.execute.return_value = result

    def test_claims_uploaded_document_then_hands_off(self) -> None:
        self._select_row("uploaded")

        result = process_document(
            self.document,
            self.handoff,
            engine=self.engine,
        )

        self.assertEqual(result, "handed_off")
        self.assertEqual(self.connection.execute.call_count, 2)
        self.handoff.assert_called_once()

    def test_pending_upload_is_retryable_and_not_handed_off(self) -> None:
        self._select_row("pending_upload")

        with self.assertRaises(DocumentNotReadyError):
            process_document(self.document, self.handoff, engine=self.engine)

        self.handoff.assert_not_called()

    def test_failed_handoff_does_not_mark_document_processing(self) -> None:
        self._select_row("uploaded")
        self.handoff.side_effect = RuntimeError("Bedrock unavailable")

        with self.assertRaisesRegex(RuntimeError, "Bedrock unavailable"):
            process_document(self.document, self.handoff, engine=self.engine)

        self.assertEqual(self.connection.execute.call_count, 1)
