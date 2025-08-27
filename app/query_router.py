"""
Query Router Module - Intelligent query classification and routing
Routes queries to SQL (structured), RAG (unstructured), or hybrid approaches
"""

import re
import json
import requests
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import logging
from .database import PlacementDatabase

class QueryType(Enum):
    """Types of queries the system can handle"""
    STRUCTURED = "structured"      # Counts, statistics, comparisons
    UNSTRUCTURED = "unstructured"  # Skills, culture, descriptions
    HYBRID = "hybrid"              # Combines both approaches
    MULTI_HOP = "multi_hop"        # Complex multi-step queries

class QueryRouter:
    """Intelligent query router for placement queries with LLM-powered classification"""
    
    def __init__(self):
        # Patterns for query classification
        # STRICT: Route to STRUCTURED only when user asks for counts/numbers/salaries
        self.structured_patterns = [
            r"\bhow many\b.*\b(companies|roles|offers)\b",
            r"\bcount\b.*\b(companies|roles|offers)\b",
            r"\btotal\b.*\b(companies|roles|offers)\b",
            r"\bnumber of\b.*\b(companies|roles|offers)\b",
            r"\bmedian salary\b",
            r"\baverage\b.*\bsalary\b|\bavg\b.*\bsalary\b",
            r"\bsalary range\b|\bmin(?:imum)? salary\b|\bmax(?:imum)? salary\b",
            r"\bplacement statistics\b|\bsalary statistics\b|\bplacement data\b",
        ]
        
        self.unstructured_patterns = [
            # Broad skills coverage
            r"\bwhat\s+.*skills\b",
            r"\bwhich\s+.*skills\b",
            r"\brelevant\s+.*skills\b",
            r"\bskills\s+to\s+(learn|hone|focus|prepare)\b",
            r"\bskills?\b",  # catch-all; safe because structured is stricter
            r"key skills", 
            r"required skills",
            r"skills needed",
            r"most.*skills",
            r"sought.*skills",
            r"popular.*skills",
            r"in.*demand.*skills", 
            r"top.*skills",
            r"important.*skills",
            r"company culture",
            r"work environment",
            r"job description",
            r"role description",
            r"responsibilities",
            r"requirements",
            r"what does.*do",
            r"how to prepare",
            r"career advice",
            r"job requirements",
            r"role requirements",
            r"full jd",
            r"complete jd",
            r"entire jd",
            r"full job description",
            r"complete job description",
            r"entire job description",
            r"show me.*jd",
            r"give.*jd",
            r"what is.*jd"
        ]
        
        self.hybrid_patterns = [
            r"compare.*salary",
            r"compare.*skills",
            r"compare.*companies",
            r"vs.*salary",
            r"vs.*skills",
            r"salary.*skills",
            r"skills.*salary",
            r"company.*salary.*skills"
        ]
        
        self.multi_hop_patterns = [
            r"among.*salary.*skills",
            r"companies.*salary.*what skills",
            r"high paying.*skills",
            r"top paying.*requirements",
            r"best companies.*skills"
        ]
    
    def classify_query(self, question: str) -> Tuple[QueryType, Dict[str, Any]]:
        """Classify the query type using LLM intelligence with fallback to pattern matching"""
        try:
            # Try LLM classification first
            llm_result = self._llm_classify_query(question)
            if llm_result:
                return llm_result
        except Exception as e:
            logging.warning(f"LLM classification failed, falling back to patterns: {e}")
        
        # Fallback to pattern-based classification with strict guards
        return self._pattern_based_classification(question)
    
    def _llm_classify_query(self, question: str) -> Optional[Tuple[QueryType, Dict[str, Any]]]:
        """LLM-based query classification with strict guardrails"""
        try:
            from .config import get_settings
            settings = get_settings()
            
            if not settings.OPENROUTER_API_KEY:
                return None
            
            # Structured prompt with strict constraints
            classification_prompt = f"""You are a query router for a placement database. Your task is to classify queries into one of these categories:

STRUCTURED: Queries that need numerical data, counts, statistics, comparisons, or filtered lists. Examples:
- "How many companies came for marketing roles?"
- "What's the average salary for finance positions?"
- "Which companies recruited in 2023?"
- "Count of roles by specialization"

UNSTRUCTURED: Queries that need detailed descriptions, skills analysis, or contextual information. Examples:
- "What skills are required for this role?"
- "Tell me about the company culture"
- "Show me the complete job description"
- "What are the responsibilities?"

HYBRID: Queries that need both structured data AND detailed analysis. Examples:
- "Compare salaries and skills across companies"
- "Which companies pay well and what skills do they need?"

MULTI_HOP: Complex queries requiring multiple steps. Examples:
- "Among high-paying companies, what skills are most valued?"

IMPORTANT RULES:
1. If the query asks for counts, numbers, or filtered lists → STRUCTURED
2. If the query asks for descriptions, skills, or detailed info → UNSTRUCTURED  
3. If the query needs both → HYBRID
4. If the query is complex with multiple conditions → MULTI_HOP
5. When in doubt, choose UNSTRUCTURED for safety

User Query: "{question}"

Respond with ONLY one word: STRUCTURED, UNSTRUCTURED, HYBRID, or MULTI_HOP"""
            
            payload = {
                "model": settings.OPENROUTER_MODEL or "moonshotai/kimi-k2:free",
                "messages": [
                    {"role": "system", "content": "You are a precise query classifier. Respond with ONLY one word: STRUCTURED, UNSTRUCTURED, HYBRID, or MULTI_HOP."},
                    {"role": "user", "content": classification_prompt}
                ],
                "temperature": 0.0,
                "max_tokens": 10,
            }
            
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=10,
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip().upper()
                
                logging.info(f"🤖 LLM Classification: {content}")
                
                # Map LLM response to QueryType with strict validation
                if "STRUCTURED" in content:
                    qtype = QueryType.STRUCTURED
                    override = self._enforce_post_llm_guards(question, qtype)
                    qtype = override or qtype
                    extractor = {
                        QueryType.STRUCTURED: self._extract_structured_params,
                        QueryType.UNSTRUCTURED: self._extract_unstructured_params,
                    }[qtype]
                    return qtype, extractor(question)
                elif "UNSTRUCTURED" in content:
                    qtype = QueryType.UNSTRUCTURED
                    override = self._enforce_post_llm_guards(question, qtype)
                    qtype = override or qtype
                    extractor = {
                        QueryType.STRUCTURED: self._extract_structured_params,
                        QueryType.UNSTRUCTURED: self._extract_unstructured_params,
                    }[qtype]
                    return qtype, extractor(question)
                elif "HYBRID" in content:
                    return QueryType.HYBRID, self._extract_hybrid_params(question)
                elif "MULTI_HOP" in content:
                    return QueryType.MULTI_HOP, self._extract_multi_hop_params(question)
                else:
                    logging.warning(f"Unexpected LLM response: {content}, defaulting to UNSTRUCTURED")
                    return QueryType.UNSTRUCTURED, {"query": question, "fallback": "unexpected_llm_response"}
            
            else:
                logging.warning(f"LLM API error: {response.status_code}, falling back to patterns")
                return None
                
        except Exception as e:
            logging.error(f"LLM classification failed: {e}")
            return None
    
    def _pattern_based_classification(self, question: str) -> Tuple[QueryType, Dict[str, Any]]:
        """Fallback pattern-based classification when LLM fails"""
        question_lower = question.lower()

        # Quick guard: explicit numeric/count queries should always be STRUCTURED
        if re.search(r"\b(how many|count|total|number of)\b", question_lower) and \
           re.search(r"\b(companies|roles|offers|salary|salaries)\b", question_lower):
            return QueryType.STRUCTURED, self._extract_structured_params(question_lower)

        # Check for multi-hop queries first (most complex)
        if self._matches_patterns(question_lower, self.multi_hop_patterns):
            return QueryType.MULTI_HOP, self._extract_multi_hop_params(question_lower)

        # Check for hybrid queries
        if self._matches_patterns(question_lower, self.hybrid_patterns):
            return QueryType.HYBRID, self._extract_hybrid_params(question_lower)

        # Prefer UNSTRUCTURED first to avoid false positives
        if self._matches_patterns(question_lower, self.unstructured_patterns):
            return QueryType.UNSTRUCTURED, self._extract_unstructured_params(question_lower)

        # Structured only if strict patterns match
        if self._matches_patterns(question_lower, self.structured_patterns):
            return QueryType.STRUCTURED, self._extract_structured_params(question_lower)

        # Check for unstructured queries
        if self._matches_patterns(question_lower, self.unstructured_patterns):
            return QueryType.UNSTRUCTURED, self._extract_unstructured_params(question_lower)

        # Default to unstructured (safety)
        return QueryType.UNSTRUCTURED, {"query": question, "fallback": "pattern_default"}
    
    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any of the patterns"""
        return any(re.search(pattern, text) for pattern in patterns)

    def _enforce_post_llm_guards(self, question: str, llm_type: QueryType) -> Optional[QueryType]:
        """If LLM says STRUCTURED but the question clearly asks for skills/descriptions,
        override to UNSTRUCTURED. If LLM says UNSTRUCTURED but query clearly demands counts, override to STRUCTURED."""
        q = question.lower()
        if llm_type == QueryType.STRUCTURED:
            # If query mentions skills/description/culture without numeric intent → UNSTRUCTURED
            if self._matches_patterns(q, self.unstructured_patterns) and not self._matches_patterns(q, self.structured_patterns):
                return QueryType.UNSTRUCTURED
        if llm_type == QueryType.UNSTRUCTURED:
            # If query clearly asks for counts/salaries → STRUCTURED
            if self._matches_patterns(q, self.structured_patterns):
                return QueryType.STRUCTURED
        return None
    
    def _extract_structured_params(self, question: str) -> Dict[str, Any]:
        """Extract parameters for structured queries"""
        params = {"query": question}
        
        # Extract year information
        year_match = re.search(r"(\d{4})", question)
        if year_match:
            params["year"] = int(year_match.group(1))
        elif "last year" in question.lower():
            params["year"] = "2023-2024"
        elif "this year" in question.lower():
            params["year"] = "2024-2025"
        
        # Extract MBA specialization
        mba_specializations = [
            "marketing", "finance", "hr", "operations", "strategy", "it", "analytics",
            "human resources", "supply chain", "consulting", "digital transformation"
        ]
        
        for spec in mba_specializations:
            if spec in question.lower():
                params["specialization"] = spec.title()
                break
        
        # Extract salary-related parameters
        if "salary" in question:
            if "median" in question:
                params["metric"] = "median"
            elif "average" in question or "avg" in question:
                params["metric"] = "average"
            elif "range" in question:
                params["metric"] = "range"
            elif "highest" in question or "max" in question:
                params["metric"] = "max"
            elif "lowest" in question or "min" in question:
                params["metric"] = "min"
        
        # Extract count-related parameters
        if "count" in question or "how many" in question:
            if "companies" in question:
                params["entity"] = "companies"
            elif "roles" in question:
                params["entity"] = "roles"
            elif "offers" in question:
                params["entity"] = "offers"
        
        return params

    def llm_extract_structured_intent(self, question: str) -> Dict[str, Any]:
        """Use the LLM to extract normalized structured intent safely (JSON-only).
        Returns a dict with possible keys: entity, specialization, year, metric.
        Falls back to pattern extraction if LLM unavailable or invalid.
        """
        try:
            from .config import get_settings
            settings = get_settings()
            if not settings.OPENROUTER_API_KEY:
                return self._extract_structured_params(question)

            prompt = (
                "Extract intent for a SQL lookup over a placement database. "
                "Return STRICT JSON only, no prose, matching this schema: {\n"
                "  \"entity\": one of [\"companies\", \"roles\", \"offers\", \"salaries\", \"stats\"] or null,\n"
                "  \"specialization\": one of [\"Marketing\", \"Finance\", \"HR\", \"Operations\", \"Strategy\", \"IT\", \"Analytics\"] or null,\n"
                "  \"year\": string like \"2024-2025\" or null,\n"
                "  \"metric\": one of [\"count\", \"average\", \"median\", \"min\", \"max\"] or null\n"
                "}\n"
                "Normalize casing and synonyms (e.g., hr -> HR, biz analytics -> Analytics).\n"
                f"User query: {question}\n"
                "JSON:"
            )

            payload = {
                "model": settings.OPENROUTER_MODEL or "moonshotai/kimi-k2:free",
                "messages": [
                    {"role": "system", "content": "You output STRICT JSON only. No explanations."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.0,
                "max_tokens": 120,
            }
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            }
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=12,
            )
            if resp.status_code != 200:
                logging.warning(f"LLM intent extraction failed: {resp.status_code}")
                return self._extract_structured_params(question)

            content = resp.json()["choices"][0]["message"]["content"].strip()
            try:
                data = json.loads(content)
            except Exception:
                # Try to extract JSON substring if model wrapped it
                start = content.find('{')
                end = content.rfind('}')
                if start != -1 and end != -1:
                    data = json.loads(content[start:end+1])
                else:
                    return self._extract_structured_params(question)

            # Validate and normalize
            valid_entities = {"companies", "roles", "offers", "salaries", "stats"}
            valid_specs = {"Marketing", "Finance", "HR", "Operations", "Strategy", "IT", "Analytics"}
            valid_metrics = {"count", "average", "median", "min", "max"}

            out: Dict[str, Any] = {"query": question}
            ent = (data.get("entity") or "").lower()
            if ent in valid_entities:
                out["entity"] = ent
            spec = data.get("specialization")
            if spec in valid_specs:
                out["specialization"] = spec
            yr = data.get("year")
            if isinstance(yr, str) and re.match(r"^\d{4}-\d{4}$", yr):
                out["year"] = yr
            met = (data.get("metric") or "").lower()
            if met in valid_metrics:
                out["metric"] = met

            # If nothing validated, fallback
            if len(out.keys()) == 1:
                return self._extract_structured_params(question)
            return out
        except Exception as e:
            logging.warning(f"LLM structured intent exception: {e}")
            return self._extract_structured_params(question)
    
    def _extract_unstructured_params(self, question: str) -> Dict[str, Any]:
        """Extract parameters for unstructured queries"""
        params = {"query": question}
        
        # Extract skill-related parameters
        if "skill" in question:
            params["focus"] = "skills"
            # Extract specific skill mentions
            skill_match = re.search(r"(\w+)\s+skills?", question)
            if skill_match:
                params["skill_type"] = skill_match.group(1)
        
        # Extract role-related parameters
        if "role" in question:
            params["focus"] = "role_description"
        
        # Extract company-related parameters
        if "culture" in question or "environment" in question:
            params["focus"] = "company_culture"
        
        return params
    
    def _extract_hybrid_params(self, question: str) -> Dict[str, Any]:
        """Extract parameters for hybrid queries"""
        params = {"query": question}
        
        # Extract comparison entities
        if "compare" in question:
            # Look for company names or role types
            companies = re.findall(r"(\w+(?:\s+\w+)*)", question)
            params["compare_entities"] = [c for c in companies if len(c.split()) <= 3]
        
        # Extract comparison aspects
        if "salary" in question:
            params["compare_salary"] = True
        if "skill" in question:
            params["compare_skills"] = True
        
        return params
    
    def _extract_multi_hop_params(self, question: str) -> Dict[str, Any]:
        """Extract parameters for multi-hop queries"""
        params = {"query": question}
        
        # Extract filter conditions
        if "salary" in question:
            salary_match = re.search(r"salary\s*(?:>|>=|less than|more than)\s*(\d+(?:\.\d+)?)", question)
            if salary_match:
                params["salary_threshold"] = float(salary_match.group(1))
                params["salary_operator"] = ">" if ">" in question else "<"
        
        # Extract target information
        if "skills" in question:
            params["target_info"] = "skills"
        elif "requirements" in question:
            params["target_info"] = "requirements"
        
        return params
    
    def get_routing_strategy(self, query_type: QueryType, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get the routing strategy for the query type"""
        if query_type == QueryType.STRUCTURED:
            return {
                "primary": "sql",
                "fallback": "rag",
                "description": "Use SQL database for fast, accurate statistics and filtered data"
            }
        
        elif query_type == QueryType.UNSTRUCTURED:
            return {
                "primary": "rag",
                "fallback": "sql",
                "description": "Use RAG for detailed, contextual answers from job descriptions"
            }
        
        elif query_type == QueryType.HYBRID:
            return {
                "primary": "hybrid",
                "components": ["sql", "rag"],
                "description": "Combine SQL for structured data and RAG for context"
            }
        
        elif query_type == QueryType.MULTI_HOP:
            return {
                "primary": "multi_step",
                "steps": ["sql_filter", "rag_analysis"],
                "description": "Multi-step approach: filter then analyze"
            }
        
        return {"primary": "rag", "description": "Default to RAG for safety"}
    
    def format_query_for_llm(self, query_type: QueryType, params: Dict[str, Any]) -> str:
        """Format the query with context for LLM processing"""
        if query_type == QueryType.STRUCTURED:
            return f"""
You are analyzing a STRUCTURED QUERY about placement data.
Query: {params.get('query', '')}
Focus on providing precise statistics, counts, and numerical data.
Use the structured database information for accurate results.
"""
        
        elif query_type == QueryType.UNSTRUCTURED:
            return f"""
You are analyzing an UNSTRUCTURED QUERY about job descriptions and company information.
Query: {params.get('query', '')}
Focus on providing detailed insights, skills analysis, and contextual information.
Use the PDF content and RAG results for comprehensive answers.
"""
        
        elif query_type == QueryType.HYBRID:
            return f"""
You are analyzing a HYBRID QUERY that requires both structured and unstructured data.
Query: {params.get('query', '')}
Combine numerical data (salaries, counts) with detailed analysis (skills, culture).
Provide both quantitative and qualitative insights.
"""
        
        elif query_type == QueryType.MULTI_HOP:
            return f"""
You are analyzing a MULTI-HOP QUERY that requires filtering then analysis.
Query: {params.get('query', '')}
Step 1: Apply filters (salary, company, etc.)
Step 2: Analyze the filtered results for detailed insights.
Provide both the filtered dataset and comprehensive analysis.
"""
        
        return f"Query: {params.get('query', '')}"

    def _handle_hybrid_query(self, question: str, params: Dict[str, Any], db: PlacementDatabase, snippets: List[Dict[str, Any]]) -> str:
        """Handle hybrid queries combining SQL and RAG"""
        try:
            # Step 1: Get structured data using SQL
            from app.rag import answer_from_text2sql
            structured_answer = answer_from_text2sql(question)
            
            # Step 2: Get RAG insights for additional context
            from app.rag import synthesize_answer
            rag_answer = synthesize_answer(question, snippets, {})
            
            # Step 3: Combine and format the response
            if structured_answer and rag_answer:
                combined_answer = f"""
**Data Analysis & Statistics:**
{structured_answer}

**Additional Context & Insights:**
{rag_answer}
"""
                return combined_answer
            elif structured_answer:
                return f"{structured_answer}\n\n*Note: Additional context could not be retrieved.*"
            elif rag_answer:
                return f"{rag_answer}\n\n*Note: Structured data could not be retrieved.*"
            else:
                return "I couldn't retrieve either structured data or contextual information for this query."
            
        except Exception as e:
            logging.error(f"Hybrid query failed: {e}")
            return f"Error processing hybrid query: {e}"

    def _handle_multi_hop_query(self, question: str, params: Dict[str, Any], db: PlacementDatabase, snippets: List[Dict[str, Any]]) -> str:
        """Handle multi-hop queries requiring sequential reasoning"""
        try:
            # Step 1: Execute first query (usually structured filtering)
            from app.rag import answer_from_text2sql
            first_results = answer_from_text2sql(question)
            
            if not first_results:
                return "I couldn't process the first step of this multi-hop query."
            
            # Step 2: Use results to constrain second query (RAG analysis)
            # Extract key information from first results for filtering
            filtered_params = self._extract_filtered_params(first_results, params)
            
            # Step 3: Execute second query with filtered context
            from app.rag import synthesize_answer
            second_results = synthesize_answer(question, snippets, filtered_params)
            
            # Step 4: Combine results
            if second_results:
                return f"""
**Step 1 - Data Filtering & Analysis:**
{first_results}

**Step 2 - Detailed Insights (Based on Filtered Results):**
{second_results}
"""
            else:
                return f"""
**Data Analysis:**
{first_results}

*Note: Additional contextual analysis could not be retrieved.*
"""
            
        except Exception as e:
            logging.error(f"Multi-hop query failed: {e}")
            return f"Error processing multi-hop query: {e}"

    def _handle_structured_query(self, question: str, params: Dict[str, Any], db: PlacementDatabase, snippets: List[Dict[str, Any]]) -> str:
        """Handle structured queries using SQL database"""
        try:
            from app.rag import answer_from_text2sql
            return answer_from_text2sql(question) or "No structured data found for this query."
        except Exception as e:
            logging.error(f"Structured query failed: {e}")
            return f"Error processing structured query: {e}"

    def _extract_filtered_params(self, first_results: str, original_params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters from first query results to constrain second query"""
        filtered_params = original_params.copy()
        
        # Extract company names if mentioned in results
        import re
        company_matches = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', first_results)
        if company_matches:
            filtered_params["company_filter"] = company_matches[0]  # Use first company found
        
        # Extract salary information if mentioned
        salary_match = re.search(r'(\d+(?:\.\d+)?)\s*LPA', first_results)
        if salary_match:
            filtered_params["salary_threshold"] = float(salary_match.group(1))
        
        # Extract specialization if mentioned
        specializations = ["Marketing", "Finance", "HR", "Operations", "Strategy", "IT", "Analytics"]
        for spec in specializations:
            if spec in first_results:
                filtered_params["specialization_filter"] = spec
                break
        
        return filtered_params

    def route_query(self, question: str) -> str:
        """Main method to route and execute queries"""
        try:
            # Step 1: Classify the query
            query_type, params = self.classify_query(question)
            
            # Step 2: Get routing strategy
            strategy = self.get_routing_strategy(query_type, params)
            
            # Step 3: Execute based on query type
            if query_type == QueryType.STRUCTURED:
                return self._handle_structured_query(question, params, None, [])
            
            elif query_type == QueryType.UNSTRUCTURED:
                from app.rag import retrieve_snippets, synthesize_answer
                snippets = retrieve_snippets(question, top_k=5, filters={})
                return synthesize_answer(question, snippets, {}) or "No relevant information found."
            
            elif query_type == QueryType.HYBRID:
                from app.rag import retrieve_snippets
                snippets = retrieve_snippets(question, top_k=5, filters={})
                return self._handle_hybrid_query(question, params, None, snippets)
            
            elif query_type == QueryType.MULTI_HOP:
                from app.rag import retrieve_snippets
                snippets = retrieve_snippets(question, top_k=5, filters={})
                return self._handle_multi_hop_query(question, params, None, snippets)
            
            else:
                return "I couldn't determine how to process this query."
                
        except Exception as e:
            logging.error(f"Query routing failed: {e}")
            return f"Error processing query: {e}"
