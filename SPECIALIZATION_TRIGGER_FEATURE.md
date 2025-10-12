# Specialization Trigger Feature

## Overview
The chat interface now supports a **specialization trigger** feature that allows students to easily query by specialization without typing the exact specialization name.

## ✅ Status: READY TO USE
The database has been populated with:
- **8 companies**
- **11 roles**
- **Current specializations**: Marketing (7 roles), Finance (1 role), HR (1 role), Lean Operation and Systems (2 roles)

### Test Results
```
✅ Marketing: 4 companies (Honasa Consumer Limited, Madison PR, Tap Academy, Target)
✅ Finance: 1 company (Mill Story)
✅ HR: 1 company (Accorian)
⚠️ Operations: 0 companies (but "Lean Operation and Systems" exists - may need normalization)
⚠️ Analytics: 0 companies (no data yet)
⚠️ IT: 0 companies (no data yet)
⚠️ Strategy: 0 companies (no data yet)
```

## How to Use

1. **Trigger the Dropdown**: Type `#` anywhere in your query
2. **Select Specialization**: A dropdown will appear with available specializations:
   - 📢 Marketing
   - 💰 Finance
   - 👥 HR
   - ⚙️ Operations
   - 📊 Analytics
   - 💻 IT
   - 🎯 Strategy

3. **Complete Your Query**: The selected specialization will be inserted into your query

## Example Queries

- Type: `How many companies came for #` → Select "Marketing" → Result: "How many companies came for marketing"
- Type: `List companies for #` → Select "Finance" → Result: "List companies for finance"
- Type: `Which companies offer # roles?` → Select "Analytics" → Result: "Which companies offer analytics roles?"

## Backend Support

The backend SQL tool automatically recognizes these specializations and executes optimized SQL queries:

```sql
SELECT COUNT(DISTINCT c.company_name) 
FROM roles r 
JOIN companies c ON r.company_id = c.id 
WHERE LOWER(r.specialization) = 'marketing';
```

## Supported Query Types

1. **Count Queries**: "How many companies came for [specialization]?"
2. **List Queries**: "List companies for [specialization]"
3. **Generic Queries**: "Companies offering [specialization] roles"

## Technical Implementation

### Frontend (spark-home-2)
- **Component**: `SpecializationDropdown.tsx` - Dropdown UI component
- **Updated**: `ChatInput.tsx` - Detects `#` and triggers dropdown
- **Styling**: Matches the theme variant (default/rag/benchmark)

### Backend (app)
- **Updated**: `sql_tool.py` - Added canonical queries for all specializations
- **Coverage**: Analytics, IT, and Strategy added alongside existing Marketing, Finance, HR, Operations

## Future Enhancements

- [ ] Add more specializations dynamically from database
- [ ] Support multiple specialization selection
- [ ] Add keyboard navigation (arrow keys) in dropdown
- [ ] Add fuzzy search within dropdown
- [ ] Show company count preview for each specialization
