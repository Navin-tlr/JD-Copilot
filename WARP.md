# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
pip install langextract  # For company extraction
```

### Configuration
```bash
# Copy environment template
cp env.example .env

# Edit .env to configure:
# - OPENROUTER_API_KEY (recommended for LLM)
# - LLAMAPARSE_API_KEY (for PDF parsing)
# - PINECONE_API_KEY and PINECONE_INDEX_NAME (for vector storage)
```

### Data Ingestion
```bash
# Place JD PDFs or .txt files in data/jds/ directory

# Ingest documents (one-liner)
bash run.sh

# Manual ingestion
python -m ingest.pipeline --pdf_dir data/jds
```

### Backend Development
```bash
# Start API server (development)
uvicorn app.main:app --reload --port 8000

# Run backend directly
python -m app.main

# Run single test
python -m pytest tests/test_specific.py

# Run all tests
python -m pytest tests/
pytest -q  # Quiet mode
```

### Frontend Development
```bash
# Multiple React UIs are available - choose one:

# Primary UI: React Style (Full-featured chat interface)
cd "React Style" && npm install && npm run dev

# Alternative UIs:
cd "CHAT UI" && npm install && npm run dev
cd "Apple Inspired AI Chat UI 2" && npm install && npm run dev

# Build for production (from within UI directory)
npm run build

# Each UI runs on http://localhost:3000 (or next available port)
```

### Docker Deployment
```bash
# Build image
docker build -t jd-copilot .

# Run container
docker run -p 8000:8000 -e OPENROUTER_API_KEY=your_key jd-copilot
```

## Architecture Overview

### System Architecture
JD-Copilot is a multi-component placement cell assistant that processes natural language queries about job descriptions and placement data using a hybrid approach:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React UI      │◄──►│  FastAPI        │◄──►│  Data Layer     │
│   (Frontend)    │    │  (Backend)      │    │  (SQLite +      │
│                 │    │                 │    │   Pinecone)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Query Processing Pipeline
1. **User Input**: Natural language questions about placements/companies
2. **Query Routing**: Intelligent classification into STRUCTURED, UNSTRUCTURED, or HYBRID
3. **Data Processing**: 
   - STRUCTURED: SQL generation via LlamaIndex NLSQLTableQueryEngine
   - UNSTRUCTURED: Vector search through Pinecone/RAG system
   - HYBRID: Combination of both approaches
4. **LLM Synthesis**: OpenRouter API integration for response generation
5. **Response Formatting**: MBA-context aware answers with citations

### Key Components

#### Backend (`app/`)
- **`main.py`**: FastAPI application with CORS, multiple chat endpoints
- **`agent.py`**: Advanced query routing system with OpenRouterLLM wrapper
- **`rag.py`**: Vector search and embedding logic (Pinecone + local fallback)
- **`database.py`**: SQLite database operations for structured data
- **`config.py`**: Settings management with environment variables

#### Data Ingestion (`ingest/`)
- **`pipeline.py`**: Document processing with LlamaParse (primary) + fallback parsers
- **`structured_extractor.py`**: Extracts structured fields from job descriptions
- **`company_extractor.py`**: Heuristic company name extraction
- **`chunking.py`**: Text chunking strategies for vector storage

#### Database Schema
- **companies**: Basic company information (name, industry, location, year)
- **roles**: Job positions (title, specialization, company_id)
- **offers**: Salary and hiring data (salary ranges, expected hires)
- **skills**: Required skills for roles
- **requirements**: Educational/experience requirements
- **specializations**: MBA specializations reference

### Frontend Architecture
This repository includes **three separate React frontends**:

1. **"React Style" Directory**
   - Full-featured chat interface with animated mascot
   - Particle vortex background and smooth animations
   - Complete integration with Python backend
   - Primary recommended UI for development

2. **"CHAT UI" Directory**
   - Apple-inspired minimalist design
   - Clean, focused chat experience
   - Alternative UI option

3. **"Apple Inspired AI Chat UI 2" Directory**
   - Another variant of Apple-inspired design
   - Secondary UI implementation

All frontends are **independent React applications** that connect to the same Python FastAPI backend on port 8000.

### Technology Stack
- **Backend**: FastAPI, Uvicorn, SQLAlchemy, Pydantic
- **Frontends**: React 18, TypeScript, Tailwind CSS, Vite (3 separate UIs)
- **AI/ML**: LlamaIndex (Text-to-SQL), OpenRouter API, Sentence-Transformers
- **Databases**: SQLite (structured), Pinecone (vectors)
- **Document Processing**: LlamaParse, LangExtract

## Coding Guidelines

### Python Code Style
```python
# Always use future annotations
from __future__ import annotations

# Type hints required
from typing import Any, Dict, Optional, List

# Relative imports for app modules
from .config import get_settings
from .database import PlacementDatabase

# FastAPI endpoints with Pydantic models
class QueryRequest(BaseModel):
    question: str
    session_id: str = "default"

@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    # Implementation
```

### React/TypeScript Style
```typescript
// Functional components with hooks
import React, { useState, useEffect } from 'react';

// TypeScript interfaces for props
interface ChatMessageProps {
  message: string;
  isUser: boolean;
}

// Tailwind CSS with dark mode support
<div className="bg-white dark:bg-gray-800 p-4">
```

### Error Handling Patterns
- **Python**: Use FastAPI's `HTTPException` for API errors
- **React**: Implement error boundaries and graceful fallbacks
- **Database**: Handle connection failures with informative messages
- **LLM API**: Timeout handling and fallback responses

### Database Interaction Patterns
- Use `PlacementDatabase` class for structured queries
- Leverage LlamaIndex `NLSQLTableQueryEngine` for natural language to SQL
- Implement specialized logic for MBA domain queries (Marketing, Finance, HR, Operations, etc.)
- Handle specialization vs. industry column confusion with correction guardrails

### LLM Integration Best Practices
- Use OpenRouter API for production LLM calls with proper error handling
- Implement query type classification (structured vs unstructured)
- Apply schema-aware prompts to prevent hallucination
- Include context from both structured database and vector search results

### Vector Search Implementation
- Primary: Pinecone cloud vector database
- Fallback: Local database with hashed embeddings for development
- Use sentence-transformers for local embeddings
- Implement smart chunking strategies for job description documents

## Key Architectural Patterns

### Query Routing Intelligence
The system automatically classifies queries using LLM-based routing:
- **STRUCTURED**: Direct database queries (counts, lists, specific data)
- **UNSTRUCTURED**: Document-based queries (descriptions, qualitative info)  
- **HYBRID**: Combines both structured facts and document context

### MBA Domain Mapping
Special handling for MBA-specific terminology:
- Map student language (Marketing, Finance, HR) to database schema (roles.specialization)
- Distinguish between company industry vs. job specializations
- Implement correction logic for common query misinterpretations

### Multi-Modal Data Processing  
- **Document Ingestion**: LlamaParse for PDFs, structured extraction via LangExtract
- **Metadata Normalization**: Consistent company names and field formats
- **Hybrid Storage**: Structured data in SQLite, embeddings in Pinecone
- **Fallback Systems**: Local alternatives when cloud services unavailable
