"""
Planning Agent - Creates execution plan with intelligent database routing.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from .intent_classifier import QueryIntent
from app.navigation_map import navigation_map
from app.database_router import route_query_intelligently, DatabaseType, DatabaseRoutingDecision
from app.database_schema_tool import get_database_introspector, validate_query_against_schema
import re


@dataclass
class DataSourceStatus:
    """Status of a data source for a company."""
    source_type: str
    company: str
    available: bool
    quality: str  # 'high', 'medium', 'low', 'unknown'
    estimated_count: int


@dataclass
class ExecutionPlan:
    """Comprehensive execution plan with intelligent database routing."""
    primary_strategy: str
    fallback_strategies: List[str]
    companies_to_query: List[str]
    sources_per_company: Dict[str, List[str]]
    data_availability: Dict[str, DataSourceStatus]
    expected_gaps: List[str]
    synthesis_adaptations: List[str]
    complexity_score: float
    
    # NEW: Intelligent database routing
    database_routing: Optional[DatabaseRoutingDecision] = None
    use_sql_database: bool = False
    use_vector_database: bool = False
    sql_query_validated: bool = False
    schema_validation: Optional[Dict] = None


class PlanningAgent:
    """Plans execution strategy with intelligent database routing."""
    
    def __init__(self):
        # Cache of known data gaps (updated from ingestion metadata)
        self.known_sparse_sources = {
            'interview': ['acuity', 'alstom', 'madison'],
            'gd_topic': ['millstory', 'wns'],
            'alumni': ['acuity', 'madison']
        }
        
        # Initialize database introspector for schema awareness
        self.db_introspector = get_database_introspector()
    
    async def create_plan(
        self, 
        intent: QueryIntent,
        context: Optional[Dict] = None
    ) -> ExecutionPlan:
        """Create comprehensive execution plan with intelligent database routing."""
        
        print(f"\n📋 Planning Agent: Creating execution plan...")
        
        # STEP 1: Intelligent Database Routing
        routing_decision = route_query_intelligently(
            intent=intent.primary_intent,
            specialization=intent.specialization if intent.specialization_explicit else None,
            company=intent.company,
            query_text=context.get('original_query', '') if context else ''
        )
        
        print(f"   🧭 Database Routing:")
        print(f"      Primary: {routing_decision.primary_database.value.upper()}")
        if routing_decision.fallback_database:
            print(f"      Fallback: {routing_decision.fallback_database.value.upper()}")
        print(f"      Confidence: {routing_decision.confidence:.0%}")
        print(f"      Reason: {routing_decision.reasoning}")
        
        # STEP 2: Validate against database schema (prevent hallucinations)
        schema_validation = None
        if routing_decision.sql_capable:
            schema_validation = validate_query_against_schema(
                query_type=intent.primary_intent,
                specialization=intent.specialization,
                company=intent.company
            )
            
            if not schema_validation['valid']:
                print(f"   ⚠️  SQL Validation Failed: {schema_validation['reason']}")
                if schema_validation['suggestions']:
                    for suggestion in schema_validation['suggestions']:
                        print(f"      💡 {suggestion}")
        
        # Check navigation map validation FIRST
        if intent.data_availability == 'not_found' and intent.specialization_explicit:
            print(f"   ⚠️  Navigation Map: Company+Specialization NOT FOUND")
            print(f"   Switching to Suggestion Response Mode")
            
            # Create suggestion-only plan (skip retrieval)
            return ExecutionPlan(
                primary_strategy='suggestion_response',
                fallback_strategies=['general_advice'],
                companies_to_query=[],
                sources_per_company={},
                data_availability={},
                expected_gaps=[f"No data for {intent.company} in {intent.specialization}"],
                synthesis_adaptations=['show_suggestions_instead'],
                complexity_score=0.1,
                database_routing=routing_decision,
                use_sql_database=False,
                use_vector_database=False,
                sql_query_validated=False,
                schema_validation=schema_validation
            )
        
        # Determine companies to query
        companies = self._determine_companies(intent, context)
        print(f"   Companies: {companies}")
        
        # Check data availability
        data_availability = self._check_data_availability(
            companies=companies,
            sources_needed=intent.sources_needed
        )
        
        # Identify expected gaps
        expected_gaps = self._identify_gaps(data_availability)
        if expected_gaps:
            print(f"   ⚠️  Gaps: {', '.join(expected_gaps[:2])}{'...' if len(expected_gaps) > 2 else ''}")
        
        # Determine primary strategy based on routing decision
        primary_strategy = self._determine_primary_strategy_with_routing(
            intent=intent,
            data_availability=data_availability,
            company_count=len(companies),
            routing_decision=routing_decision
        )
        print(f"   Strategy: {primary_strategy}")
        
        # Create fallbacks
        fallback_strategies = self._create_fallback_strategies(
            intent=intent,
            data_availability=data_availability,
            primary_strategy=primary_strategy
        )
        
        # Map sources per company
        sources_per_company = self._map_sources_per_company(
            companies=companies,
            data_availability=data_availability,
            intent=intent
        )
        
        # Determine synthesis adaptations
        synthesis_adaptations = self._determine_synthesis_adaptations(
            expected_gaps=expected_gaps,
            data_availability=data_availability,
            intent=intent
        )
        
        # Calculate complexity
        complexity_score = self._calculate_complexity(
            company_count=len(companies),
            source_count=len(intent.sources_needed),
            data_gaps=len(expected_gaps),
            intent=intent
        )
        
        # Determine which databases to use
        use_sql = (routing_decision.primary_database == DatabaseType.SQL or 
                   routing_decision.primary_database == DatabaseType.BOTH)
        use_vector = (routing_decision.primary_database == DatabaseType.VECTOR or 
                      routing_decision.primary_database == DatabaseType.BOTH or 
                      routing_decision.fallback_database == DatabaseType.VECTOR)

        # SQL query is validated if routing says SQL-capable and schema validation passed
        sql_validated = routing_decision.sql_capable and (
            schema_validation is None or schema_validation.get('valid', False)
        )

        # OVERRIDE: Unknown-topic count queries should be vector-first aggregation (no SQL validation)
        if intent.primary_intent == 'count_query' and (not intent.specialization_explicit) and intent.topic_or_keyword:
            print("   🔎 Detected keyword-based count → Using vector-first aggregation")
            use_sql = False
            use_vector = True
            sql_validated = False
            primary_strategy = 'hybrid_vector_sql_aggregate'
        
        plan = ExecutionPlan(
            primary_strategy=primary_strategy,
            fallback_strategies=fallback_strategies,
            companies_to_query=companies,
            sources_per_company=sources_per_company,
            data_availability=data_availability,
            expected_gaps=expected_gaps,
            synthesis_adaptations=synthesis_adaptations,
            complexity_score=complexity_score,
            database_routing=routing_decision,
            use_sql_database=use_sql,
            use_vector_database=use_vector,
            sql_query_validated=sql_validated,
            schema_validation=schema_validation
        )
        
        print(f"   Complexity: {complexity_score:.2f}")
        print(f"   Databases: {'SQL' if use_sql else ''}{'+ Vector' if use_vector else 'Vector' if not use_sql else ''}\n")
        return plan
    
    def _determine_companies(
        self, 
        intent: QueryIntent, 
        context: Optional[Dict]
    ) -> List[str]:
        """Determine which companies to query."""
        companies = []
        
        # Single company query
        if intent.company:
            companies.append(intent.company)
        
        # Multi-company comparison
        elif intent.requires_comparison and context:
            companies = self._extract_comparison_companies(context)
        
        # "Show all" type queries
        elif intent.primary_intent == 'count_query':
            companies = ['*']  # Wildcard
        
        return companies if companies else ['*']
    
    def _extract_comparison_companies(self, context: Dict) -> List[str]:
        """Extract companies from comparison query."""
        query = context.get('resolved_query', '').lower()
        
        company_pattern = r'\b(honasa|target|uniqlo|mastersunion|wns|millstory|acuity|alstom|madison)\b'
        companies = re.findall(company_pattern, query)
        
        return list(dict.fromkeys(companies))  # Remove duplicates
    
    def _check_data_availability(
        self,
        companies: List[str],
        sources_needed: List[str]
    ) -> Dict[str, DataSourceStatus]:
        """Check what data exists for each company+source combo."""
        
        availability = {}
        
        for company in companies:
            if company == '*':  # Wildcard
                continue
            
            for source in sources_needed:
                key = f"{company}:{source}"
                
                # Check if source is known to be sparse
                is_sparse = (
                    source in self.known_sparse_sources and
                    company in self.known_sparse_sources[source]
                )
                
                availability[key] = DataSourceStatus(
                    source_type=source,
                    company=company,
                    available=not is_sparse,
                    quality='low' if is_sparse else 'unknown',
                    estimated_count=0 if is_sparse else 10
                )
        
        return availability
    
    def _determine_primary_strategy_with_routing(
        self,
        intent: QueryIntent,
        data_availability: Dict[str, DataSourceStatus],
        company_count: int,
        routing_decision: DatabaseRoutingDecision
    ) -> str:
        """Determine primary execution strategy with database routing awareness."""
        
        # NEW: If this is a count query with a generic topic/keyword (no explicit specialization),
        # prefer a hybrid vector-first strategy: retrieve JD snippets mentioning the term and aggregate.
        if intent.primary_intent == 'count_query' and (not intent.specialization_explicit) and intent.topic_or_keyword:
            return 'hybrid_vector_sql_aggregate'

        # If SQL is primary and validated, use SQL-first strategy
        if routing_decision.primary_database == DatabaseType.SQL and routing_decision.sql_capable:
            return 'sql_first'
        
        # If both databases needed, use hybrid strategy
        if routing_decision.primary_database == DatabaseType.BOTH:
            return 'hybrid_sql_vector'

        # NEW: If this is a count query with a generic topic/keyword (no explicit specialization),
        # prefer a hybrid vector-first strategy: retrieve JD snippets mentioning the term and aggregate.
        if intent.primary_intent == 'count_query' and (not intent.specialization_explicit) and intent.topic_or_keyword:
            return 'hybrid_vector_sql_aggregate'
        
        # Multi-company comparison
        if company_count > 1:
            return 'parallel_comparison'
        
        # Count available sources
        available_sources = sum(
            1 for status in data_availability.values() 
            if status.available
        )
        
        if available_sources > 1:
            return 'parallel_multi_source'
        
        if available_sources == 1:
            return 'single_source'
        
        return 'general_advice_mode'
    
    def _identify_gaps(
        self, 
        data_availability: Dict[str, DataSourceStatus]
    ) -> List[str]:
        """Identify expected data gaps."""
        gaps = []
        
        for key, status in data_availability.items():
            if not status.available or status.quality == 'low':
                gaps.append(
                    f"{status.source_type.replace('_', ' ')} for {status.company}"
                )
        
        return gaps
    
    def _determine_primary_strategy(
        self,
        intent: QueryIntent,
        data_availability: Dict[str, DataSourceStatus],
        company_count: int
    ) -> str:
        """Determine primary execution strategy."""
        
        # Multi-company comparison
        if company_count > 1:
            return 'parallel_comparison'
        
        # Count available sources
        available_sources = sum(
            1 for status in data_availability.values() 
            if status.available
        )
        
        if available_sources > 1:
            return 'parallel_multi_source'
        
        if available_sources == 1:
            return 'single_source'
        
        return 'general_advice_mode'
    
    def _create_fallback_strategies(
        self,
        intent: QueryIntent,
        data_availability: Dict[str, DataSourceStatus],
        primary_strategy: str
    ) -> List[str]:
        """Create fallback strategies."""
        fallbacks = []
        
        if primary_strategy == 'parallel_multi_source':
            fallbacks.append('jd_only')
        
        if intent.company:
            fallbacks.append('remove_company_filter')
        
        fallbacks.append('general_advice')
        
        return fallbacks
    
    def _map_sources_per_company(
        self,
        companies: List[str],
        data_availability: Dict[str, DataSourceStatus],
        intent: QueryIntent
    ) -> Dict[str, List[str]]:
        """Map which sources to query per company."""
        sources_per_company = {}
        
        for company in companies:
            if company == '*':
                sources_per_company[company] = ['jd']  # Only JD for wildcard
                continue
            
            available_sources = []
            
            for source in intent.sources_needed:
                key = f"{company}:{source}"
                if key in data_availability and data_availability[key].available:
                    available_sources.append(source)
            
            # Always include JD as baseline
            if 'jd' not in available_sources and 'jd' in intent.sources_needed:
                available_sources.insert(0, 'jd')
            
            sources_per_company[company] = available_sources or ['jd']
        
        return sources_per_company
    
    def _determine_synthesis_adaptations(
        self,
        expected_gaps: List[str],
        data_availability: Dict[str, DataSourceStatus],
        intent: QueryIntent
    ) -> List[str]:
        """Determine how synthesis should adapt."""
        adaptations = []
        
        if any('interview' in gap for gap in expected_gaps):
            adaptations.append('acknowledge_no_interview_data')
            adaptations.append('suggest_general_interview_prep')
        
        if any('alumni' in gap for gap in expected_gaps):
            adaptations.append('acknowledge_no_alumni_feedback')
            adaptations.append('focus_on_jd_analysis')
        
        if any('gd' in gap for gap in expected_gaps):
            adaptations.append('acknowledge_no_gd_topics')
        
        if intent.requires_comparison:
            adaptations.append('acknowledge_data_asymmetry')
        
        return adaptations
    
    def _calculate_complexity(
        self,
        company_count: int,
        source_count: int,
        data_gaps: int,
        intent: QueryIntent
    ) -> float:
        """Calculate query complexity score (0-1)."""
        
        complexity = (company_count * 0.3) + (source_count * 0.2)
        
        if intent.requires_comparison:
            complexity += 0.3
        
        complexity += min(data_gaps * 0.1, 0.2)
        
        if intent.primary_intent in ['prepare_interview', 'compare_companies']:
            complexity += 0.2
        
        return min(complexity, 1.0)


# Global instance
planning_agent = PlanningAgent()
