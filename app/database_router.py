"""
Intelligent Database Router
Determines which database(s) to use based on query intent and available schemas.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class DatabaseType(Enum):
    """Available database types."""
    SQL = "sql"  # Structured SQLite database
    VECTOR = "vector"  # Pinecone vector database
    BOTH = "both"  # Use both databases


class QueryCategory(Enum):
    """Categories of queries."""
    STRUCTURED_COUNT = "structured_count"  # Count queries
    STRUCTURED_LIST = "structured_list"  # List queries
    STRUCTURED_FILTER = "structured_filter"  # Filter/search queries
    STRUCTURED_AGGREGATE = "structured_aggregate"  # Aggregations (salary, etc.)
    UNSTRUCTURED_CONTENT = "unstructured_content"  # Interview prep, JD analysis
    UNSTRUCTURED_SEMANTIC = "unstructured_semantic"  # Semantic search
    HYBRID = "hybrid"  # Needs both structured and unstructured


@dataclass
class DatabaseRoutingDecision:
    """Decision on which database(s) to use."""
    primary_database: DatabaseType
    fallback_database: Optional[DatabaseType]
    query_category: QueryCategory
    confidence: float
    reasoning: str
    sql_capable: bool  # Can SQL answer this?
    vector_capable: bool  # Can vector answer this?
    prefer_sql_reason: Optional[str]  # Why prefer SQL over vector


class IntelligentDatabaseRouter:
    """
    Intelligently routes queries to appropriate database(s).
    
    Rules:
    1. Structured queries (counts, lists, filters) → SQL first
    2. Unstructured queries (interview prep, semantic) → Vector first
    3. Hybrid queries (detailed company insights) → Both
    4. Always validate against actual schema before routing
    """
    
    def __init__(self):
        # Import here to avoid circular dependency
        from app.database_schema_tool import get_database_introspector
        self.sql_introspector = get_database_introspector()
    
    def route_query(
        self,
        intent: str,
        specialization: Optional[str] = None,
        company: Optional[str] = None,
        query_text: str = ""
    ) -> DatabaseRoutingDecision:
        """
        Route query to appropriate database(s).
        
        Args:
            intent: Primary intent (count_query, list_query, interview_prep, etc.)
            specialization: MBA specialization filter
            company: Company name filter
            query_text: Original query text for context
        
        Returns:
            DatabaseRoutingDecision with routing logic
        """
        
        # Categorize the query
        category = self._categorize_query(intent, query_text)
        
        # Check SQL capability
        sql_capable = self._can_sql_answer(category, intent, specialization, company)
        
        # Check vector capability
        vector_capable = self._can_vector_answer(category, intent, company)
        
        # Make routing decision
        if category in [QueryCategory.STRUCTURED_COUNT, QueryCategory.STRUCTURED_LIST, 
                       QueryCategory.STRUCTURED_FILTER, QueryCategory.STRUCTURED_AGGREGATE]:
            # Structured queries: SQL first, vector fallback
            if sql_capable:
                return DatabaseRoutingDecision(
                    primary_database=DatabaseType.SQL,
                    fallback_database=DatabaseType.VECTOR if vector_capable else None,
                    query_category=category,
                    confidence=0.95,
                    reasoning="Structured query best answered by SQL database for accuracy",
                    sql_capable=True,
                    vector_capable=vector_capable,
                    prefer_sql_reason="SQL provides exact counts/lists from structured data"
                )
            elif vector_capable:
                return DatabaseRoutingDecision(
                    primary_database=DatabaseType.VECTOR,
                    fallback_database=None,
                    query_category=category,
                    confidence=0.6,
                    reasoning="SQL cannot answer; using vector search (may be less accurate)",
                    sql_capable=False,
                    vector_capable=True,
                    prefer_sql_reason=None
                )
        
        elif category in [QueryCategory.UNSTRUCTURED_CONTENT, QueryCategory.UNSTRUCTURED_SEMANTIC]:
            # Unstructured queries: Vector primary
            return DatabaseRoutingDecision(
                primary_database=DatabaseType.VECTOR,
                fallback_database=None,
                query_category=category,
                confidence=0.9,
                reasoning="Unstructured content query best answered by vector search",
                sql_capable=False,
                vector_capable=vector_capable,
                prefer_sql_reason=None
            )
        
        elif category == QueryCategory.HYBRID:
            # Hybrid queries: Use both
            return DatabaseRoutingDecision(
                primary_database=DatabaseType.BOTH,
                fallback_database=None,
                query_category=category,
                confidence=0.85,
                reasoning="Hybrid query requires both structured and unstructured data",
                sql_capable=sql_capable,
                vector_capable=vector_capable,
                prefer_sql_reason="SQL for structured facts, vector for detailed content"
            )
        
        # Default fallback
        return DatabaseRoutingDecision(
            primary_database=DatabaseType.VECTOR,
            fallback_database=DatabaseType.SQL if sql_capable else None,
            query_category=category,
            confidence=0.5,
            reasoning="Uncertain routing; defaulting to vector search",
            sql_capable=sql_capable,
            vector_capable=vector_capable,
            prefer_sql_reason=None
        )
    
    def _categorize_query(self, intent: str, query_text: str) -> QueryCategory:
        """Categorize query into structured/unstructured/hybrid."""
        
        # Structured categories
        if intent in ['count_query', 'specialization_count']:
            return QueryCategory.STRUCTURED_COUNT
        
        if intent in ['list_query', 'company_list', 'role_list']:
            return QueryCategory.STRUCTURED_LIST
        
        if intent in ['filter_query', 'search_query', 'skill_query']:
            return QueryCategory.STRUCTURED_FILTER
        
        if intent in ['salary_query', 'aggregate_query']:
            return QueryCategory.STRUCTURED_AGGREGATE
        
        # Unstructured categories
        if intent in ['interview_prep', 'gd_topic', 'alumni_insight', 'culture_query']:
            return QueryCategory.UNSTRUCTURED_CONTENT
        
        if intent in ['similarity_query', 'semantic_search']:
            return QueryCategory.UNSTRUCTURED_SEMANTIC
        
        # Hybrid categories
        if intent in ['company_deep_dive', 'role_details', 'comparison_query']:
            return QueryCategory.HYBRID
        
        # Keyword-based fallback
        query_lower = query_text.lower()
        
        # Count indicators
        if any(word in query_lower for word in ['how many', 'count', 'number of']):
            return QueryCategory.STRUCTURED_COUNT
        
        # List indicators
        if any(word in query_lower for word in ['list', 'show all', 'give me all']):
            return QueryCategory.STRUCTURED_LIST
        
        # Unstructured indicators
        if any(word in query_lower for word in ['interview', 'prepare', 'tips', 'advice', 'culture', 'work environment']):
            return QueryCategory.UNSTRUCTURED_CONTENT
        
        # Default to hybrid
        return QueryCategory.HYBRID
    
    def _can_sql_answer(
        self,
        category: QueryCategory,
        intent: str,
        specialization: Optional[str],
        company: Optional[str]
    ) -> bool:
        """Check if SQL database can answer this query."""
        
        # SQL cannot answer unstructured queries
        if category in [QueryCategory.UNSTRUCTURED_CONTENT, QueryCategory.UNSTRUCTURED_SEMANTIC]:
            return False
        
        # Get schema and validate
        schema = self.sql_introspector.get_schema()
        
        # Check specialization filter
        if specialization and specialization not in schema.specializations:
            return False
        
        # Check company filter
        if company:
            companies_lower = [c.lower() for c in schema.companies]
            if company.lower() not in companies_lower:
                return False
        
        # Check if we have data
        if schema.total_rows == 0:
            return False
        
        # Structured queries are SQL-capable if filters valid
        if category in [QueryCategory.STRUCTURED_COUNT, QueryCategory.STRUCTURED_LIST,
                       QueryCategory.STRUCTURED_FILTER, QueryCategory.STRUCTURED_AGGREGATE]:
            return True
        
        # Hybrid queries are partially SQL-capable
        if category == QueryCategory.HYBRID:
            return True
        
        return False
    
    def _can_vector_answer(
        self,
        category: QueryCategory,
        intent: str,
        company: Optional[str]
    ) -> bool:
        """Check if vector database can answer this query."""
        
        # Vector can answer most query types (less accurate for structured)
        # but excels at unstructured content
        
        if category in [QueryCategory.UNSTRUCTURED_CONTENT, QueryCategory.UNSTRUCTURED_SEMANTIC]:
            return True
        
        if category == QueryCategory.HYBRID:
            return True
        
        # Vector can attempt structured queries but less accurately
        if category in [QueryCategory.STRUCTURED_COUNT, QueryCategory.STRUCTURED_LIST]:
            return True
        
        return True  # Vector is versatile, can attempt most queries
    
    def explain_routing(self, decision: DatabaseRoutingDecision) -> str:
        """Generate human-readable explanation of routing decision."""
        
        lines = []
        lines.append(f"🧭 Database Routing Decision")
        lines.append(f"   Primary: {decision.primary_database.value.upper()}")
        if decision.fallback_database:
            lines.append(f"   Fallback: {decision.fallback_database.value.upper()}")
        lines.append(f"   Category: {decision.query_category.value.replace('_', ' ').title()}")
        lines.append(f"   Confidence: {decision.confidence:.0%}")
        lines.append(f"   Reasoning: {decision.reasoning}")
        
        if decision.prefer_sql_reason:
            lines.append(f"   ✅ SQL Preferred: {decision.prefer_sql_reason}")
        
        return "\n".join(lines)


# Singleton instance
_router = None

def get_database_router() -> IntelligentDatabaseRouter:
    """Get singleton router instance."""
    global _router
    if _router is None:
        _router = IntelligentDatabaseRouter()
    return _router


def route_query_intelligently(
    intent: str,
    specialization: Optional[str] = None,
    company: Optional[str] = None,
    query_text: str = ""
) -> DatabaseRoutingDecision:
    """
    Main routing function for external use.
    
    Example:
        decision = route_query_intelligently(
            intent='count_query',
            specialization='Finance',
            query_text='how many companies came for finance?'
        )
        
        if decision.primary_database == DatabaseType.SQL:
            # Use SQL database
            result = execute_sql_query(...)
    """
    router = get_database_router()
    return router.route_query(intent, specialization, company, query_text)
