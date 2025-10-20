"""
Agent Orchestrator - Coordinates all agents in the pipeline.
"""

import re
from functools import lru_cache
from typing import Any, Dict, List, Optional
from .intent_classifier import intent_classifier
from .planning_agent import planning_agent
from .route_decider import route_decider
from .data_quality_agent import data_quality_agent


@lru_cache(maxsize=1)
def _load_company_industry_map() -> Dict[str, str]:
    """Lazy-load mapping from normalized company name to industry for filtering."""
    try:
        from app.database import PlacementDatabase

        db = PlacementDatabase()
        companies = db.get_companies() or []
        mapping: Dict[str, str] = {}
        for row in companies:
            name = (row.get("company_name") or "").strip().lower()
            if not name:
                continue
            industry = (row.get("industry") or "").strip()
            if industry:
                mapping[name] = industry
        return mapping
    except Exception:
        # If the structured database is unavailable, fall back to empty mapping.
        return {}


class AgentOrchestrator:
    """
    Orchestrates the complete agent pipeline.
    
    Pipeline:
    1. Intent Classification
    2. Planning
    3. Route Decision
    4. Conversation (if needed)
    5. Retrieval
    6. Quality Check
    7. Synthesis
    """

    # Normalized topic synonyms to improve semantic filtering when aggregating companies
    TOPIC_SYNONYMS = {
        "fmcg": [
            "fast moving consumer goods",
            "fast moving consumer good",
            "fast moving consumer-goods",
            "fast moving consumer",
            "consumer goods",
            "consumer packaged goods",
            "consumer package goods",
            "cpg",
        ],
        "consumer goods": [
            "fmcg",
            "consumer packaged goods",
            "cpg",
            "fast moving consumer goods",
        ],
        "portfolio management": [
            "portfolio manager",
            "investment management",
            "investment manager",
            "asset management",
            "wealth management",
            "investment portfolio",
        ],
        "investment banking": [
            "investment bank",
            "capital markets",
            "mergers acquisitions",
            "m&a",
            "equity capital markets",
            "debt capital markets",
        ],
        "finance": [
            "financial analysis",
            "corporate finance",
            "financial analyst",
            "treasury",
            "investment banking",
        ],
        "marketing": [
            "brand management",
            "digital marketing",
            "market research",
            "brand marketing",
        ],
        "sales": [
            "business development",
            "account executive",
            "inside sales",
            "field sales",
        ],
        "lean operation and systems": [
            "supply chain",
            "logistics",
            "procurement",
            "manufacturing",
        ],
        "supply chain": [
            "lean operation and systems",
            "logistics",
            "procurement",
            "inventory management",
        ],
        "analytics": [
            "business analytics",
            "data analytics",
            "data science",
            "business intelligence",
        ],
        "human resources": [
            "hr",
            "people operations",
            "talent acquisition",
            "human resource",
            "talent management",
        ],
        "product management": [
            "product manager",
            "product strategy",
            "product owner",
            "product development",
        ],
        "strategy": [
            "management consulting",
            "strategy consulting",
            "business strategy",
        ],
        "technology": [
            "information technology",
            "software engineering",
            "it",
            "technology consulting",
        ],
    }

    TOPIC_STRUCTURED_HINTS = {
        "fmcg": {
            "industries": {
                "fast moving consumer goods",
                "consumer goods",
                "consumer packaged goods",
                "cpg",
                "beauty and personal care",
                "personal care",
                "household products",
                "food and beverages",
            },
            "specializations": {"marketing", "lean operation and systems", "general"},
        },
        "consumer goods": {
            "industries": {
                "consumer goods",
                "consumer packaged goods",
                "cpg",
                "retail consumer",
                "d2c",
            },
            "specializations": {"marketing", "lean operation and systems", "general"},
        },
        "investment banking": {
            "industries": {
                "investment banking",
                "financial services",
                "banking",
                "capital markets",
                "corporate finance",
            },
            "specializations": {"finance"},
        },
        "finance": {
            "industries": {
                "financial services",
                "banking",
                "corporate finance",
                "treasury",
                "asset management",
            },
            "specializations": {"finance"},
        },
        "marketing": {
            "industries": {
                "advertising",
                "brand marketing",
                "digital marketing",
                "consumer goods",
            },
            "specializations": {"marketing", "general"},
        },
        "analytics": {
            "industries": {
                "analytics",
                "data science",
                "business analytics",
            },
            "specializations": {"analytics"},
        },
        "human resources": {
            "industries": {
                "human resources",
                "talent management",
                "people operations",
            },
            "specializations": {"hr", "general"},
        },
        "lean operation and systems": {
            "industries": {
                "lean operation and systems",
                "supply chain",
                "logistics",
                "procurement",
                "manufacturing",
            },
            "specializations": {"lean operation and systems"},
        },
    }

    TOPIC_STOPWORDS = {
        "how",
        "many",
        "companies",
        "company",
        "came",
        "come",
        "for",
        "and",
        "who",
        "what",
        "are",
        "is",
        "the",
        "a",
        "an",
        "in",
        "of",
        "to",
        "with",
        "from",
        "list",
        "show",
        "tell",
        "give",
        "me",
        "their",
        "that",
        "which",
        "count",
        "detail",
        "details",
        "role",
        "roles",
        "job",
        "jobs",
        "openings",
        "positions",
        "available",
        "generic",
        "data",
        "need",
        "want",
        "please",
    }
    
    def __init__(self):
        """Initialize orchestrator."""
        pass
    
    async def process_query(
        self,
        query: str,
        session_id: str,
        user_id: str = "student-123",
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Process query through complete agent pipeline.
        
        Args:
            query: User query
            session_id: Session ID for conversation memory
            user_id: User ID
            context: Optional conversation context
        
        Returns:
            Dict with response and metadata
        """
        
        print(f"\n{'='*70}")
        print(f"🚀 Agent Pipeline Started")
        print(f"Query: {query[:60]}{'...' if len(query) > 60 else ''}")
        print(f"{'='*70}\n")
        
        try:
            # Stage 0: Intent Classification
            print("🎯 Stage 0: Classifying intent...")
            intent = intent_classifier.classify(query, context=context)
            
            # Stage 0.5: Planning
            print(f"\n📋 Stage 0.5: Creating execution plan...")
            plan = await planning_agent.create_plan(intent, context=context)
            
            # Stage 1: Route Decision
            print(f"🚦 Stage 1: Determining route...")
            routing = route_decider.decide(intent, plan)
            print()
            
            # Build minimal context if not provided
            if not context:
                context = {}
            
            context['original_query'] = query
            context['intent'] = intent.primary_intent
            context['company'] = intent.company
            context['specialization'] = intent.specialization  # Add specialization to context
            context['topic_or_keyword'] = intent.topic_or_keyword  # Add topic/keyword for flexible routing
            context['intent_object'] = intent  # Pass full intent for synthesis access
            
            # Stage 2: Conversation Agent (if needed)
            if 'conversation' in routing.agent_pipeline:
                print(f"📖 Stage 2: Processing conversation context...")
                # Use existing conversation memory system
                from app.enhanced_chat_memory import EnhancedConversationMemory
                
                memory = EnhancedConversationMemory(
                    session_id=session_id,
                    user_id=user_id
                )
                
                # Resolve context - returns (resolved_query, extracted_context)
                resolved_result = memory.resolve_context(query)
                if isinstance(resolved_result, tuple):
                    resolved_query, extracted_context = resolved_result
                else:
                    resolved_query = resolved_result
                    extracted_context = {}
                
                context['resolved_query'] = resolved_query
                
                # Update company if found in context
                if not context.get('company') and memory.current_context.get('last_company'):
                    context['company'] = memory.current_context['last_company']
                
                print(f"   ✅ Resolved: {resolved_query[:60]}...")
                print(f"   Company: {context.get('company', 'Not specified')}\n")
            
            # Check if navigation map validation failed (no data available)
            if plan.primary_strategy == 'suggestion_response':
                print(f"🔍 Stage 3: SKIPPING RETRIEVAL (Data not available)")
                print(f"   Using suggestion response mode instead\n")
                
                # Skip retrieval, go directly to synthesis with suggestions
                response = await self._execute_suggestion_response(
                    context=context,
                    intent=intent,
                    plan=plan
                )
                
                print(f"   ✅ Generated suggestion response\n")
                print(f"{'='*70}")
                print(f"🎉 Pipeline Complete (Suggestion Mode)")
                print(f"{'='*70}\n")
                
                return {
                    'response': response,
                    'metadata': {
                        'intent': intent.primary_intent,
                        'company': intent.company,
                        'mode': 'suggestion_response',
                        'data_available': False,
                        'suggestions': intent.suggestions
                    }
                }
            
            # Stage 3: Retrieval
            print(f"🔍 Stage 3: Retrieving from sources...")
            print(f"   Strategy: {routing.retrieval_strategy}")
            
            retrieval_results = await self._execute_retrieval(
                context=context,
                intent=intent,
                plan=plan,
                strategy=routing.retrieval_strategy
            )
            # If strategy requests hybrid vector-first aggregation for counts, aggregate by company
            if routing.retrieval_strategy == 'hybrid_vector_sql_aggregate' and 'jd' in retrieval_results:
                print("   🔢 Aggregating vector results by company for keyword-based count")
                topic = getattr(context.get('intent_object') or {}, 'topic_or_keyword', None) or context.get('topic_or_keyword')
                user_query = context.get('resolved_query') or context.get('original_query')
                agg = self._aggregate_by_company(
                    retrieval_results['jd'].snippets,
                    topic=topic,
                    raw_query=user_query
                )
                retrieval_results['vector_aggregate'] = agg
            
            # Stage 4: Quality Check
            if 'quality' in routing.agent_pipeline:
                print(f"\n✓ Stage 4: Validating data quality...")
                quality_report = data_quality_agent.validate(
                    retrieval_results=retrieval_results,
                    expected_companies=plan.companies_to_query,
                    expected_sources=intent.sources_needed
                )
                print()
            else:
                quality_report = None
            
            # Stage 5: Synthesis
            print(f"✨ Stage 5: Synthesizing response...")
            print(f"   Mode: {routing.synthesis_mode}")
            
            response = await self._execute_synthesis(
                context=context,
                retrieval_results=retrieval_results,
                synthesis_mode=routing.synthesis_mode,
                plan=plan,
                quality_report=quality_report
            )
            
            print(f"   ✅ Generated ({len(response)} chars)\n")
            
            print(f"{'='*70}")
            print(f"🎉 Pipeline Complete")
            print(f"{'='*70}\n")
            
            return {
                'response': response,
                'metadata': {
                    'intent': intent.primary_intent,
                    'company': intent.company,
                    'sources_used': list(retrieval_results.keys()),
                    'confidence': quality_report.confidence_score if quality_report else 0.8,
                    'complexity': plan.complexity_score
                }
            }
        
        except Exception as e:
            print(f"\n❌ Pipeline error: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to simple response
            return {
                'response': f"I encountered an error processing your query. Please try rephrasing or contact support. Error: {str(e)[:100]}",
                'metadata': {
                    'error': str(e),
                    'fallback': True
                }
            }
    
    async def _execute_retrieval(
        self,
        context: Dict,
        intent,
        plan,
        strategy: str
    ) -> Dict:
        """Execute retrieval using intelligent database routing from planning agent."""
        
        # Check if plan specifies database routing
        if hasattr(plan, 'database_routing') and plan.database_routing:
            routing = plan.database_routing
            print(f"   🧭 Using intelligent database routing")
            print(f"      Primary DB: {routing.primary_database.value.upper()}")
            print(f"      Confidence: {routing.confidence:.0%}")
            
            # Try SQL first if plan says so
            if plan.use_sql_database and plan.sql_query_validated:
                sql_result = await self._try_sql_query(context, intent, plan)
                if sql_result:
                    print(f"   ✅ SQL database returned valid results")
                    return {'sql': sql_result}
                else:
                    print(f"   ⚠️  SQL query returned no results, falling back...")
            
            # Use vector database if plan says so (or as fallback)
            if plan.use_vector_database:
                return await self._execute_vector_retrieval(context, intent, plan, strategy)
        
        # LEGACY: Fallback to old logic if no routing in plan
        # Try SQL first for count queries with specialization
        if intent.primary_intent == 'count_query' and intent.specialization:
            sql_result = await self._try_sql_count(context, intent)
            if sql_result:
                print(f"   ✅ Using SQL database (accurate count)")
                return {'sql': sql_result}
        
        # Fallback to vector search
        return await self._execute_vector_retrieval(context, intent, plan, strategy)
    
    async def _try_sql_query(self, context: Dict, intent, plan) -> Optional[Dict]:
        """Try to answer query using SQL database with schema validation."""
        from app.sql_tool import execute_canonical_query
        import asyncio
        
        specialization = intent.specialization
        company = intent.company
        resolved_query = context.get('resolved_query', context.get('original_query', ''))
        
        # Check schema validation from plan
        if hasattr(plan, 'schema_validation') and plan.schema_validation:
            if not plan.schema_validation.get('valid', False):
                print(f"   ⚠️  SQL schema validation failed: {plan.schema_validation.get('reason', 'Unknown')}")
                return None
        
        try:
            # Run SQL query in thread pool (it's sync)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                execute_canonical_query,
                resolved_query
            )
            
            if result and 'result' in result:
                # SQL query succeeded - extract data
                sql_data = result['result']
                
                # Parse result based on query type
                if isinstance(sql_data, list):
                    # List query result
                    return {
                        'source': 'sql',
                        'type': 'list',
                        'specialization': specialization,
                        'company': company,
                        'items': sql_data,
                        'count': len(sql_data),
                        'query': result.get('query', ''),
                        'accurate': True
                    }
                elif isinstance(sql_data, dict) and 'count' in sql_data:
                    # Count query result
                    return {
                        'source': 'sql',
                        'type': 'count',
                        'specialization': specialization,
                        'company': company,
                        'count': sql_data['count'],
                        'items': sql_data.get('companies', []),
                        'query': result.get('query', ''),
                        'accurate': True
                    }
                elif isinstance(sql_data, (int, float)):
                    # Simple count
                    return {
                        'source': 'sql',
                        'type': 'count',
                        'specialization': specialization,
                        'count': int(sql_data),
                        'query': result.get('query', ''),
                        'accurate': True
                    }
                else:
                    # Generic result
                    return {
                        'source': 'sql',
                        'type': 'generic',
                        'specialization': specialization,
                        'result': sql_data,
                        'query': result.get('query', ''),
                        'accurate': True
                    }
        except Exception as e:
            print(f"   ⚠️  SQL query error: {e}")
        
        return None
    
    async def _try_sql_count(self, context: Dict, intent) -> Optional[Dict]:
        """Try to answer count query using SQL database."""
        from app.sql_tool import execute_canonical_query
        import asyncio
        
        specialization = intent.specialization
        resolved_query = context.get('resolved_query', '')
        
        try:
            # Run SQL query in thread pool (it's sync)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                execute_canonical_query,
                resolved_query
            )
            
            if result and 'result' in result:
                # SQL query succeeded
                return {
                    'source': 'sql',
                    'specialization': specialization,
                    'result': result['result'],
                    'query': result.get('query', ''),
                    'accurate': True
                }
        except Exception as e:
            print(f"   ⚠️  SQL query failed: {e}")
        
        return None
    
    async def _execute_vector_retrieval(
        self,
        context: Dict,
        intent,
        plan,
        strategy: str
    ) -> Dict:
        """Execute PARALLEL retrieval from vector sources."""
        import asyncio
        from app.rag import retrieve_snippets
        from dataclasses import dataclass
        
        @dataclass
        class SourceResult:
            source_type: str
            snippets: list
            count: int
        
        company = context.get('company')
        specialization = context.get('specialization')  # For specialization filtering
        specialization_explicit = intent.specialization_explicit if intent else False
        resolved_query = context.get('resolved_query', context.get('original_query'))
        
        # Support for hierarchy-based filtering (from > trigger UI)
        hierarchy_filter = context.get('hierarchy_filter')  # {specialization, level1, level2}
        
        # CRITICAL: Only query JD for now (interview/GD data not ingested yet)
        sources_to_query = ['jd']
        
        print(f"   Querying sources: {', '.join(sources_to_query)}")
        if hierarchy_filter:
            print(f"   🎯 Hierarchy Filter:")
            if hierarchy_filter.get('specialization'):
                print(f"      Specialization: {hierarchy_filter['specialization']}")
            if hierarchy_filter.get('level1'):
                print(f"      Level 1: {hierarchy_filter['level1']}")
            if hierarchy_filter.get('level2'):
                print(f"      Level 2: {hierarchy_filter['level2']}")
        elif specialization:
            if specialization_explicit:
                print(f"   Specialization: {specialization} (EXPLICIT - will guide semantic search)")
            else:
                print(f"   Specialization: {specialization} (inferred, NOT filtering)")
        
        base_filter: Dict[str, Any] = {}
        company_norm = None
        if company and company != '*':
            company_norm = company.lower().replace(" ", "").replace("-", "")
            base_filter['company_norm'] = company_norm
            print(f"   Filter: company={company_norm}")
        else:
            print("   Filter: no company filter (global search)")

        # Priority: Hierarchy filter from UI > Explicit specialization > No filter
        if hierarchy_filter:
            # User selected from > trigger UI - use hierarchy metadata
            if hierarchy_filter.get('level1'):
                base_filter['industry_level1'] = hierarchy_filter['level1']
                print(f"   Filter ➕ industry_level1: {hierarchy_filter['level1']}")
            
            if hierarchy_filter.get('specialization'):
                # Use raw specialization value directly (no normalization)
                spec_raw = hierarchy_filter['specialization']
                
                base_filter['$or'] = [
                    {'specializations': {'$in': [spec_raw]}},
                    {'is_general': True}
                ]
                print(f"   Filter ➕ specialization: {spec_raw} OR General")
        
        elif specialization and specialization_explicit:
            # ONLY add specialization filter if explicitly mentioned in query
            # Use raw specialization value directly (no normalization)
            
            # Add specialization filter using $or logic while preserving company constraint
            # Match if: (specialization in specializations array) OR (is_general = true)
            base_filter['$or'] = [
                {'specializations': {'$in': [specialization]}},
                {'is_general': True}
            ]
            print(f"   Filter ➕ specialization: {specialization} (explicit) OR General")
        elif specialization:
            print("   Note: specialization inferred from context, not applying metadata filter")
        
        # Define async retrieval task
        async def fetch_source(source_type: str) -> tuple:
            """Fetch from a single source asynchronously."""
            try:
                # Build filter with source_type
                filter_dict = base_filter.copy()
                # filter_dict['source_type'] = source_type  # Future: when we have metadata
                
                # Run retrieve_snippets in thread pool (it's sync, not async)
                loop = asyncio.get_event_loop()
                snippets = await loop.run_in_executor(
                    None,
                    retrieve_snippets,
                    resolved_query,
                    50,  # top_k increased to capture full role coverage
                    filter_dict if filter_dict else {}
                )
                
                # TEMPORARY: Filter by source_type if metadata exists
                # For now, only JD data exists
                if source_type != 'jd':
                    snippets = []  # No data yet for other sources
                
                return (source_type, snippets, None)
                
            except Exception as e:
                return (source_type, [], str(e))
        
        # Execute ALL queries in PARALLEL
        tasks = [fetch_source(source_type) for source_type in sources_to_query]
        results_list = await asyncio.gather(*tasks)
        
        # Build results dict
        results = {}
        for source_type, snippets, error in results_list:
            if error:
                print(f"   ⚠️  {source_type}: Failed ({error[:50]})")
            else:
                print(f"   ✅ {source_type}: {len(snippets)} snippets")
            
            results[source_type] = SourceResult(
                source_type=source_type,
                snippets=snippets if not error else [],
                count=len(snippets) if not error else 0
            )
        
        return results

    def _aggregate_by_company(self, snippets: list, *, topic: Optional[str] = None, raw_query: Optional[str] = None) -> dict:
        """
        Aggregate snippets by company with intelligent metadata filtering.
        Uses hierarchical industry classification stored in Pinecone metadata.
        """

        if not snippets:
            return {'count': 0, 'companies': []}

        # Step 1: Try to map user's query to Level 1 category using LLM
        level1_filter = self._infer_level1_category(topic, raw_query)
        if level1_filter:
            print(f"   🏭 Inferred Level 1 category: {level1_filter}")
        
        matched_companies: List[str] = []
        fallback_companies: List[str] = []
        seen: set[str] = set()
        filtered_out = 0

        for sn in snippets:
            metadata = sn.get('metadata') or {}
            company = (metadata.get('company') or '').strip()
            if not company:
                continue

            norm_company = company.lower()
            if norm_company in seen:
                continue

            fallback_companies.append(company)

            # Apply metadata-based filtering
            if self._snippet_matches_industry(sn, level1_filter, topic, raw_query):
                seen.add(norm_company)
                matched_companies.append(company)
            else:
                filtered_out += 1

        if matched_companies:
            if filtered_out:
                print(f"   🔍 Industry filter kept {len(matched_companies)} companies, removed {filtered_out} misaligned candidates")
            return {'count': len(matched_companies), 'companies': sorted(set(matched_companies))}

        # Fallback: if everything was filtered out, return unfiltered aggregate
        if fallback_companies:
            print("   ⚠️ Industry filter rejected all companies; returning unfiltered aggregate as fallback")
            deduped = []
            seen.clear()
            for company in fallback_companies:
                key = company.lower()
                if key in seen:
                    continue
                seen.add(key)
                deduped.append(company)
            return {'count': len(deduped), 'companies': sorted(deduped)}

        return {'count': 0, 'companies': []}

    def _build_topic_keywords(self, topic: Optional[str], raw_query: Optional[str]) -> Dict[str, Any]:
        """Create normalized keyword bundles (phrases + tokens) for topic filtering."""

        sources = [topic or "", raw_query or ""]
        normalized_inputs = []
        for text in sources:
            normalized = self._normalize_topic_text(text)
            if normalized:
                normalized_inputs.append(normalized)

        canonical_hits: set[str] = set()
        for canonical, synonyms in self.TOPIC_SYNONYMS.items():
            candidates = [canonical] + synonyms
            for alias in candidates:
                alias_norm = self._normalize_topic_text(alias)
                if not alias_norm:
                    continue
                if any(alias_norm in text for text in normalized_inputs):
                    canonical_hits.add(canonical)
                    break

        # Expand with synonyms based on detected canonical topic fragments
        expanded: List[str] = list(normalized_inputs)
        for candidate in list(normalized_inputs):
            for canonical, synonyms in self.TOPIC_SYNONYMS.items():
                if canonical and canonical in candidate:
                    expanded.extend(synonyms)

        structured_hints: Dict[str, Dict[str, Any]] = {}
        for canonical in canonical_hits:
            raw_hints = self.TOPIC_STRUCTURED_HINTS.get(canonical)
            if not raw_hints:
                continue
            industries = self._normalize_hint_collection(raw_hints.get("industries", set()))
            industry_tokens = set()
            for alias in industries:
                industry_tokens.update(tok for tok in alias.split() if tok)
            keywords = self._normalize_hint_collection(raw_hints.get("keywords", set()))
            for alias in keywords:
                industry_tokens.update(tok for tok in alias.split() if tok)
            specializations = {spec.strip().lower() for spec in raw_hints.get("specializations", set()) if spec}
            structured_hints[canonical] = {
                "industries": industries,
                "industry_tokens": industry_tokens,
                "specializations": specializations,
            }

        phrases: set[str] = set()
        tokens: set[str] = set()
        for text in expanded:
            normalized = self._normalize_topic_text(text)
            if not normalized:
                continue
            phrases.add(normalized)
            tokens.update(tok for tok in normalized.split() if tok)

        tokens = {tok for tok in tokens if tok not in self.TOPIC_STOPWORDS and (len(tok) > 2 or tok in {"hr", "it", "ai", "ux", "cpg"})}

        if not phrases and tokens:
            phrases = set()

        token_threshold = 1 if len(tokens) <= 1 else min(2, len(tokens))

        return {
            'phrases': phrases,
            'tokens': tokens,
            'token_threshold': token_threshold,
            'canonical_topics': canonical_hits,
            'structured_hints': structured_hints,
        }

    def _normalize_topic_text(self, text: str) -> str:
        if not text:
            return ""
        cleaned = re.sub(r"[^a-z0-9&/+]+", " ", text.lower())
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        tokens = [tok for tok in cleaned.split() if tok and tok not in self.TOPIC_STOPWORDS]
        return " ".join(tokens)

    def _collect_snippet_haystack(self, snippet: Dict[str, Any]) -> str:
        """Collect textual fields from a snippet and its metadata for keyword matching."""

        parts: List[str] = []
        for key in ("text", "content", "page_content", "chunk_text", "summary", "title", "subtitle"):
            value = snippet.get(key)
            if isinstance(value, str):
                parts.append(value)

        metadata = snippet.get('metadata') or {}
        meta_fields = (
            "chunk_text",
            "summary",
            "specialization",
            "industry",
            "function",
            "role",
            "role_title",
            "role_types",
            "tags",
            "focus",
            "focus_area",
            "keywords",
            "topics",
        )
        for key in meta_fields:
            value = metadata.get(key)
            if isinstance(value, str):
                parts.append(value)
            elif isinstance(value, list):
                parts.extend(str(item) for item in value)

        haystack = " ".join(parts).lower()
        haystack = re.sub(r"\s+", " ", haystack).strip()
        return haystack

    def _snippet_matches_topic(
        self,
        snippet: Dict[str, Any],
        company_key: str,
        company_display: str,
        keyword_bundle: Dict[str, Any],
        industry_map: Dict[str, str],
        navigation_map
    ) -> bool:
        phrases = keyword_bundle.get('phrases') or set()
        tokens = keyword_bundle.get('tokens') or set()
        token_threshold = keyword_bundle.get('token_threshold', 1)
        canonical_topics = keyword_bundle.get('canonical_topics') or set()
        structured_hints = keyword_bundle.get('structured_hints') or {}

        if not phrases and not tokens:
            # No topic hint available; allow pass-through
            return True

        haystack = self._collect_snippet_haystack(snippet)

        # Enrich haystack with industry metadata if available from structured DB
        industry_value = industry_map.get(company_key)
        if industry_value:
            haystack = f"{haystack} {industry_value.lower()}"

        if not haystack:
            return False

        if any(phrase and phrase in haystack for phrase in phrases):
            return True

        if tokens:
            hits = {tok for tok in tokens if tok in haystack}
            if len(hits) >= token_threshold:
                return True

        if canonical_topics:
            industry_normalized = self._normalize_topic_text(industry_value) if industry_value else ""
            for canonical in canonical_topics:
                hints = structured_hints.get(canonical)
                if not hints:
                    continue
                for alias in hints.get('industries', set()):
                    if alias and alias in industry_normalized:
                        return True
                if hints.get('industry_tokens') and industry_normalized:
                    if any(tok in industry_normalized for tok in hints['industry_tokens']):
                        return True
                if navigation_map and company_display:
                    specs = {spec.lower() for spec in navigation_map.get_specializations(company_display)}
                    if specs and hints.get('specializations'):
                        if specs.intersection(hints['specializations']):
                            return True

        return False

    def _normalize_hint_collection(self, values) -> set:
        normalized = set()
        for value in values or []:
            norm = self._normalize_topic_text(str(value))
            if norm:
                normalized.add(norm)
        return normalized
    
    def _infer_level1_category(self, topic: Optional[str], raw_query: Optional[str]) -> Optional[str]:
        """
        Infer Level 1 industry subcategory from user query.
        
        Returns: FMCG, Investment Banking, Supply Chain, etc. (NOT specialization)
        """
        if not topic and not raw_query:
            return None
        
        query_text = f"{topic or ''} {raw_query or ''}".strip().lower()
        if not query_text:
            return None
        
        # Fast keyword matching for common queries
        keyword_to_level1 = {
            "fmcg": "FMCG",
            "fast moving consumer": "FMCG",
            "consumer goods": "FMCG",
            "cpg": "FMCG",
            "investment banking": "Investment Banking",
            "investment bank": "Investment Banking",
            "m&a": "Investment Banking",
            "mergers acquisitions": "Investment Banking",
            "supply chain": "Supply Chain",
            "logistics": "Logistics",
            "procurement": "Supply Chain",
            "manufacturing": "Manufacturing",
            "asset management": "Asset Management",
            "portfolio management": "Portfolio Management",
            "wealth management": "Wealth Management",
            "retail banking": "Retail Banking",
            "digital marketing": "Digital Marketing",
            "b2b sales": "B2B Sales",
            "market research": "Market Research",
            "talent acquisition": "Talent Acquisition",
            "people operations": "People Operations",
            "business analytics": "Business Analytics",
            "data science": "Data Science",
            "business intelligence": "Business Intelligence",
        }
        
        # Check for keyword matches
        for keyword, level1 in keyword_to_level1.items():
            if keyword in query_text:
                return level1
        
        return None
    
    def _snippet_matches_industry(
        self,
        snippet: Dict[str, Any],
        level1_filter: Optional[str],
        topic: Optional[str],
        raw_query: Optional[str]
    ) -> bool:
        """
        Check if snippet matches industry classification using metadata.
        
        Hierarchy:
        1. Specialization (already in metadata): Marketing, Finance, Operations, HR, Analytics
        2. Level 1 (industry subcategory): FMCG, Investment Banking, Supply Chain, etc.
        3. Level 2 (specific details): LLM-inferred
        """
        metadata = snippet.get('metadata') or {}
        
        # Get classification metadata from chunk
        chunk_specialization = metadata.get('specialization')  # Could be a list
        chunk_specializations = metadata.get('specializations', [])  # List format
        chunk_level1 = metadata.get('industry_level1')
        chunk_level2 = metadata.get('industry_level2', '').lower()
        
        # Normalize specialization to list
        all_specs = set()
        if isinstance(chunk_specialization, str):
            all_specs.add(chunk_specialization)
        if isinstance(chunk_specializations, list):
            all_specs.update(chunk_specializations)
        elif isinstance(chunk_specializations, str):
            all_specs.add(chunk_specializations)
        
        # If we have a Level 1 filter inferred from query, match against it
        if level1_filter and chunk_level1:
            if chunk_level1.lower() == level1_filter.lower():
                return True
        
        # Fallback: text-based matching on level2 for specific queries
        if topic or raw_query:
            query_text = f"{topic or ''} {raw_query or ''}".lower()
            query_normalized = self._normalize_topic_text(query_text)
            
            # Check if query terms appear in Level 2 classification
            if chunk_level2 and query_normalized:
                query_tokens = set(query_normalized.split())
                level2_tokens = set(chunk_level2.split())
                
                # If 40%+ query tokens match level2, it's relevant
                if query_tokens and level2_tokens:
                    overlap = query_tokens.intersection(level2_tokens)
                    if len(overlap) / len(query_tokens) >= 0.4:
                        return True
            
            # Also check if query matches any specialization
            if all_specs and query_normalized:
                for spec in all_specs:
                    if spec.lower() in query_normalized or query_normalized in spec.lower():
                        return True
        
        # If no Level 1 filter was inferred and no strong match, allow all (too general to filter)
        if not level1_filter:
            return True
        
        return False
    
    async def _execute_suggestion_response(
        self,
        context: Dict,
        intent,
        plan
    ) -> str:
        """
        Generate suggestion response when data not available.
        Uses navigation map suggestions to help user pivot.
        """
        from app.rag import call_llm_async
        
        company = intent.company or "Unknown Company"
        specialization = intent.specialization or "Unknown Specialization"
        suggestions = intent.suggestions or {}
        
        # Build suggestions text
        suggestions_text = ""
        
        if suggestions.get('available_specializations'):
            specs_list = suggestions['available_specializations']
            suggestions_text += f"\n**Available Specializations for {company}:**\n"
            suggestions_text += "\n".join(f"- {spec}" for spec in specs_list)
        
        if suggestions.get('similar_companies_with_spec'):
            companies_list = suggestions['similar_companies_with_spec'][:5]
            suggestions_text += f"\n\n**Companies with {specialization} roles:**\n"
            suggestions_text += "\n".join(f"- {comp}" for comp in companies_list)
        
        # Generate response with suggestions
        suggestion_prompt = f"""
You are a career advisor helping a student find relevant job data.

SITUATION:
The student asked about: {company} - {specialization}

PROBLEM:
We don't have any {specialization} role data for {company} in our database.

SUGGESTIONS:
{suggestions_text if suggestions_text else "No alternative suggestions available."}

YOUR TASK:
1. Politely explain we don't have data for their exact request
2. Present the available alternatives clearly
3. Ask if they'd like details on any of the alternatives
4. Maintain a helpful, encouraging tone

Keep it concise (3-4 sentences max).
"""
        
        response = await call_llm_async(suggestion_prompt, temperature=0.3)
        return response
    
    async def _execute_synthesis(
        self,
        context: Dict,
        retrieval_results: Dict,
        synthesis_mode: str,
        plan,
        quality_report
    ) -> str:
        """Execute synthesis with tone + template."""
        from app.rag import synthesize_answer
        
        # 🎯 NEW: Handle SQL results directly for count queries
        if 'sql' in retrieval_results:
            return await self._synthesize_sql_result(
                context=context,
                sql_result=retrieval_results['sql'],
                synthesis_mode=synthesis_mode
            )

        # NEW: Handle vector aggregate count result - deterministic synthesis (no LLM)
        if 'vector_aggregate' in retrieval_results and synthesis_mode == 'direct_count':
            agg = retrieval_results['vector_aggregate']
            topic = getattr(context.get('intent_object') or {}, 'topic_or_keyword', None) or context.get('topic_or_keyword')
            topic_display = topic or context.get('specialization') or 'the requested topic'
            count = int(agg.get('count', 0) or 0)
            companies = list(agg.get('companies', []) or [])

            # Deterministic formatted response
            lines = []
            lines.append(f"## Companies for {topic_display} — Count: **{count}**")
            lines.append("")
            lines.append("### What this means")
            lines.append("- Count is derived from semantic vector search across JDs + company deduplication")
            lines.append("- This is an approximate signal (not SQL-validated against a structured table)")
            lines.append("")

            # List companies sensibly
            if companies:
                max_list = 30
                shown = companies[:max_list]
                remaining = len(companies) - len(shown)
                lines.append("### Companies identified")
                for c in shown:
                    lines.append(f"- **{c}**")
                if remaining > 0:
                    lines.append(f"- …and **{remaining}** more")
                lines.append("")

            # Provenance footer
            lines.append("---")
            lines.append("Data provenance: Vector search over job description corpus → normalized by company. Use SQL route for exact counts.")

            return "\n".join(lines)
        
        # Combine all snippets for vector results
        all_snippets = []
        source_counts = {}
        
        for source_type, result in retrieval_results.items():
            for snippet in result.snippets:
                snippet['_source_type'] = source_type
                all_snippets.append(snippet)
            source_counts[source_type] = result.count
        
        # Build synthesis instructions
        company = context.get('company', 'Unknown')
        
        synthesis_instructions = self._build_synthesis_instructions(
            company=company,
            synthesis_mode=synthesis_mode,
            plan=plan,
            quality_report=quality_report,
            source_counts=source_counts
        )
        
        # Synthesize
        response = synthesize_answer(
            question=context.get('resolved_query', context['original_query']),
            snippets=all_snippets,
            filters={},
            context={'synthesis_instructions': synthesis_instructions, **context}
        )
        
        # Add source footer
        if source_counts:
            response = self._add_source_footer(response, source_counts)
        
        return response
    
    async def _synthesize_sql_result(
        self,
        context: Dict,
        sql_result: Dict,
        synthesis_mode: str
    ) -> str:
        """Synthesize response from SQL query results."""
        specialization = sql_result.get('specialization', 'Unknown')
        result_data = sql_result.get('result', {})
        
        # Extract count and companies from SQL result
        if isinstance(result_data, list) and len(result_data) > 0:
            if isinstance(result_data[0], tuple):
                count = result_data[0][0]
                # Get company list if available
                companies = []
                if len(result_data[0]) > 1:
                    companies_str = result_data[0][1]
                    companies = companies_str.split(',') if companies_str else []
            else:
                count = result_data[0]
                companies = []
        elif isinstance(result_data, dict):
            count = result_data.get('count', 0)
            companies = result_data.get('companies', [])
        else:
            count = result_data if isinstance(result_data, int) else 0
            companies = []
        
        # Format response
        response = f"""## {specialization} Roles: Company Count

Based on our **structured placement database**, I can confirm that **{count} companies** recruited for {specialization} roles.
"""
        
        if companies and len(companies) <= 20:
            response += f"""
### Companies that recruited for {specialization}:

"""
            for i, company in enumerate(companies, 1):
                response += f"{i}. **{company.strip()}**\n"
        
        response += f"""
---
> **Data Source**: Structured SQLite Database (100% accurate)
> **Query**: `{sql_result.get('query', 'SQL count query')[:100]}...`
"""
        
        return response
    
    def _build_synthesis_instructions(
        self,
        company: str,
        synthesis_mode: str,
        plan,
        quality_report,
        source_counts: Dict
    ) -> str:
        """Build synthesis instructions based on mode and data quality."""
        
        # Base instruction (preserve tone)
        company_display = company.upper() if company else "ALL COMPANIES"
        instructions = f"""
TARGET COMPANY: **{company_display}**
RESPONSE MODE: {synthesis_mode.replace('_', ' ').title()}

SOURCES AVAILABLE:
{self._format_sources(source_counts)}

CRITICAL RULES:
1. PRIMARY FOCUS: {company if company else "ALL COMPANIES"}
2. CROSS-COMPANY INSIGHTS: You may receive chunks from similar companies for comparison/context
   - Each chunk has "company" metadata - use this to attribute insights correctly
   - When referencing other companies, explicitly mention: "Similar to [Company X]..."
   - Use cross-company insights to provide strategic advice (e.g., "Companies like X prioritize...")
3. Cite sources: "According to {company}'s JD..." / "Interview data shows..."
4. Use Linus/Robert Greene/Aristotelian tone (direct, strategic, logical)
5. Format with white bold headings, white bold emphasis

IMPORTANT: The retrieval system uses semantic search to find relevant context across companies.
This allows strategic comparisons (e.g., "HONASA focuses on X, while similar companies prioritize Y").
Always check chunk metadata to attribute insights to the correct company.
"""
        
        # Add data gap acknowledgments
        if plan.expected_gaps:
            instructions += f"""
DATA LIMITATIONS:
{chr(10).join(f"- {gap}" for gap in plan.expected_gaps[:3])}

→ Acknowledge these gaps explicitly in response
→ Focus on available data (JD analysis if interview data missing)
"""
        
        # Add synthesis adaptations
        if plan.synthesis_adaptations:
            instructions += f"""
SYNTHESIS ADAPTATIONS:
{chr(10).join(f"- {adapt.replace('_', ' ').title()}" for adapt in plan.synthesis_adaptations[:3])}
"""
        
        # Add confidence context
        if quality_report:
            instructions += f"""
DATA CONFIDENCE: {quality_report.confidence_score:.0%}
{f"⚠️  Low confidence - acknowledge data limitations" if quality_report.confidence_score < 0.5 else ""}
"""
        
        return instructions
    
    def _format_sources(self, source_counts: Dict) -> str:
        """Format source counts."""
        lines = []
        for source, count in source_counts.items():
            icon = {'jd': '📄', 'interview': '💬', 'alumni': '🎓', 'gd_topic': '👥'}.get(source, '📌')
            lines.append(f"{icon} {count} {source.replace('_', ' ').title()} documents")
        return "\n".join(lines) if lines else "No sources available"
    
    def _add_source_footer(self, response: str, source_counts: Dict) -> str:
        """Add source attribution footer."""
        footer = "\n\n---\n**Intelligence Sources:**\n"
        
        for source, count in source_counts.items():
            if count > 0:
                icon = {'jd': '📄', 'interview': '💬', 'alumni': '🎓', 'gd_topic': '👥'}.get(source, '📌')
                footer += f"{icon} {count} {source.replace('_', ' ').title()} documents\n"
        
        return response + footer


# Global instance
agent_orchestrator = AgentOrchestrator()
