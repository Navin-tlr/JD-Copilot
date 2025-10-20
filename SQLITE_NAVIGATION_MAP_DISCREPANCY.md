# SQLite vs Navigation Map Discrepancy Report

**Date**: October 17, 2025  
**Issue**: Companies with Operations specialization mismatch between data sources

## Summary

- **Navigation Map**: 21 companies with "Operations" specialization
- **SQLite Database**: 12 companies with "LEAN OPERATION AND SYSTEMS" specialization
- **Net Difference**: 13 companies missing in SQLite, 4 companies missing in Navigation Map

## Root Cause

The Navigation Map and SQLite database are populated from **different sources**:

1. **Navigation Map** (`data/navigation_map.json`)
   - Source: Pinecone vector DB + ingestion pipeline
   - Populated during PDF ingestion via `ingest/pipeline.py`
   - Uses **normalized specialization names** (e.g., "Operations")
   - Contains all ingested job descriptions

2. **SQLite Database** (`data/placement_data.db`)
   - Source: Manual structured JSON data
   - Populated from `data/structured_json/*.json` files
   - Uses **raw specialization names** from source data (e.g., "LEAN OPERATION AND SYSTEMS")
   - Contains only manually curated/structured extractions

## Companies Missing in SQLite (13)

These companies exist in Navigation Map but NOT in SQLite:

1. Abb
2. Alstom
3. Anz 04
4. Associate Project Manager
5. Commonwealth Bank Of Australia
6. Companystore
7. Deloitte
8. Disa India Limited
9. Egov Foundation
10. Ericsson
11. Executive Management Trainee
12. Head Field
13. Hul

**Why**: These companies were ingested via the PDF pipeline and stored in Pinecone/Navigation Map, but were never added to the manual structured JSON files that populate SQLite.

## Companies Missing in Navigation Map (4)

These companies exist in SQLite but NOT in Navigation Map:

1. EdiGlobe
2. Hello Mentor
3. KNOLSKAPE
4. Masters' Union

**Why**: These companies exist in structured JSON but may have been:
- Ingested before navigation map feature was implemented
- Manually added to SQLite without corresponding PDF ingestion
- Name normalization differences (e.g., "Masters' Union" vs "MastersUnion")

## Companies in BOTH (8 overlapping)

These companies appear in both sources:
1. Aurm
2. Chocolatex
3. Consilio
4. Grayquest
5. Sonata Software Limited
6. Tata Play Limited
7. Uniqlo
8. Wns

## Impact on Query Results

When users query "How many companies came for Operations?":

### Current Behavior
- **SQL-first routing**: Returns **0** (searches for 'operations', finds nothing)
- **Vector retrieval**: Would return **21** (from navigation map)

### Why SQL Returns 0
The SQL query looks for:
```sql
WHERE LOWER(r.specialization) = 'operations'
```

But database contains:
```sql
'LEAN OPERATION AND SYSTEMS'
```

No match → 0 results.

## Solutions

### Option 1: Update UI with Actual DB Names (IMPLEMENTED)
✅ Updated `SpecializationPopup.tsx` to show:
- "MARKETING" (instead of "Marketing")
- "HR" (instead of "Human Resources")
- "BUSINESS ANALYTICS" (instead of "Business Analytics")
- "LEAN OPERATION AND SYSTEMS" (instead of "Operations")
- "FINANCE" (instead of "Finance")

**Pros**: Queries will now match DB exactly  
**Cons**: Less user-friendly display names

### Option 2: Add Normalization Layer in SQL Queries
Map specialization tokens to DB values in orchestrator:
```python
SPEC_DB_MAPPING = {
    'operations': 'LEAN OPERATION AND SYSTEMS',
    'marketing': 'MARKETING',
    'hr': 'HR',
    'finance': 'FINANCE',
    'business-analytics': 'BUSINESS ANALYTICS'
}
```

**Pros**: User-friendly names in UI  
**Cons**: Requires updating orchestrator logic

### Option 3: Normalize SQLite Database Values
Update `data/placement_data.db` to use standardized names:
- "LEAN OPERATION AND SYSTEMS" → "Operations"
- Keep others uppercase: "MARKETING", "HR", "FINANCE", "BUSINESS ANALYTICS"

**Pros**: Consistent with Navigation Map  
**Cons**: Requires database migration

### Option 4: Sync SQLite from Navigation Map (RECOMMENDED)
Re-ingest all PDFs and populate SQLite from the same extraction:
```bash
python -m ingest.pipeline --pdf_dir data/jds --sync-db
```

**Pros**: Single source of truth, no discrepancies  
**Cons**: Requires ingestion pipeline update

## Recommended Action Plan

1. ✅ **Immediate Fix**: Update UI popup with exact DB names (completed)
2. **Short-term**: Add specialization normalization in orchestrator
3. **Long-term**: Implement unified data ingestion that populates both Pinecone and SQLite from same extraction

## Files Affected

- `spark-home-2/client/components/SpecializationPopup.tsx` - Updated with DB names
- `app/agents/orchestrator.py` - Needs normalization logic
- `data/navigation_map.json` - Contains 21 Operations companies
- `data/placement_data.db` - Contains 12 LEAN OPERATION AND SYSTEMS companies

## Queries to Verify

```sql
-- Check all distinct specializations
SELECT DISTINCT specialization FROM roles ORDER BY specialization;

-- Count companies per specialization
SELECT specialization, COUNT(DISTINCT company_id) 
FROM roles 
GROUP BY specialization 
ORDER BY specialization;
```

```python
# Check navigation map
import json
with open('data/navigation_map.json') as f:
    nav = json.load(f)
    ops = [v['display_name'] for k, v in nav.items() 
           if 'Operations' in v.get('specializations', [])]
    print(f"Operations companies: {len(ops)}")
```
