"""
Database Schema Introspection Tool
Provides intelligent schema awareness to prevent hallucinations and enable smart routing.
"""

import sqlite3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json
from pathlib import Path


@dataclass
class ColumnInfo:
    """Information about a database column."""
    name: str
    type: str
    nullable: bool
    primary_key: bool
    default_value: Optional[str]
    description: str


@dataclass
class TableSchema:
    """Complete schema information for a table."""
    name: str
    columns: List[ColumnInfo]
    indexes: List[str]
    foreign_keys: List[Dict[str, str]]
    row_count: int
    sample_values: Dict[str, List[Any]]  # Sample values for each column
    description: str


@dataclass
class DatabaseSchema:
    """Complete database schema with metadata."""
    database_type: str  # 'sqlite' or 'vector'
    tables: List[TableSchema]
    total_rows: int
    specializations: List[str]
    companies: List[str]
    capabilities: List[str]  # What queries this DB can answer


class DatabaseSchemaIntrospector:
    """Introspects database schema to provide accurate metadata to agents."""
    
    def __init__(self, db_path: str = "data/placement_data.db"):
        self.db_path = db_path
        self._cached_schema: Optional[DatabaseSchema] = None
        
    def get_schema(self, force_refresh: bool = False) -> DatabaseSchema:
        """Get complete database schema with caching."""
        if self._cached_schema and not force_refresh:
            return self._cached_schema
        
        schema = self._introspect_database()
        self._cached_schema = schema
        return schema
    
    def _introspect_database(self) -> DatabaseSchema:
        """Perform complete database introspection."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            table_names = [row[0] for row in cursor.fetchall()]
            
            tables = []
            total_rows = 0
            
            for table_name in table_names:
                table_schema = self._introspect_table(cursor, table_name)
                tables.append(table_schema)
                total_rows += table_schema.row_count
            
            # Get specializations
            cursor.execute("SELECT DISTINCT name FROM specializations ORDER BY name")
            specializations = [row[0] for row in cursor.fetchall()]
            
            # Get companies
            cursor.execute("SELECT DISTINCT company_name FROM companies ORDER BY company_name")
            companies = [row[0] for row in cursor.fetchall()]
            
            # Determine capabilities
            capabilities = self._determine_capabilities(tables, specializations, companies)
            
            return DatabaseSchema(
                database_type='sqlite',
                tables=tables,
                total_rows=total_rows,
                specializations=specializations,
                companies=companies,
                capabilities=capabilities
            )
    
    def _introspect_table(self, cursor: sqlite3.Cursor, table_name: str) -> TableSchema:
        """Introspect a single table."""
        # Get column information
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_raw = cursor.fetchall()
        
        columns = []
        for col in columns_raw:
            col_info = ColumnInfo(
                name=col[1],
                type=col[2],
                nullable=not bool(col[3]),
                primary_key=bool(col[5]),
                default_value=col[4],
                description=self._get_column_description(table_name, col[1])
            )
            columns.append(col_info)
        
        # Get indexes
        cursor.execute(f"PRAGMA index_list({table_name})")
        indexes = [row[1] for row in cursor.fetchall()]
        
        # Get foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        foreign_keys = []
        for fk in cursor.fetchall():
            foreign_keys.append({
                'column': fk[3],
                'references_table': fk[2],
                'references_column': fk[4]
            })
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        # Get sample values for key columns
        sample_values = self._get_sample_values(cursor, table_name, columns)
        
        return TableSchema(
            name=table_name,
            columns=columns,
            indexes=indexes,
            foreign_keys=foreign_keys,
            row_count=row_count,
            sample_values=sample_values,
            description=self._get_table_description(table_name)
        )
    
    def _get_sample_values(
        self, 
        cursor: sqlite3.Cursor, 
        table_name: str, 
        columns: List[ColumnInfo]
    ) -> Dict[str, List[Any]]:
        """Get sample values for key columns."""
        sample_values = {}
        
        # Focus on key columns
        key_columns = [
            col.name for col in columns 
            if col.name in ['company_name', 'specialization', 'title', 'skill_name', 'company_type', 'industry']
        ]
        
        for col_name in key_columns:
            try:
                cursor.execute(f"SELECT DISTINCT {col_name} FROM {table_name} LIMIT 10")
                values = [row[0] for row in cursor.fetchall() if row[0] is not None]
                if values:
                    sample_values[col_name] = values
            except Exception:
                continue
        
        return sample_values
    
    def _get_table_description(self, table_name: str) -> str:
        """Get human-readable table description."""
        descriptions = {
            'companies': 'Stores company information including name, type, industry, and location',
            'roles': 'Stores job roles with titles, specializations, and descriptions',
            'offers': 'Stores salary and hiring information for roles',
            'skills': 'Stores required skills for each role',
            'requirements': 'Stores educational and other requirements for roles',
            'specializations': 'Stores MBA specialization domains (Marketing, Finance, HR, etc.)'
        }
        return descriptions.get(table_name, f'Table: {table_name}')
    
    def _get_column_description(self, table_name: str, column_name: str) -> str:
        """Get human-readable column description."""
        descriptions = {
            'companies': {
                'company_name': 'Official name of the company',
                'company_type': 'Type: B2B, B2C, Government, etc.',
                'industry': 'Industry sector (Technology, Finance, Consulting, etc.)',
                'location': 'Primary location or headquarters'
            },
            'roles': {
                'title': 'Job title (e.g., Marketing Manager, Financial Analyst)',
                'specialization': 'MBA specialization: Marketing, Finance, HR, Operations, etc.',
                'location': 'Job location',
                'role_types': 'JSON array of role type tags',
                'source_chunk_id': 'Link to original JD chunk in vector DB'
            },
            'offers': {
                'salary_min_lpa': 'Minimum salary in LPA (Lakhs Per Annum)',
                'salary_max_lpa': 'Maximum salary in LPA',
                'expected_hires': 'Number of positions available'
            },
            'skills': {
                'skill_name': 'Name of the skill (e.g., Python, Excel, SQL)',
                'skill_type': 'Type: technical, soft, domain-specific',
                'skill_priority': 'Priority level (1=required, 2=preferred, 3=nice-to-have)'
            }
        }
        
        if table_name in descriptions and column_name in descriptions[table_name]:
            return descriptions[table_name][column_name]
        return column_name.replace('_', ' ').title()
    
    def _determine_capabilities(
        self, 
        tables: List[TableSchema], 
        specializations: List[str], 
        companies: List[str]
    ) -> List[str]:
        """Determine what queries this database can answer."""
        capabilities = []
        
        table_names = [t.name for t in tables]
        
        # Count queries
        if 'companies' in table_names and 'roles' in table_names:
            capabilities.append('count_companies_by_specialization')
            capabilities.append('list_companies_by_specialization')
        
        # Company details
        if 'companies' in table_names:
            capabilities.append('get_company_details')
            capabilities.append('list_all_companies')
            capabilities.append('filter_by_company_type')
            capabilities.append('filter_by_industry')
        
        # Role queries
        if 'roles' in table_names:
            capabilities.append('get_role_titles')
            capabilities.append('filter_roles_by_specialization')
            capabilities.append('search_role_titles')
        
        # Salary queries
        if 'offers' in table_names:
            capabilities.append('get_salary_range')
            capabilities.append('compare_salaries')
            capabilities.append('filter_by_salary')
        
        # Skills queries
        if 'skills' in table_names:
            capabilities.append('get_required_skills')
            capabilities.append('list_skills_by_role')
            capabilities.append('find_roles_by_skill')
        
        # Specialization support
        if specializations:
            capabilities.append('filter_by_specialization')
            capabilities.append('count_by_specialization')
        
        return capabilities
    
    def get_schema_for_llm(self) -> str:
        """Get schema in LLM-friendly format."""
        schema = self.get_schema()
        
        output = ["# SQL Database Schema\n"]
        output.append(f"**Database Type:** {schema.database_type}")
        output.append(f"**Total Records:** {schema.total_rows:,}")
        output.append(f"**Companies:** {len(schema.companies)}")
        output.append(f"**Specializations:** {len(schema.specializations)}\n")
        
        # Specializations
        output.append("## Available Specializations")
        for spec in schema.specializations:
            output.append(f"- {spec}")
        output.append("")
        
        # Tables
        output.append("## Database Tables\n")
        for table in schema.tables:
            output.append(f"### {table.name} ({table.row_count:,} rows)")
            output.append(f"*{table.description}*\n")
            
            output.append("**Columns:**")
            for col in table.columns:
                pk = " [PRIMARY KEY]" if col.primary_key else ""
                nullable = " [NULL]" if col.nullable else " [NOT NULL]"
                output.append(f"- `{col.name}` {col.type}{pk}{nullable}")
                output.append(f"  - {col.description}")
            
            # Sample values
            if table.sample_values:
                output.append("\n**Sample Values:**")
                for col_name, values in table.sample_values.items():
                    values_str = ", ".join(str(v) for v in values[:5])
                    output.append(f"- {col_name}: {values_str}")
            
            # Foreign keys
            if table.foreign_keys:
                output.append("\n**Foreign Keys:**")
                for fk in table.foreign_keys:
                    output.append(f"- {fk['column']} → {fk['references_table']}.{fk['references_column']}")
            
            output.append("")
        
        # Capabilities
        output.append("## Query Capabilities")
        output.append("This database can answer:")
        for cap in schema.capabilities:
            output.append(f"- {cap.replace('_', ' ').title()}")
        
        return "\n".join(output)
    
    def can_answer_query(self, query_type: str, filters: Dict[str, Any]) -> bool:
        """Check if database can answer a specific query."""
        schema = self.get_schema()
        
        # Check specialization filter
        if 'specialization' in filters:
            spec = filters['specialization']
            if spec not in schema.specializations:
                return False
        
        # Check company filter
        if 'company' in filters:
            company = filters['company']
            # Normalize for comparison
            companies_lower = [c.lower() for c in schema.companies]
            if company.lower() not in companies_lower:
                return False
        
        # Map query types to required capabilities
        query_capability_map = {
            'count_query': ['count_companies_by_specialization', 'count_by_specialization'],
            'list_query': ['list_companies_by_specialization', 'list_all_companies'],
            'company_details': ['get_company_details'],
            'role_query': ['get_role_titles', 'filter_roles_by_specialization'],
            'salary_query': ['get_salary_range', 'compare_salaries'],
            'skills_query': ['get_required_skills', 'list_skills_by_role'],
        }
        
        # Check if any required capability exists for this query type
        required_capabilities = query_capability_map.get(query_type, [])
        if required_capabilities:
            has_capability = any(cap in schema.capabilities for cap in required_capabilities)
            if not has_capability:
                return False
        
        return True
    
    def get_valid_specializations(self) -> List[str]:
        """Get list of valid specializations."""
        schema = self.get_schema()
        return schema.specializations
    
    def get_valid_companies(self) -> List[str]:
        """Get list of valid companies."""
        schema = self.get_schema()
        return schema.companies
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        schema = self.get_schema()
        
        stats = {
            'total_companies': len(schema.companies),
            'total_specializations': len(schema.specializations),
            'total_records': schema.total_rows,
            'tables': {}
        }
        
        for table in schema.tables:
            stats['tables'][table.name] = {
                'rows': table.row_count,
                'columns': len(table.columns)
            }
        
        return stats


# Singleton instance
_introspector = None

def get_database_introspector(db_path: str = "data/placement_data.db") -> DatabaseSchemaIntrospector:
    """Get singleton introspector instance."""
    global _introspector
    if _introspector is None:
        _introspector = DatabaseSchemaIntrospector(db_path)
    return _introspector


# Convenience functions
def get_sql_schema_for_llm() -> str:
    """Get SQL schema in LLM-friendly format."""
    introspector = get_database_introspector()
    return introspector.get_schema_for_llm()


def validate_query_against_schema(
    query_type: str, 
    specialization: Optional[str] = None,
    company: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate if a query can be answered by the database.
    
    Returns:
        {
            'valid': bool,
            'reason': str,
            'suggestions': List[str]
        }
    """
    introspector = get_database_introspector()
    schema = introspector.get_schema()
    
    filters = {}
    if specialization:
        filters['specialization'] = specialization
    if company:
        filters['company'] = company
    
    # Check if query can be answered
    if introspector.can_answer_query(query_type, filters):
        return {
            'valid': True,
            'reason': 'Query can be answered with available data',
            'suggestions': []
        }
    
    # Determine why it failed
    reason = None
    suggestions = []
    
    if specialization and specialization not in schema.specializations:
        reason = f"Specialization '{specialization}' not found in database"
        suggestions = [f"Available specializations: {', '.join(schema.specializations)}"]
    
    if company:
        companies_lower = {c.lower(): c for c in schema.companies}
        if company.lower() not in companies_lower:
            reason = f"Company '{company}' not found in database"
            # Find similar companies
            similar = [c for c in schema.companies if company.lower() in c.lower()][:5]
            if similar:
                suggestions.append(f"Similar companies: {', '.join(similar)}")
            else:
                suggestions.append(f"Total companies available: {len(schema.companies)}")
    
    if not reason:
        reason = f"Query type '{query_type}' not supported for given filters"
    
    return {
        'valid': False,
        'reason': reason,
        'suggestions': suggestions
    }
