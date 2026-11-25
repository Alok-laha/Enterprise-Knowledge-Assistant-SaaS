# Document ingestion worker

The Lambda handler is `handlers.document_created.lambda_handler` when the
contents of this directory are used as the deployment package root. It accepts
SQS events containing S3 `ObjectCreated:Put` notifications for keys shaped as
`documents/{tenant_id}/{document_id}/original.pdf`.

The worker checks the configured `S3_BUCKET_NAME`, derives the tenant and
document UUIDs from the key, and verifies the matching row in PostgreSQL.
Only documents with status `uploaded` are claimed; `pending_upload` messages are
retried to handle the race between the S3 notification and upload completion.
The status update and downstream handoff run in one database transaction.

Configure `DATABASE_URL`, `S3_BUCKET_NAME`, `KB_ID`, and `AWS_REGION` in the
Lambda environment. The worker discovers the Knowledge Base's sole data source;
set `KB_DATA_SOURCE_ID` when it has zero or multiple sources. For local runs,
the worker loads `services/api/.env` when present. Its execution role needs
permission to reach PostgreSQL and S3 through the configured network and
security-group path, and permissions for `s3:PutObject`,
`bedrock:ListDataSources`, and `bedrock:StartIngestionJob`.

Before starting ingestion, the worker writes an S3 metadata sidecar containing
the tenant and document IDs. The Knowledge Base query endpoint filters on the
`tenant_id` metadata attribute. The worker ignores PUT notifications for these
sidecars and unrelated objects. The Lambda SQS event source mapping must enable
`ReportBatchItemFailures`; otherwise the returned partial-batch retry response
is ignored. Set the queue's redrive policy to the configured DLQ.

Install `requirements.txt` in the deployment artifact along with this
directory's Python packages.
