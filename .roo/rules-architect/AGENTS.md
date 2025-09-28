# Project Architecture Rules (Non-Obvious Only)

- Providers MUST be stateless - hidden caching layer assumes this
- Webview and extension communicate through specific IPC channel patterns only
- Database migrations cannot be rolled back - forward-only by design
- React hooks required because external state libraries break webview isolation
- Monorepo packages have intentional circular dependency on types package
- Hybrid classification system requires both rule-based and LLM validation
- All PDF processing must go through the pipeline in ingest/pipeline.py