# Structured DB Routing Fix

## Problem Analysis

The system is using **Pinecone (vector DB)** for count queries instead of the **structured SQLite database**, leading to:

1. **Inaccurate counts**: Vector search returns 6 companies when there are actually 14 finance companies in structured DB
2. **Inefficiency**: Vector embeddings + semantic search for simple counting is overkill
3. **Unreliability**: Depends on embedding quality and retrieval parameters instead of exact SQL

## Root Cause

Looking at the pipeline flow:

```
Query: "how many companies came for #finance"
   ↓
Stage 0: Intent Classification → "count_query" ✓
   ↓
Stage 1: Route Decision → Pipeline: retrieval → quality → synthesis ✓
   ↓
Stage 3: Retrieval → ALWAYS uses Pinecone vector search ✗ (BUG)
   ↓
Stage 5: Synthesis → Counts unique companies from vector results
```

**The bug**: The orchestrator's `_execute_retrieval()` method **always** calls `retrieve_snippets()` which uses Pinecone, even for `count_query` intents that should use SQL.

## Solution Architecture

### 1. **SQL-First Routing for Count Queries**

Modify `/app/agents/orchestrator.py` to check if SQL can handle the query before using vector search:

```python
async def _execute_retrieval(self, context, intent, plan, strategy):
    # NEW: Try SQL first for count queries
    if intent.primary_intent == 'count_query':
        sql_result = await self._try_sql_count(context, intent)
        if sql_result:
            return {'sql': sql_result}  # Use SQL result
    
    # Fallback to vector search
    return await self._execute_vector_retrieval(context, intent, plan)
```

### 2. **Hybrid SQL + Vector Approach**

For count queries with specialization:

```python
async def _try_sql_count(self, context, intent):
    from app.sql_tool import execute_canonical_query
    
    specialization = intent.specialization
    resolved_query = context.get('resolved_query', '')
    
    # Try canonical SQL queries first
    result = execute_canonical_query(resolved_query)
    
    if result and 'count' in str(result).lower():
        return {
            'source': 'sql',
            'count': result,
            'companies': self._get_companies_list(specialization),
            'accurate': True
        }
    
    return None
```

### 3. **Enhanced SQL Tool Integration**

Update `sql_tool.py` to export a simpler interface:

```python
def get_count_for_specialization(specialization: str) -> dict:
    """Direct count query for specialization."""
    query = f"""
        SELECT 
            COUNT(DISTINCT c.company_name) as count,
            GROUP_CONCAT(DISTINCT c.company_name) as companies
        FROM roles r
        JOIN companies c ON r.company_id = c.id
        WHERE LOWER(r.specialization) = '{specialization.lower()}'
    """
    # Execute and return structured result
```

## Implementation Plan

### Phase 1: Quick Fix (30 minutes)
1. Add SQL routing logic to orchestrator
2. Update synthesis to handle both SQL and vector results
3. Add logging to show which data source was used

### Phase 2: Robust Solution (2 hours)
1. Create unified data layer abstraction
2. Implement query planner that chooses optimal source
3. Add caching for frequent SQL queries
4. Fallback chain: SQL → Vector → Hybrid

### Phase 3: Flexible Architecture (4 hours)
1. Intent-based routing table
2. Query complexity analyzer
3. Multi-source aggregation
4. Real-time accuracy monitoring

## Benefits of Fix

| Aspect | Before (Vector Only) | After (SQL-First) |
|--------|---------------------|-------------------|
| **Accuracy** | 6/14 companies (43%) | 14/14 companies (100%) |
| **Speed** | ~500ms (embedding + search) | ~5ms (SQL query) |
| **Reliability** | Depends on embeddings | Guaranteed accurate |
| **Token Cost** | Uses API for embeddings | Zero API cost |
| **Flexibility** | Good for unstructured | Best for structured |

## Recommended Routing Logic

```python
QUERY_ROUTING_MAP = {
    'count_query': {
        'primary': 'sql',
        'fallback': 'vector',
        'condition': 'has_specialization'
    },
    'list_query': {
        'primary': 'sql',
        'fallback': 'vector',
        'condition': 'simple_filter'
    },
    'comparison_query': {
        'primary': 'sql',
        'fallback': 'hybrid',
        'condition': 'structured_data_available'
    },
    'interview_prep': {
        'primary': 'vector',
        'fallback': 'none',
        'condition': 'always'
    }
}
```

## Example Fix for Your Query

**Query**: "how many companies came for #finance"

**Current Flow** ❌:
```
Pinecone → 222 candidates → Filter to 50 → Extract unique companies → Count = 6
```

**Fixed Flow** ✅:
```
SQL → SELECT COUNT(DISTINCT c.company_name) FROM roles r ... → Count = 14
If SQL fails → Fallback to Pinecone
```

## Next Steps

1. **Immediate**: I can implement the quick fix now (modify orchestrator)
2. **Short-term**: Add comprehensive SQL routing
3. **Long-term**: Build query planner with cost-based optimization

Would you like me to implement the quick fix right now?
