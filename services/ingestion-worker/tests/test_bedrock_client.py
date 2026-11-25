import os
import unittest
from unittest.mock import Mock, patch
from uuid import UUID

from integrations.bedrock_client import (
    BedrockConfigurationError,
    start_ingestion_job,
)


class StartIngestionJobTests(unittest.TestCase):
    @patch.dict(os.environ, {"KB_ID": "kb-123"}, clear=True)
    def test_discovers_sole_source_and_uses_stable_client_token(self) -> None:
        client = Mock()
        client.list_data_sources.return_value = {
            "dataSourceSummaries": [{"dataSourceId": "source-123"}]
        }
        client.start_ingestion_job.return_value = {
            "ingestionJob": {"ingestionJobId": "job-123"}
        }
        with patch(
            "integrations.bedrock_client._client",
            return_value=client,
        ):
            job_id = start_ingestion_job(
                UUID("00000000-0000-0000-0000-000000000002")
            )

        self.assertEqual(job_id, "job-123")
        self.assertEqual(
            client.start_ingestion_job.call_args.kwargs["clientToken"],
            "00000000-0000-0000-0000-000000000002",
        )

    @patch.dict(os.environ, {"KB_ID": "kb-123"}, clear=True)
    def test_requires_source_id_when_multiple_sources_exist(self) -> None:
        client = Mock()
        client.list_data_sources.return_value = {
            "dataSourceSummaries": [
                {"dataSourceId": "source-1"},
                {"dataSourceId": "source-2"},
            ]
        }
        with patch(
            "integrations.bedrock_client._client",
            return_value=client,
        ):
            with self.assertRaises(BedrockConfigurationError):
                start_ingestion_job(
                    UUID("00000000-0000-0000-0000-000000000002")
                )
        client.start_ingestion_job.assert_not_called()

    @patch.dict(
        os.environ,
        {"KB_ID": "kb-123", "KB_DATA_SOURCE_ID": "source-configured"},
        clear=True,
    )
    def test_uses_configured_source_without_discovery(self) -> None:
        client = Mock()
        client.start_ingestion_job.return_value = {
            "ingestionJob": {"ingestionJobId": "job-123"}
        }
        with patch(
            "integrations.bedrock_client._client",
            return_value=client,
        ):
            start_ingestion_job(UUID("00000000-0000-0000-0000-000000000002"))

        client.list_data_sources.assert_not_called()
        self.assertEqual(
            client.start_ingestion_job.call_args.kwargs["dataSourceId"],
            "source-configured",
        )
