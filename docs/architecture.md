Project: Enterprise Knowledge Assistant

Architecture:
- Modular monolith
- Multi-tenant SaaS
- REST API

Frontend:
- Next.js
- TypeScript

Backend:
- Python
- FastAPI

Database:
- PostgreSQL

AI:
- Amazon Bedrock
- Bedrock Knowledge Bases

Storage:
- Amazon S3

Authentication:
- Amazon Cognito

Deployment:
- AWS ECS Fargate

Every tenant-owned resource must be scoped to an authenticated tenant context. Tenant identity is resolved and authorized by the backend, never trusted from client input.