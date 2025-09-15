# Coding Agent Guidelines for JD-Copilot

## Build/Test Commands
- **React Frontend**: `cd "React Style" && npm run dev` (development), `npm run build` (build), `npm run lint` (lint)
- **Python Backend**: `python -m pytest tests/` (all tests), `python -m pytest tests/test_specific.py` (single test)
- **Start Backend**: `python -m app.main` or `uvicorn app.main:app --reload`

## Python Code Style
- Use `from __future__ import annotations` for forward references
- Type hints required: `from typing import Any, Dict, Optional, List`
- FastAPI endpoints with Pydantic models for request/response
- Snake_case for variables/functions, PascalCase for classes
- Relative imports: `from .module import function`
- Async/await for I/O operations, use `pytest-asyncio` for tests

## React/TypeScript Style  
- Functional components with hooks (`useState`, `useEffect`)
- TypeScript interfaces for props, strict typing required
- Tailwind CSS for styling with dark mode support (`dark:` prefix)
- Named exports for components, default export for main App
- CamelCase for variables/functions, PascalCase for components

## Error Handling
- Python: Use FastAPI's `HTTPException` for API errors
- React: Graceful fallbacks, error boundaries for component errors
- Always handle async operations with try/catch or error states