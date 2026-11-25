import json
import unittest
from unittest.mock import Mock
from uuid import UUID

from integrations.s3_client import S3Document, write_document_metadata


class WriteDocumentMetadataTests(unittest.TestCase):
    def test_writes_tenant_and_document_metadata_sidecar(self) -> None:
        client = Mock()
        document = S3Document(
            bucket="documents-bucket",
            object_key=(
                "documents/00000000-0000-0000-0000-000000000001/"
                "00000000-0000-0000-0000-000000000002/original.pdf"
            ),
            tenant_id=UUID("00000000-0000-0000-0000-000000000001"),
            document_id=UUID("00000000-0000-0000-0000-000000000002"),
        )

        write_document_metadata(document, client=client)

        params = client.put_object.call_args.kwargs
        self.assertEqual(params["Key"], f"{document.object_key}.metadata.json")
        self.assertEqual(
            json.loads(params["Body"]),
            {
                "metadataAttributes": {
                    "tenant_id": str(document.tenant_id),
                    "document_id": str(document.document_id),
                }
            },
        )
