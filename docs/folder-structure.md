# Folder structure of the whole application

enterprise-knowledge-assistant/
│
├── apps/
│   └── web/
│       ├── app/
│       │   ├── login/
│       │   ├── register/
│       │   ├── dashboard/
│       │   ├── documents/
│       │   ├── chat/
│       │   └── settings/
│       ├── components/
│       ├── hooks/
│       ├── lib/
│       └── package.json
│
├── services/
│   ├── api/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   │   └── v1/
│   │   │   │       ├── auth.py
│   │   │   │       ├── tenants.py
│   │   │   │       ├── documents.py
│   │   │   │       ├── conversations.py
│   │   │   │       └── chat.py
│   │   │   │
│   │   │   ├── core/
│   │   │   │   ├── config.py
│   │   │   │   ├── security.py
│   │   │   │   └── exceptions.py
│   │   │   │
│   │   │   ├── models/
│   │   │   ├── schemas/
│   │   │   ├── repositories/
│   │   │   ├── services/
│   │   │   │   ├── tenant_service.py
│   │   │   │   ├── document_service.py
│   │   │   │   ├── rag_service.py
│   │   │   │   └── conversation_service.py
│   │   │   │
│   │   │   ├── integrations/
│   │   │   │   └── aws/
│   │   │   │       ├── s3_client.py
│   │   │   │       ├── bedrock_client.py
│   │   │   │       ├── knowledge_base.py
│   │   │   │       └── cognito.py
│   │   │   │
│   │   │   ├── middleware/
│   │   │   ├── db/
│   │   │   └── main.py
│   │   │
│   │   ├── migrations/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── ingestion-worker/
│       ├── handlers/
│       ├── services/
│       ├── integrations/
│       └── tests/
│
├── infrastructure/
│   └── cdk/
│       ├── bin/
│       ├── lib/
│       │   ├── storage-stack.ts
│       │   ├── database-stack.ts
│       │   ├── auth-stack.ts
│       │   ├── rag-stack.ts
│       │   └── application-stack.ts
│       └── package.json
│
├── docs/
│   ├── architecture.md
│   ├── database-design.md
│   ├── api-specification.md
│   └── security.md
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md