# Document uploads

The development document API is available under `/api/v1/documents`. It uses
a fixed local-development tenant and user, and has no authentication. Do not
enable this mode in a deployed or shared environment. Set
`ENABLE_DEMO_UPLOADS=true` to enable it locally; the matching tenant and user
records are created on the first request.

Configure `S3_BUCKET_NAME` with the bucket name. The S3 client uses boto3's
standard credential chain, including `AWS_PROFILE` and AWS IAM Identity Center
profiles; for example, run `aws sso login --profile <profile>` before starting
the API. Do not put AWS credentials in application configuration.

`POST /api/v1/documents/upload-url` accepts a filename, `application/pdf`
content type, and file size from 1 byte through 20 MiB. It returns a
five-minute presigned PUT URL. Upload the PDF to that URL with the same
`Content-Type` header, then call
`POST /api/v1/documents/{document_id}/complete-upload`. Completion checks the
S3 object's actual size and content type before marking the record `uploaded`.

`GET /api/v1/documents` returns the development tenant's documents, newest
first. Pagination uses `limit` (1-100, default 50) and `offset` (default 0);
the response contains `items` and the unpaginated `total`.

## Knowledge Base queries

`POST /api/v1/chat/query` accepts `{"query": "..."}` and returns a generated
`answer` with source `citations`. It is available only when
`ENABLE_DEMO_UPLOADS=true`. Retrieval is currently unfiltered and may include
documents belonging to any tenant in the Knowledge Base; use only in a
trusted development environment. Configure `KB_ID`, `KB_NAME`, and
`BEDROCK_MODEL_ARN`; the API's AWS role must have permission to call
`bedrock:RetrieveAndGenerate` and invoke the configured generation model.
