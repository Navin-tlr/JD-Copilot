-- Migration to add dynamic hierarchy fields for specializations, level1_roles, level2_roles
-- Adapted for SQLite (uses TEXT for JSON storage; parse as JSON in app code)
-- Run this via sqlite3 data/placement_data.db < this_file.sql

-- Assume table is 'roles' or 'job_ingestion'; adjust if needed based on schema
-- From app/database.py, likely 'roles' table has company, title, etc.

-- Add columns if not exist (SQLite doesn't have IF NOT EXISTS for ALTER, so check manually or use app code)
ALTER TABLE roles ADD COLUMN specializations TEXT DEFAULT '[]';

ALTER TABLE roles ADD COLUMN level1_roles TEXT DEFAULT '[]';

ALTER TABLE roles ADD COLUMN level2_roles TEXT DEFAULT '[]';

-- Example data format (stored as JSON strings):
-- specializations: '[{"specialization":"Finance","confidence":0.92,"source":"llm","evidence":"forecasting models"}]'
-- level1_roles: '[{"level1":"FP&A","specialization":["Finance"],"confidence":0.85,"source":"llm","rationale":"JD mentions budgeting"}]'
-- level2_roles: '[{"level2":"Budget Analyst","level1":"FP&A","confidence":0.82,"source":"llm","rationale":"From responsibilities"}]'

-- To verify after migration:
-- SELECT title, specializations FROM roles LIMIT 5;
-- Note: In app code, use json.loads() to parse TEXT fields when querying.

-- Rollback (if needed):
-- PRAGMA writable_schema = ON;
-- UPDATE sqlite_master SET sql = replace(sql, ' specializations TEXT DEFAULT ''[]'';', '') WHERE type = 'table' AND name = 'roles';
-- PRAGMA writable_schema = OFF;
-- But better to drop columns manually if rollback.