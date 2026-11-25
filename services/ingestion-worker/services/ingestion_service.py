from integrations.bedrock_client import start_ingestion_job
from integrations.s3_client import S3Document, write_document_metadata
from services.document_status_service import DocumentReference


def handoff_document(document: DocumentReference) -> str:
    """Write tenant metadata and start a Bedrock Knowledge Base sync job."""
    write_document_metadata(
        S3Document(
            bucket=document.bucket,
            object_key=document.object_key,
            tenant_id=document.tenant_id,
            document_id=document.document_id,
        )
    )
    return start_ingestion_job(document.document_id)
