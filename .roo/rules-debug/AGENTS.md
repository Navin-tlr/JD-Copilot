# Project Debug Rules (Non-Obvious Only)

- Check 'company_norm' field first when debugging Pinecone metadata issues
- API errors related to ingestion will log to "Ingestion Pipeline" channel
- Set NODE_ENV=production to replicate cloud issues locally
- Database migrations cannot be rolled back - forward-only design
- Webview dev tools accessed via Command Palette > "Developer: Open Webview Developer Tools"