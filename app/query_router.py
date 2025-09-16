import os
import requests

# Using a placeholder for a more robust LLM client as per the plan.
# In a real application, this would be your LLMClient class.

# --- PROMPTS ---
CLASSIFIER_PROMPT_TEMPLATE = """
You are a query router for a placement database. Your task is to classify queries into one of these categories:

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
1. If the query asks for counts, numbers, or filtered lists -> STRUCTURED
2. If the query asks for descriptions, skills, or detailed info -> UNSTRUCTURED
3. If the query needs both -> HYBRID
4. If the query is complex with multiple conditions -> MULTI_HOP
5. When in doubt, choose UNSTRUCTURED for safety

User Query: "{question}"

Respond with ONLY one word: STRUCTURED, UNSTRUCTURED, HYBRID, or MULTI_HOP
"""

PRECISE_CLASSIFIER_PROMPT = "You are a precise query classifier. Respond with ONLY one word: STRUCTURED, UNSTRUCTURED, HYBRID, or MULTI_HOP."

def classify(question: str) -> str:
    """
    Classifies the user's question into STRUCTURED, UNSTRUCTURED, HYBRID, or MULTI_HOP.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Warning: OPENROUTER_API_KEY not found. Falling back to basic classification.")
        return "UNSTRUCTURED" # Safe default

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "model": "mistralai/mistral-7b-instruct", # A fast and reliable model for classification
                "messages": [
                    {"role": "system", "content": PRECISE_CLASSIFIER_PROMPT},
                    {"role": "user", "content": CLASSIFIER_PROMPT_TEMPLATE.format(question=question)}
                ],
                "temperature": 0,
                "max_tokens": 10
            }
        )
        response.raise_for_status()
        
        classification = response.json()['choices'][0]['message']['content'].strip().upper()
        
        valid_classifications = ["STRUCTURED", "UNSTRUCTURED", "HYBRID", "MULTI_HOP"]
        if classification in valid_classifications:
            return classification
        else:
            print(f"Warning: LLM returned invalid classification '{classification}'. Defaulting to UNSTRUCTURED.")
            return "UNSTRUCTURED"
            
    except requests.exceptions.RequestException as e:
        print(f"Error in query classification API call: {e}")
        # Default to UNSTRUCTURED on error for safety
        return "UNSTRUCTURED"
    except (KeyError, IndexError) as e:
        print(f"Error parsing LLM response: {e}")
        return "UNSTRUCTURED"

def classify_query(question: str) -> str:
    """
    Main function to classify a query. This acts as the public interface for the module.
    """
    return classify(question)

if __name__ == '__main__':
    # Verification command as per the plan
    def run_verification():
        test_query = "How many companies came for marketing roles?"
        print(f"Query router sanity check:")
        print(f"python -c \"from app.query_router import classify_query; print(classify_query('{test_query}'))\"")
        
        classification = classify_query(test_query)
        print(f"Expected output: STRUCTURED")
        print(f"Actual output:   {classification}")
        
        if classification == "STRUCTURED":
            print("✅ Sanity check passed!")
        else:
            print("❌ Sanity check failed!")

    run_verification()

import re
from typing import Dict, List, Any, Optional
import sqlite3
import requests

from .config import get_settings
from .rag import retrieve_snippets, synthesize_answer
from .final_sql_tool import run_llama_index_sql_query


class QueryRouter:
    """Routes queries to SQL database or vector search based on LLM classification."""

    def __init__(self):
        self.settings = get_settings()

    def route_query(self, question: str) -> str:
        """
        Route query to appropriate backend system using LLM classification.
        """
        print(f"🔍 Processing query: '{question}'")

        # Classify the query using LLM
        classification = self._classify_query(question)
        print(f"🎯 Query Classification: {classification}")

        if classification == "STRUCTURED":
            return self._handle_structured_query(question)
        elif classification == "UNSTRUCTURED":
            return self._handle_unstructured_query(question)
        elif classification == "HYBRID":
            return self._handle_hybrid_query(question)
        elif classification == "MULTI_HOP":
            return self._handle_multi_hop_query(question)
        else:
            # Default to unstructured search
            return self._handle_unstructured_query(question)

    def _classify_query(self, question: str) -> str:
        """
        Classify query into STRUCTURED, UNSTRUCTURED, HYBRID, or MULTI_HOP using LLM.
        """
        schema_info = self._get_database_schema()

        classification_prompt = f"""
        You are a query router for a placement database. Your task is to classify queries into one of these categories:

        **Database Schema:**
        {schema_info}

        **Routing Rules:**

        1. **STRUCTURED**: Queries that need numerical data, counts, statistics, comparisons, or filtered lists.
           Examples:
           - "How many companies came for marketing roles?"
           - "What's the average salary for finance positions?"
           - "Which companies recruited in 2023?"
           - "Count of roles by specialization"
           - "List all companies in finance"

        2. **UNSTRUCTURED**: Queries that need detailed descriptions, skills analysis, or contextual information.
           Examples:
           - "What skills are required for this role?"
           - "Tell me about the company culture"
           - "Show me the complete job description"
           - "What are the responsibilities?"
           - "Explain the daily tasks for this position"

        3. **HYBRID**: Queries that need both structured data AND detailed analysis.
           Examples:
           - "Compare salaries and skills across companies"
           - "Which companies pay well and what skills do they need?"
           - "Show me companies with high salaries and their required skills"

        4. **MULTI_HOP**: Complex queries requiring multiple steps or reasoning.
           Examples:
           - "Among high-paying companies, what skills are most valued?"
           - "Find companies in Bangalore, then compare their salary ranges"
           - "Get marketing roles, then analyze the required skills"

        **CRITICAL RULES:**
        - If query asks for counts, numbers, or filtered lists → STRUCTURED
        - If query asks for descriptions, skills, or detailed info → UNSTRUCTURED
        - If query needs both structured data AND analysis → HYBRID
        - If query is complex with multiple conditions/steps → MULTI_HOP
        - When in doubt, choose UNSTRUCTURED for safety

        **Response Format:**
        Respond with ONLY one word: STRUCTURED, UNSTRUCTURED, HYBRID, or MULTI_HOP

        User Query: "{question}"
        """

        try:
            if self.settings.OPENROUTER_API_KEY:
                payload = {
                    "model": "moonshotai/kimi-k2",
                    "messages": [
                        {"role": "system", "content": "You are a precise query classifier. Respond with ONLY one word: STRUCTURED, UNSTRUCTURED, HYBRID, or MULTI_HOP."},
                        {"role": "user", "content": classification_prompt},
                    ],
                    "temperature": 0.0,
                    "max_tokens": 10,
                }

                headers = {
                    "Authorization": f"Bearer {self.settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                }

                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=10
                )

                if response.status_code == 200:
                    result = response.json()["choices"][0]["message"]["content"].strip().upper()
                    if result in ["STRUCTURED", "UNSTRUCTURED", "HYBRID", "MULTI_HOP"]:
                        return result

        except Exception as e:
            print(f"❌ LLM classification failed: {e}")

        # Fallback classification
        return self._fallback_classification(question)

    def _get_database_schema(self) -> str:
        """Get comprehensive database schema information for LLM context."""
        try:
            # Complete database schema as per system documentation
            return """
            Database Schema for JD-Copilot Placement System:

            TABLES:

            1. COMPANIES TABLE:
            - id (INTEGER PRIMARY KEY)
            - company_name (TEXT UNIQUE NOT NULL)
            - company_type (TEXT)
            - industry (TEXT)
            - location (TEXT)
            - batch_year (TEXT DEFAULT '2024-2025')
            - created_at (TIMESTAMP)

            2. ROLES TABLE:
            - id (INTEGER PRIMARY KEY)
            - company_id (INTEGER NOT NULL, FK → companies.id)
            - title (TEXT NOT NULL)
            - specialization (TEXT NOT NULL) - MBA specializations: Marketing, Finance, HR, Operations, Business Analytics, Strategy, IT
            - location (TEXT)
            - role_description (TEXT)
            - created_at (TIMESTAMP)

            3. OFFERS TABLE:
            - id (INTEGER PRIMARY KEY)
            - role_id (INTEGER NOT NULL, FK → roles.id)
            - batch_year (TEXT DEFAULT '2024-2025')
            - salary_min_lpa (REAL)
            - salary_max_lpa (REAL)
            - expected_hires (INTEGER)
            - created_at (TIMESTAMP)

            4. SKILLS TABLE:
            - id (INTEGER PRIMARY KEY)
            - role_id (INTEGER NOT NULL, FK → roles.id)
            - skill_name (TEXT NOT NULL)
            - skill_type (TEXT DEFAULT 'technical')
            - skill_priority (INTEGER DEFAULT 1)
            - created_at (TIMESTAMP)

            5. REQUIREMENTS TABLE:
            - id (INTEGER PRIMARY KEY)
            - role_id (INTEGER NOT NULL, FK → roles.id)
            - requirement_text (TEXT NOT NULL)
            - requirement_type (TEXT DEFAULT 'education')
            - requirement_priority (INTEGER DEFAULT 1)
            - created_at (TIMESTAMP)

            6. SPECIALIZATIONS TABLE:
            - id (INTEGER PRIMARY KEY)
            - name (TEXT UNIQUE NOT NULL)
            - description (TEXT)
            - created_at (TIMESTAMP)

            RELATIONSHIPS:
            - companies (1) ←→ (many) roles
            - roles (1) ←→ (many) offers
            - roles (1) ←→ (many) skills
            - roles (1) ←→ (many) requirements

            MBA SPECIALIZATIONS:
            - Marketing (Marketing and Brand Management)
            - Finance (Finance and Investment Banking)
            - HR (Human Resources and Organizational Behavior)
            - Operations (Operations and Supply Chain Management)
            - Strategy (Strategic Management and Consulting)
            - IT (Information Technology and Digital Transformation)
            - Analytics (Business Analytics and Data Science)
            """
        except Exception:
            return "Database schema information not available"

    def _handle_structured_query(self, question: str) -> str:
        """
        Handle STRUCTURED queries using SQL database.
        """
        print("🔧 Routing to structured database query")

        try:
            # Use LlamaIndex for SQL generation
            result = run_llama_index_sql_query(question)
            if result and not result.startswith("Structured query engine not available"):
                return self._format_structured_response(result, question)
            else:
                return "I couldn't find the structured data you're looking for."
        except Exception as e:
            print(f"❌ Structured query failed: {e}")
            return "I encountered an error while processing your structured query."

    def _handle_unstructured_query(self, question: str) -> str:
        """
        Handle UNSTRUCTURED queries using vector search.
        """
        print("🔍 Routing to unstructured vector search")

        try:
            snippets = retrieve_snippets(question, top_k=20, filters={})
            if snippets:
                rag_result = synthesize_answer(question, snippets, {})
                if rag_result:
                    return f"Based on available placement information:\n\n{rag_result}\n\n" \
                           "Note: This is general guidance based on our database."
        except Exception as e:
            print(f"❌ Unstructured search failed: {e}")

        return "I need to search through our knowledge base for this information."

    def _handle_hybrid_query(self, question: str) -> str:
        """
        Handle HYBRID queries requiring both structured data and analysis.
        """
        print("🔄 Routing to hybrid processing (structured + unstructured)")

        try:
            # First try structured query
            structured_result = run_llama_index_sql_query(question)
            if structured_result and not structured_result.startswith("Structured query engine not available"):
                # Then get unstructured analysis
                snippets = retrieve_snippets(question, top_k=15, filters={})
                if snippets:
                    analysis_result = synthesize_answer(question, snippets, {})
                    if analysis_result:
                        return f"**Structured Data:**\n{structured_result}\n\n" \
                               f"**Analysis & Insights:**\n{analysis_result}"
                else:
                    return self._format_structured_response(structured_result, question)
            else:
                # Fallback to unstructured
                return self._handle_unstructured_query(question)
        except Exception as e:
            print(f"❌ Hybrid query failed: {e}")
            return self._handle_unstructured_query(question)

    def _handle_multi_hop_query(self, question: str) -> str:
        """
        Handle MULTI_HOP queries requiring sequential reasoning.
        """
        print("🚀 Routing to multi-hop reasoning")

        # Decompose the query
        sub_questions = self._decompose_multi_hop_query(question)

        if len(sub_questions) <= 1:
            return self._handle_hybrid_query(question)

        results = []
        for i, sub_q in enumerate(sub_questions[:3], 1):  # Limit to 3 steps
            print(f"🔄 Step {i}: {sub_q}")
            try:
                result = run_llama_index_sql_query(sub_q)
                if result and not result.startswith("Structured query engine not available"):
                    results.append(f"**Step {i}:** {sub_q}\n{result}")
                else:
                    results.append(f"**Step {i}:** {sub_q}\nNo data found for this step.")
            except Exception as e:
                results.append(f"**Step {i}:** {sub_q}\nError: {str(e)}")

        if results:
            return f"**Multi-Hop Analysis Results:**\n\n" + "\n\n".join(results)
        else:
            return "I couldn't complete the multi-step analysis for this query."

    def _decompose_multi_hop_query(self, question: str) -> List[str]:
        """
        Decompose multi-hop queries into sequential steps.
        """
        # Simple decomposition for now - can be enhanced with LLM
        question_lower = question.lower()

        if "among" in question_lower and "what" in question_lower:
            # Pattern: "Among X, what Y"
            return [
                question.split("among")[1].split(",")[0].strip() + "?",
                "What " + question.split("what")[1].strip()
            ]
        elif "compare" in question_lower:
            # Comparison queries
            return [
                "What are the details for " + question.split("compare")[1].split("and")[0].strip() + "?",
                "What are the details for " + question.split("and")[1].strip() + "?",
                "What are the key differences?"
            ]
        else:
            return [question]

    def _format_structured_response(self, raw_result: str, question: str) -> str:
        """
        Format structured query results into user-friendly answers.
        """
        if not raw_result or raw_result.startswith("Error"):
            return "I couldn't find the information you're looking for in the database."

        # For simple queries like "what are the companies", format as a clean list
        if "companies" in question.lower():
            return f"**Companies Found:**\n\n{raw_result}\n\n*Data from placement database*"

        return f"**Results:**\n\n{raw_result}\n\n*Database query results*"

    def _fallback_classification(self, question: str) -> str:
        """
        Fallback classification when LLM is unavailable.
        """
        question_lower = question.lower()

        # Basic heuristics based on keywords
        if any(word in question_lower for word in ['how many', 'count', 'total', 'average', 'list', 'what are']):
            return "STRUCTURED"
        elif any(word in question_lower for word in ['compare', 'versus', 'vs', 'among']):
            return "MULTI_HOP"
        elif any(word in question_lower for word in ['and', 'also', 'both']):
            return "HYBRID"
        else:
            return "UNSTRUCTURED"


# Global instance for easy access
query_router = QueryRouter()


# Test function for validation
def test_llm_driven_routing():
    """Test the LLM-driven query routing with sample queries."""
    router = QueryRouter()

    test_queries = [
        "what are the companies came for placements",  # Should be STRUCTURED (list query)
        "how many companies came for placements",  # Should be STRUCTURED (count query)
        "list all companies in finance",  # Should be STRUCTURED (filtered list)
        "Compare AWS and Azure cloud requirements",  # Should be MULTI_HOP (comparison + requirements)
        "Find companies offering ML roles with good salaries",  # Should be HYBRID (structured + analysis)
        "What skills are needed for data science?",  # Should be UNSTRUCTURED (skills analysis)
        "tell me about the company culture",  # Should be UNSTRUCTURED (descriptive)
        "among high-paying companies, what skills are most valued",  # Should be MULTI_HOP (complex multi-step)
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing: {query}")
        print(f"{'='*60}")

        # Test LLM classification
        try:
            classification = router._classify_query(query)
            print(f"LLM Classification: {classification}")

            # Test decomposition for multi-hop queries
            if classification == "MULTI_HOP":
                sub_questions = router._decompose_multi_hop_query(query)
                print(f"Decomposed into {len(sub_questions)} sub-questions:")
                for i, sq in enumerate(sub_questions, 1):
                    print(f"  {i}. {sq}")

        except Exception as e:
            print(f"❌ Test failed: {e}")
            # Fallback classification
            fallback = router._fallback_classification(query)
            print(f"Fallback Classification: {fallback}")


if __name__ == "__main__":
    test_llm_driven_routing()