import unittest
from unittest.mock import Mock, patch

from handlers.document_created import lambda_handler
from integrations.sqs_client import InvalidSqsMessage


class DocumentCreatedHandlerTests(unittest.TestCase):
    @patch("handlers.document_created.process_document")
    @patch("handlers.document_created.parse_sqs_message")
    def test_returns_failed_message_for_retry(
        self,
        parse_sqs_message: Mock,
        process_document: Mock,
    ) -> None:
        parse_sqs_message.side_effect = InvalidSqsMessage("invalid event")
        result = lambda_handler(
            {"Records": [{"messageId": "message-1", "body": "invalid"}]},
            None,
        )

        self.assertEqual(
            result,
            {"batchItemFailures": [{"itemIdentifier": "message-1"}]},
        )
        process_document.assert_not_called()
