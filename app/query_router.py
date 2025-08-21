"""
Query Router Module - Intelligent query classification and routing
Routes queries to SQL (structured), RAG (unstructured), or hybrid approaches
"""

import re
import requests
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import logging

class QueryType(Enum):
    """Types of queries the system can handle"""
    STRUCTURED = "structured"      # Counts, statistics, comparisons
    UNSTRUCTURED = "unstructured"  # Skills, culture, descriptions
    HYBRID = "hybrid"              # Combines both approaches
    MULTI_HOP = "multi_hop"        # Complex multi-step queries

class QueryRouter:
    """Intelligent query router for placement queries"""
    
    def __init__(self):
        # Patterns for query classification
        self.structured_patterns = [
            r"how many companies",
            r"count.*companies",
            r"total.*companies",
            r"median salary",
            r"average salary",
            r"salary range",
            r"highest salary",
            r"lowest salary",
            r"number of roles",
            r"total roles",
            r"placement statistics",
            r"placement data",
            r"salary statistics",
            r"company count",
            r"role count",
            r"which companies.*(?:marketing|finance|hr|operations|strategy|it|analytics)",
            r"companies.*(?:marketing|finance|hr|operations|strategy|it|analytics)",
            r"(?:marketing|finance|hr|operations|strategy|it|analytics).*companies"
        ]
        
        self.unstructured_patterns = [
            r"what skills",
            r"key skills",
            r"required skills",
            r"skills needed",
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
        """Classify the query type and extract relevant parameters"""
        question_lower = question.lower()
        
        # Check for multi-hop queries first (most complex)
        if self._matches_patterns(question_lower, self.multi_hop_patterns):
            return QueryType.MULTI_HOP, self._extract_multi_hop_params(question_lower)
        
        # Check for hybrid queries
        if self._matches_patterns(question_lower, self.hybrid_patterns):
            return QueryType.HYBRID, self._extract_hybrid_params(question_lower)
        
        # Check for structured queries
        if self._matches_patterns(question_lower, self.structured_patterns):
            return QueryType.STRUCTURED, self._extract_structured_params(question_lower)
        
        # Check for unstructured queries
        if self._matches_patterns(question_lower, self.unstructured_patterns):
            return QueryType.UNSTRUCTURED, self._extract_unstructured_params(question_lower)
        
        # Default to unstructured for unknown queries
        return QueryType.UNSTRUCTURED, {"query": question}
    
    def _llm_classify_query(self, question: str) -> Tuple[QueryType, Dict[str, Any]]:
        """LLM-based query classification for edge cases"""
        try:
            from .config import get_settings
            settings = get_settings()
            
            if not settings.OPENROUTER_API_KEY:
                print("⚠️ No OpenRouter API key, defaulting to HYBRID")
                return QueryType.HYBRID, {"query": question, "fallback": "no_api_key"}
            
            # LLM classification prompt
            classification_prompt = f"""You are a query router for a placement database. 
Classify the user's query into one of:
- SQL (counts, statistics, totals, averages, medians, comparisons across companies or years)
- RAG (open-ended, descriptive, unstructured answers requiring JD details)
- HYBRID (needs both SQL stats + JD text details).

Respond ONLY with one label: SQL, RAG, or HYBRID.

User Query: "{question}"

Classification:"""
            
            payload = {
                "model": settings.OPENROUTER_MODEL or "moonshotai/kimi-k2:free",
                "messages": [
                    {"role": "system", "content": "You are a precise query classifier. Respond with ONLY one word: SQL, RAG, or HYBRID."},
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
                
                print(f"🤖 LLM Classification: {content}")
                
                # Map LLM response to QueryType
                if "SQL" in content:
                    return QueryType.STRUCTURED, self._extract_structured_params(question)
                elif "RAG" in content:
                    return QueryType.UNSTRUCTURED, self._extract_unstructured_params(question)
                elif "HYBRID" in content:
                    return QueryType.HYBRID, self._extract_hybrid_params(question)
                else:
                    print(f"⚠️ Unexpected LLM response: {content}, defaulting to HYBRID")
                    return QueryType.HYBRID, {"query": question, "fallback": "unexpected_llm_response"}
            
            else:
                print(f"❌ LLM API error: {response.status_code}, defaulting to HYBRID")
                return QueryType.HYBRID, {"query": question, "fallback": "llm_api_error"}
                
        except Exception as e:
            print(f"❌ LLM classification failed: {e}, defaulting to HYBRID")
            return QueryType.HYBRID, {"query": question, "fallback": "llm_exception"}
    
    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any of the patterns"""
        return any(re.search(pattern, text) for pattern in patterns)
    
    def _extract_structured_params(self, question: str) -> Dict[str, Any]:
        """Extract parameters for structured queries"""
        params = {"query": question}
        
        # Extract year information
        year_match = re.search(r"(\d{4})", question)
        if year_match:
            params["year"] = int(year_match.group(1))
        
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
                "description": "Use SQL database for fast, accurate statistics"
            }
        
        elif query_type == QueryType.UNSTRUCTURED:
            return {
                "primary": "rag",
                "fallback": "sql",
                "description": "Use RAG for detailed, contextual answers"
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
        
        return {"primary": "rag", "description": "Default to RAG"}
    
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
