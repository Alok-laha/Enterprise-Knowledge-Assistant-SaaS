import os
import unittest
from unittest.mock import Mock, patch

from app.integrations.aws.knowledge_base import (
    KnowledgeBaseConfigurationError,
    query_knowledge_base,
)


class QueryKnowledgeBaseTests(unittest.TestCase):
    @patch.dict(
        os.environ,
        {
            "KB_ID": "kb-123",
            "KB_NAME": "test-kb",
            "BEDROCK_MODEL_ARN": "arn:aws:bedrock:region:account:model/model-id",
        },
        clear=True,
    )
    def test_queries_without_tenant_filter_and_returns_citations(self) -> None:
        client = Mock()
        client.retrieve_and_generate.return_value = {
            "output": {"text": "Generated answer"},
            "citations": [
                {
                    "retrievedReferences": [
                        {
                            "content": {"text": "Source excerpt"},
                            "location": {
                                "s3Location": {"uri": "s3://bucket/document.pdf"}
                            },
                        }
                    ]
                }
            ],
        }
        result = query_knowledge_base(
            "What is in this document?",
            client=client,
        )

        self.assertEqual(result["answer"], "Generated answer")
        self.assertEqual(
            result["citations"],
            [
                {
                    "source_uri": "s3://bucket/document.pdf",
                    "excerpt": "Source excerpt",
                }
            ],
        )
        config = client.retrieve_and_generate.call_args.kwargs[
            "retrieveAndGenerateConfiguration"
        ]["knowledgeBaseConfiguration"]
        self.assertNotIn("retrievalConfiguration", config)

    @patch.dict(os.environ, {"KB_ID": "kb-123"}, clear=True)
    def test_requires_generation_model_arn(self) -> None:
        with self.assertRaises(KnowledgeBaseConfigurationError):
            query_knowledge_base(
                "question",
                client=Mock(),
            )
