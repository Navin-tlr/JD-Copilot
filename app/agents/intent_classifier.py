"""
Intent Classifier Agent - Extracts structured intent from queries.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import re
from app.navigation_map import navigation_map


@dataclass
class QueryIntent:
    """Structured intent classification result."""
    primary_intent: str
    secondary_intent: Optional[str]
    company: Optional[str]
    role_type: Optional[str]
    specialization: Optional[str]  # Marketing, Finance, Operations, Data Analytics, HR
    sources_needed: List[str]
    response_format: str
    complexity: str  # low, medium, high
    requires_comparison: bool
    # When user mentions a domain term that is NOT one of the predefined specializations
    # (e.g., "blockchain", "AI safety", "renewables"), capture it generically here.
    # This MUST NOT be auto-mapped to a specialization.
    topic_or_keyword: Optional[str] = None
    specialization_explicit: bool = False  # True if specialization mentioned in query, False if inferred
    data_availability: str = "available"  # 'available' or 'not_found'
    suggestions: Optional[Dict] = None  # Alternative suggestions when data not found


class IntentClassifier:
    """Classifies user intent to determine agent pipeline."""
    
    # Intent patterns (rule-based for speed)
    INTENT_PATTERNS = {
        'prepare_interview': [
            'prepare', 'interview', 'tips', 'how to crack', 'advice', 'prep'
        ],
        'get_gd_topics': [
            'gd topic', 'group discussion', 'gd', 'discussion topic'
        ],
        'get_alumni_feedback': [
            'experience', 'alumni', 'feedback', 'review', 'how was'
        ],
        'get_jd_details': [
            'eligibility', 'ctc', 'salary', 'package', 'location', 
            'role', 'responsibilities', 'requirements', 'details'
        ],
        'compare_companies': [
            'compare', 'vs', 'versus', 'difference', 'better', 'which one'
        ],
        'count_query': [
            'how many', 'count', 'list all', 'show all', 'which companies'
        ]
    }
    
    # Source mapping (which sources to query per intent)
    INTENT_SOURCES = {
        'prepare_interview': ['jd', 'interview', 'alumni'],
        'get_gd_topics': ['gd_topic', 'alumni'],
        'get_alumni_feedback': ['alumni', 'jd'],
        'get_jd_details': ['jd'],
        'compare_companies': ['jd', 'alumni'],
        'count_query': ['jd']
    }
    
    # Response format templates
    RESPONSE_FORMATS = {
        'prepare_interview': 'interview_prep_guide',
        'get_gd_topics': 'topic_list',
        'get_alumni_feedback': 'experience_summary',
        'get_jd_details': 'structured_info',
        'compare_companies': 'comparison_table',
        'count_query': 'simple_count'
    }
    
    def classify(
        self, 
        query: str, 
        context: Optional[Dict] = None
    ) -> QueryIntent:
        """
        Classify user intent from query and conversation context.
        
        Args:
            query: Raw user query
            context: Conversation context (from Historic Conversation Agent)
        
        Returns:
            QueryIntent with full classification
        """
        query_lower = query.lower()
        
        # Detect primary intent
        primary_intent = self._detect_primary_intent(query_lower)
        
        # Detect secondary intent
        secondary_intent = self._detect_secondary_intent(query_lower, primary_intent)
        
        # Extract company
        company = self._extract_company(query_lower, context)
        
        # Extract role type
        role_type = self._extract_role_type(query_lower, context)
        
        # Extract specialization (Marketing, Finance, Operations, Analytics, HR, General)
        # Returns (specialization, is_explicit) tuple
        # CRITICAL: Only explicit mentions (with #) are treated as specializations
        specialization, specialization_explicit = self._extract_specialization(query_lower, context)

        # Extract a generic topic/keyword when no explicit specialization found
        # This allows flexible handling of terms like "blockchain", "FMCG", "AI safety", etc.
        topic_or_keyword = None
        if not specialization_explicit:
            topic_or_keyword = self._extract_topic_or_keyword(query_lower)
            # Clear any conversation context specialization to avoid false positives
            if specialization and not specialization_explicit:
                print(f"   ℹ️  Ignoring context specialization '{specialization}' - not explicitly requested")
                specialization = None
        
        # Validate with Navigation Map ONLY if specialization is explicit
        data_availability = 'available'
        suggestions = None
        
        if company and specialization and specialization_explicit:
            if not navigation_map.exists(company, specialization):
                # Data doesn't exist - get suggestions
                suggestions = navigation_map.suggest_alternatives(company, specialization)
                data_availability = 'not_found'
                print(f"⚠️ Navigation Map: {company} + {specialization} not found")
        
        # Determine sources needed
        sources_needed = self._determine_sources(
            primary_intent, 
            secondary_intent,
            company
        )
        
        # Determine response format
        response_format = self.RESPONSE_FORMATS.get(
            primary_intent, 
            'structured_info'
        )
        
        # Assess complexity
        complexity = self._assess_complexity(
            primary_intent,
            secondary_intent,
            len(sources_needed),
            bool(company)
        )
        
        # Check if comparison needed
        requires_comparison = (
            primary_intent == 'compare_companies' or
            secondary_intent == 'compare_companies'
        )
        
        # Store data availability and suggestions
        intent_data = {
            'primary_intent': primary_intent,
            'secondary_intent': secondary_intent,
            'company': company,
            'role_type': role_type,
            'specialization': specialization,
            'sources_needed': sources_needed,
            'response_format': response_format,
            'data_availability': data_availability,
            'suggestions': suggestions
        }
        
        # Create intent with all fields including navigation map validation results
        intent = QueryIntent(
            primary_intent=primary_intent,
            secondary_intent=secondary_intent,
            company=company,
            role_type=role_type,
            specialization=specialization,
            topic_or_keyword=topic_or_keyword,
            specialization_explicit=specialization_explicit,
            sources_needed=sources_needed,
            response_format=response_format,
            complexity=complexity,
            requires_comparison=requires_comparison,
            data_availability=data_availability,
            suggestions=suggestions
        )
        
        print(f"🎯 Intent Classification:")
        print(f"   Primary: {intent.primary_intent}")
        print(f"   Company: {intent.company or 'Not specified'}")
        if specialization:
            spec_type = "Explicit" if specialization_explicit else "Inferred"
            print(f"   Specialization: {specialization} ({spec_type})")
        if topic_or_keyword and not specialization_explicit:
            print(f"   Topic/Keyword: {topic_or_keyword} (generic)")
        if data_availability == 'not_found':
            print(f"   ⚠️ Data Availability: NOT FOUND")
        print(f"   Sources: {', '.join(intent.sources_needed)}")
        print(f"   Complexity: {intent.complexity}")
        
        return intent
    
    def _detect_primary_intent(self, query_lower: str) -> str:
        """Detect primary intent using pattern matching."""
        for intent, patterns in self.INTENT_PATTERNS.items():
            if any(pattern in query_lower for pattern in patterns):
                return intent
        return 'get_jd_details'  # Default fallback
    
    def _detect_secondary_intent(
        self, 
        query_lower: str, 
        primary_intent: str
    ) -> Optional[str]:
        """Detect secondary intent."""
        for intent, patterns in self.INTENT_PATTERNS.items():
            if intent != primary_intent:
                if any(pattern in query_lower for pattern in patterns):
                    if intent in ['compare_companies', 'get_alumni_feedback']:
                        return intent
        return None
    
    def _extract_company(
        self, 
        query_lower: str, 
        context: Optional[Dict]
    ) -> Optional[str]:
        """Extract company from query or context."""
        # Check query
        company_pattern = r'\b(honasa|target|uniqlo|masters\s*union|wns|mill\s*story|acuity|alstom|madison)\b'
        match = re.search(company_pattern, query_lower)
        if match:
            return match.group(1).replace(' ', '')
        
        # Check context
        if context and context.get('company'):
            return context['company']
        
        return None
    
    def _extract_role_type(
        self, 
        query_lower: str, 
        context: Optional[Dict]
    ) -> Optional[str]:
        """Extract role type from query or context."""
        role_keywords = {
            'sales': ['sales', 'business development', 'bd'],
            'marketing': ['marketing', 'brand', 'digital marketing'],
            'finance': ['finance', 'accounting', 'ca', 'cma'],
            'tech': ['software', 'developer', 'engineer', 'sde', 'tech'],
            'operations': ['operations', 'ops', 'supply chain']
        }
        
        for role_type, keywords in role_keywords.items():
            if any(kw in query_lower for kw in keywords):
                return role_type
        
        # Check context
        if context and context.get('role_type'):
            return context['role_type']
        
        return None
    
    def _extract_specialization(
        self,
        query_lower: str,
        context: Optional[Dict]
    ) -> tuple[Optional[str], bool]:
        """
        Extract specialization from query or context.
        Returns: (specialization, is_explicit)
        - is_explicit=True ONLY if specialization was explicitly typed with # or selected from popup
        - is_explicit=False if inferred from context
        
        CRITICAL: Do NOT auto-map keywords to specializations. Only recognize explicit mentions.
        Specializations: Marketing, Finance, Operations, Data Analytics, HR, IT, Strategy
        """
        # STRICT: Only match if query contains "#SpecializationName" pattern (user explicitly selected)
        # Example: "how many companies for #Finance?" 
        # This prevents false matches like "FMCG" → "Finance"
        
        explicit_specializations = [
            'Marketing', 'Finance', 'Operations', 'Data Analytics', 
            'HR', 'IT', 'Strategy', 'Analytics'
        ]
        
        # Check for explicit # mention (highest priority - user selected from popup)
        for spec in explicit_specializations:
            if f'#{spec.lower()}' in query_lower or f'# {spec.lower()}' in query_lower:
                return spec, True
        
        # REMOVED: Keyword-based auto-detection that caused false positives
        # Users must either:
        # 1. Type "#Specialization" to explicitly select
        # 2. Or let the system treat unknown terms as generic topics/keywords
        
        # Check context - if found here, it's INFERRED from previous conversation
        if context and context.get('specialization'):
            return context['specialization'], False  # Inferred from context
        
        return None, False  # No specialization found

    def _extract_topic_or_keyword(self, query_lower: str) -> Optional[str]:
        """Extract a generic topic/keyword phrase without mapping it to specialization.
        Example: "how many came for blockchain" -> "blockchain"
        The extraction is lightweight and avoids hardcoded mappings.
        """
        # Ignore if user clearly asked for totals without a qualifier
        if re.search(r"\b(total|overall|in\s+total)\b", query_lower):
            return None

        # Look for simple prepositional patterns commonly used by users
        # Keep the phrase short (1-3 words), strip punctuation
        patterns = [
            r"\bfor\s+([a-z0-9\-\s]{1,40})",
            r"\bin\s+([a-z0-9\-\s]{1,40})",
            r"\babout\s+([a-z0-9\-\s]{1,40})"
        ]
        stop_terms = {
            'companies','company','roles','jobs','placements','internships','campus','profile','profiles',
            'specialization','specializations','domains','categories','streams','positions','offers','ctc'
        }
        for pat in patterns:
            m = re.search(pat, query_lower)
            if not m:
                continue
            phrase = m.group(1).strip()
            # Trim trailing fillers
            phrase = re.sub(r"\b(came|came\s+for|are|were|offered|offer|offers)\b.*$", "", phrase).strip()
            # Take up to 3 words
            words = [w for w in re.split(r"\s+", phrase) if w and w not in stop_terms]
            if not words:
                continue
            cleaned = " ".join(words[:3])
            # Return the cleaned keyword/topic (no longer skip specialization keywords)
            return cleaned
        return None
    
    def _determine_sources(
        self,
        primary_intent: str,
        secondary_intent: Optional[str],
        company: Optional[str]
    ) -> List[str]:
        """Determine which sources to query."""
        sources = set(self.INTENT_SOURCES.get(primary_intent, ['jd']))
        
        # Add secondary intent sources
        if secondary_intent:
            sources.update(self.INTENT_SOURCES.get(secondary_intent, []))
        
        # If no company specified and asking about counts, only query JD
        if not company and primary_intent == 'count_query':
            return ['jd']
        
        return list(sources)
    
    def _assess_complexity(
        self,
        primary_intent: str,
        secondary_intent: Optional[str],
        source_count: int,
        has_company: bool
    ) -> str:
        """Assess query complexity for routing decisions."""
        
        # High complexity
        if secondary_intent or source_count > 2:
            return 'high'
        
        # Medium complexity
        if source_count == 2 or primary_intent in ['prepare_interview', 'compare_companies']:
            return 'medium'
        
        # Low complexity
        return 'low'


# Global instance
intent_classifier = IntentClassifier()
