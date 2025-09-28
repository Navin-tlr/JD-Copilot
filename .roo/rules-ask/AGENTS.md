# Project Documentation Rules (Non-Obvious Only)

- "src/" contains VSCode extension code, not standard web app source
- Provider examples in app/llm_role_type_classifier.py are canonical reference
- UI runs in VSCode webview with restrictions (no localStorage, limited APIs)
- Package.json scripts must be run from project root directory
- Locales in root are for extension, webview-ui/src/i18n for UI (separate systems)