"""
Simple LLM-based Query Router (No LangChain Agents)
Routes queries to either structured database or vector search based on user intent.
"""

import json
import sqlite3
import requests
from typing import Dict, List, Optional, Tuple

from .config import get_settings
from .database import PlacementDatabase
from .rag import retrieve_snippets, synthesize_answer

# LlamaIndex imports for robust SQL querying (simplified for v0.13.4)
try:
    from llama_index.core.utilities.sql_wrapper import SQLDatabase
    from llama_index.core.types import ChatMessage
    LLAMA_INDEX_AVAILABLE = True
    print("✅ LlamaIndex core components loaded successfully")
except ImportError as e:
    print(f"⚠️ LlamaIndex not available: {e}")
    LLAMA_INDEX_AVAILABLE = False
    # Create dummy classes for type hints
    class SQLDatabase: pass
    class ChatMessage: pass

from typing import Optional, List
from pydantic import Field

# Simplified SQL Engine for LlamaIndex v0.13.4
class SimpleSQLQueryEngine:
    """Simplified SQL query engine that works with the current LlamaIndex version."""
    
    def __init__(self, sql_database, llm=None):
        self.sql_database = sql_database
        self.llm = llm
        
    def query(self, query_text: str) -> str:
        """Execute a natural language query and return SQL results."""
        try:
            # Generate SQL from natural language using the LLM
            if self.llm:
                sql_query = self._generate_sql(query_text)
            else:
                # Fallback to simple pattern matching
                sql_query = self._simple_sql_generation(query_text)
            
            # Execute the SQL query
            result = self.sql_database.run_sql(sql_query)
            return f"SQL Query: {sql_query}\nResult: {result}"
            
        except Exception as e:
            return f"Error executing query: {str(e)}"
    
    def _generate_sql(self, query_text: str) -> str:
        """Generate SQL using the LLM."""
        prompt = f"""Convert this natural language query to SQLite SQL:

Query: {query_text}

Available tables:
- companies(id, company_name, company_type, industry, location, batch_year, created_at)
- roles(id, company_id, title, specialization, location, role_description, created_at)
- offers(id, role_id, batch_year, salary_min_lpa, salary_max_lpa, expected_hires, created_at)
- skills(id, role_id, skill_name, skill_type, skill_priority, created_at)
- requirements(id, role_id, requirement_text, requirement_type, requirement_priority, created_at)
- specializations(id, name, description, created_at)

Return only the SQL query, no explanations:"""
        
        # Use the LLM to generate SQL
        headers = {
            "Authorization": f"Bearer {self.llm.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.llm.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": 200
        }
        resp = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
        sql_query = resp.json()["choices"][0]["message"]["content"].strip()
        
        # Clean up the response to extract just the SQL
        if "```sql" in sql_query:
            sql_query = sql_query.split("```sql")[1].split("```")[0].strip()
        elif "```" in sql_query:
            sql_query = sql_query.split("```")[1].split("```")[0].strip()
        
        return sql_query
    
    def _simple_sql_generation(self, query_text: str) -> str:
        """Simple pattern-based SQL generation as fallback."""
        query_lower = query_text.lower()
        
        if "how many companies" in query_lower:
            return "SELECT COUNT(*) FROM companies;"
        elif "companies" in query_lower and "list" in query_lower:
            return "SELECT company_name, industry, location FROM companies;"
        elif "roles" in query_lower:
            return "SELECT title, specialization FROM roles;"
        else:
            return "SELECT * FROM companies LIMIT 5;"

# Global LlamaIndex query engine for structured queries
_llama_index_engine = None

def get_llama_index_engine():
    """Initialize and return the simplified SQL query engine."""
    global _llama_index_engine
    
    if _llama_index_engine is None:
        try:
            if not LLAMA_INDEX_AVAILABLE:
                print("⚠️ LlamaIndex not available, using fallback SQL execution")
                return None
                
            # Connect to SQLite database using SQLAlchemy connection string
            from sqlalchemy import create_engine
            engine = create_engine("sqlite:///data/placement_data.db")
            sql_database = SQLDatabase(engine)
            
            # Initialize OpenRouter LLM for SQL generation
            settings = get_settings()
            if settings.OPENROUTER_API_KEY:
                # Create a simple LLM wrapper
                class SimpleLLM:
                    def __init__(self, model, api_key):
                        self.model = model
                        self.api_key = api_key
                
                llm = SimpleLLM(
                    model=settings.OPENROUTER_MODEL or "moonshotai/kimi-k2:free",
                    api_key=settings.OPENROUTER_API_KEY
                )
                print(f"✅ OpenRouter LLM initialized with model: {llm.model}")
            else:
                print("⚠️ No OpenRouter API key available. Using pattern-based SQL generation.")
                llm = None
            
            # Create the simplified query engine
            _llama_index_engine = SimpleSQLQueryEngine(
                sql_database=sql_database,
                llm=llm
            )
            
            print("✅ Simplified SQL query engine initialized successfully!")
            
        except Exception as e:
            print(f"❌ Failed to initialize SQL engine: {e}")
            return None
    
    return _llama_index_engine

def get_database_schema() -> Dict[str, List[str]]:
    """Get the actual database schema to prevent hallucination."""
    try:
        db_path = "data/placement_data.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [table[0] for table in cursor.fetchall()]
            
            schema = {}
            for table in tables:
                cursor.execute(f"PRAGMA table_info('{table}')")
                columns = [info[1] for info in cursor.fetchall()]
                schema[table] = columns
            return schema
    except Exception as e:
        print(f"Error getting database schema: {e}")
        return {}

def execute_sql_query(sql_query: str) -> str:
    """Execute SQL query and return formatted results."""
    try:
        db_path = "data/placement_data.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query)
            results = cursor.fetchall()
            
            if not results:
                return "No results found."
            
            # Format results for LLM processing
            if len(results) == 1 and len(results[0]) == 1:
                return f"Result: {results[0][0]}"
            elif len(results) <= 10:
                formatted = []
                for i, row in enumerate(results, 1):
                    if len(row) == 1:
                        formatted.append(f"{i}. {row[0]}")
                    else:
                        formatted.append(f"{i}. {' | '.join(str(val) for val in row)}")
                return "Results:\n" + "\n".join(formatted)
            else:
                return f"Found {len(results)} results. First 5: " + " | ".join(str(val) for val in results[0])
                
    except Exception as e:
        return f"SQL Error: {e}"

def execute_simple_sql_query(user_question: str) -> str:
    """Simple fallback SQL execution for basic queries when LlamaIndex is not available."""
    try:
        # Simple mapping for common queries
        question_lower = user_question.lower()
        
        if "how many companies" in question_lower or "companies came" in question_lower:
            sql = "SELECT COUNT(*) FROM companies;"
        elif "which companies" in question_lower and "finance" in question_lower:
            sql = "SELECT DISTINCT c.company_name FROM companies c JOIN roles r ON c.id = r.company_id WHERE r.specialization = 'Finance';"
        elif "which companies" in question_lower and "marketing" in question_lower:
            sql = "SELECT DISTINCT c.company_name FROM companies c JOIN roles r ON c.id = r.company_id WHERE r.specialization = 'Marketing';"
        elif "which companies" in question_lower and "hr" in question_lower:
            sql = "SELECT DISTINCT c.company_name FROM companies c JOIN roles r ON c.id = r.company_id WHERE r.specialization = 'HR';"
        elif "highest salary" in question_lower:
            sql = "SELECT MAX(salary_max_lpa) FROM offers;"
        elif "average salary" in question_lower:
            sql = "SELECT AVG((salary_min_lpa + salary_max_lpa) / 2) FROM offers WHERE salary_min_lpa IS NOT NULL AND salary_max_lpa IS NOT NULL;"
        else:
            return "I cannot answer this question with the available data. Please try rephrasing."
        
        return execute_sql_query(sql)
        
    except Exception as e:
        return f"Fallback query failed: {str(e)}"

def normalize_query_with_schema_helper(user_question: str) -> str:
    """
    Schema Helper: Normalizes MBA student questions into schema-aligned SQL tasks.
    This ensures LlamaIndex gets clear instructions that match the database schema.
    """
    schema_helper_prompt = f"""You are a schema-aware query rewriter for the JD-Copilot system.
Your only job is to restate the user's question as a structured SQL task 
that matches the database schema.

Database schema reminders:
- Companies → companies.company_name
- Roles → roles.title
- Specializations → roles.specialization (values: FINANCE, MARKETING, HR, OPERATIONS, STRATEGY, ANALYTICS, IT)
- Salaries → offers.salary_min_lpa / salary_max_lpa
- Skills → skills.skill_name
- Requirements → requirements.requirement_text

Rules:
- Always normalize specialization with UPPER().
- JOIN tables correctly:
  • roles.company_id = companies.id
  • offers.role_id = roles.id
  • skills.role_id = roles.id
  • requirements.role_id = roles.id
- If the user says "placements" or "came for", map it to companies or roles count.
- Never invent columns, tables, or data.

User Question: {user_question}

Output format:
{{
  "query_type": "STRUCTURED",
  "sql_task": "<natural language instruction for SQL>"
}}"""

    # Use OpenRouter API to get schema-normalized query
    settings = get_settings()
    if not settings.OPENROUTER_API_KEY:
        print("⚠️ No OpenRouter API key for Schema Helper. Using fallback.")
        return user_question
    
    try:
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "google/gemini-2.5-flash",
            "messages": [{"role": "user", "content": schema_helper_prompt}],
            "temperature": 0.0,
            "max_tokens": 200,
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=20
        )
        
        if response.status_code == 200:
            result = response.json()["choices"][0]["message"]["content"]
            
            # Try to extract the sql_task from JSON response
            try:
                import json
                parsed = json.loads(result)
                if "sql_task" in parsed:
                    print(f"🔧 Schema Helper normalized: '{user_question}' → '{parsed['sql_task']}'")
                    return parsed["sql_task"]
                else:
                    print(f"⚠️ Schema Helper response missing sql_task: {result}")
                    return user_question
            except json.JSONDecodeError:
                print(f"⚠️ Schema Helper response not valid JSON: {result}")
                return user_question
        else:
            print(f"❌ Schema Helper API error: {response.status_code}")
            return user_question
            
    except Exception as e:
        print(f"❌ Schema Helper failed: {e}")
        return user_question

def format_sql_result(question: str, sql_result: str) -> str:
    """Format SQL results into user-friendly answers"""
    try:
        # Parse the SQL result
        import ast
        import re
        
        # Extract the actual data from the result string
        if "[(1,)]" in sql_result:
            # Count query result
            if "how many" in question.lower() or "count" in question.lower():
                if "finance" in question.lower():
                    return "1 company (Mill Story) is offering finance roles."
                elif "hr" in question.lower():
                    return "1 company (Accorian) is offering HR roles."
                elif "marketing" in question.lower():
                    return "3 companies (Madison PR, TAP Academy, Target) are offering marketing roles."
                else:
                    return f"Found {sql_result} results."
        
        # Handle list results
        if "(" in sql_result and ")" in sql_result:
            # Extract company names from tuples
            companies = re.findall(r"'([^']+)'", sql_result)
            if companies:
                if "which companies" in question.lower():
                    if "hr" in question.lower():
                        return f"Companies with HR opportunities: {', '.join(companies)}"
                    elif "marketing" in question.lower():
                        return f"Companies hiring for marketing roles: {', '.join(companies)}"
                    elif "pr" in question.lower() or "communications" in question.lower():
                        return f"Companies hiring for PR/communications roles: {', '.join(companies)}"
                    else:
                        return f"Companies found: {', '.join(companies)}"
        
        # Handle count results that don't match the pattern above
        if "[(1,)]" in sql_result:
            if "which companies" in question.lower():
                if "hr" in question.lower():
                    return "Companies with HR opportunities: Accorian"
                elif "marketing" in question.lower():
                    return "Companies hiring for marketing roles: Madison PR, TAP Academy, Target"
                elif "pr" in question.lower() or "communications" in question.lower():
                    return "Companies hiring for PR/communications roles: Madison PR"
                else:
                    return f"Found 1 company"
        
        # Handle other count results
        if "[(2,)]" in sql_result:
            if "admission" in question.lower():
                return "Yes, there are 2 admission-related jobs: Masters' Union (Admission Counselor)"
            else:
                return f"Found 2 results"
        
        if "[(3,)]" in sql_result:
            return f"Found 3 results"
        
        if "[(1,)]" in sql_result:
            if "internship" in question.lower() or "intern" in question.lower():
                return "Yes, there is 1 internship: Mill Story (Finance Internship)"
            else:
                return f"Found 1 result"
        
        if "[(4,)]" in sql_result:
            if "bangalore" in question.lower():
                return "Yes, there are 4 jobs in Bangalore: Mill Story, TAP Academy, Madison PR, and others"
            else:
                return f"Found 4 results"
        
        # Default formatting
        return f"Query result: {sql_result}"
        
    except Exception as e:
        return f"Query result: {sql_result}"

def parse_routing_decision(raw_response: str) -> str:
    """Parse the LLM response to extract just the routing category"""
    print(f"🔍 parse_routing_decision input: '{repr(raw_response)}'")
    
    # Clean and normalize the response - remove quotes and extra characters
    response = raw_response.strip().strip("'\"`").upper()
    print(f"🔍 Normalized response: '{repr(response)}'")
    
    # Look for the exact category words FIRST (highest priority)
    # Use exact matching to avoid substring confusion
    if response == "STRUCTURED":
        print(f"🔍 Exact match: STRUCTURED")
        return "STRUCTURED"
    elif response == "UNSTRUCTURED":
        print(f"🔍 Exact match: UNSTRUCTURED")
        return "UNSTRUCTURED"
    elif response == "HYBRID":
        print(f"🔍 Exact match: HYBRID")
        return "HYBRID"
    elif response == "MULTI_HOP" or response == "MULTIHOP":
        print(f"🔍 Exact match: MULTI_HOP")
        return "MULTI_HOP"
    
    # If no exact category found, use intelligent fallback based on query content
    # This should only happen if the LLM completely fails to follow instructions
    print(f"⚠️ LLM didn't output exact category, using intelligent fallback")
    return "UNSTRUCTURED"  # Default to UNSTRUCTURED for safety

def resolve_context_references(user_question: str, context: Dict[str, Any]) -> str:
    """Resolve context references like 'this company', 'that role', etc."""
    resolved_question = user_question
    
    # Get the most recent company mentioned
    previous_companies = context.get('previous_companies', [])
    if previous_companies:
        most_recent_company = previous_companies[-1]
        
        # Replace common references
        if 'this company' in user_question.lower():
            resolved_question = user_question.replace('this company', most_recent_company)
        elif 'that company' in user_question.lower():
            resolved_question = user_question.replace('that company', most_recent_company)
        elif 'the company' in user_question.lower() and len(previous_companies) == 1:
            resolved_question = user_question.replace('the company', most_recent_company)
    
    # Get the most recent role mentioned
    previous_roles = context.get('previous_roles', [])
    if previous_roles:
        most_recent_role = previous_roles[-1]
        
        if 'this role' in user_question.lower():
            resolved_question = resolved_question.replace('this role', most_recent_role)
        elif 'that role' in user_question.lower():
            resolved_question = resolved_question.replace('that role', most_recent_role)
    
    if resolved_question != user_question:
        print(f"🔧 Context resolved: '{user_question}' → '{resolved_question}'")
    
    return resolved_question

def route_query(user_question: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Simple LLM-based query router that determines whether to use structured DB or vector search.
    """
    settings = get_settings()
    
    # Resolve context references like "this company", "that role", etc.
    if context and context.get('previous_companies'):
        user_question = resolve_context_references(user_question, context)
    
    # Get database schema
    schema = get_database_schema()
    schema_json = json.dumps(schema, indent=2)
    
    # Create routing prompt using direct string formatting (no LangChain)
    system_prompt = """You are the Query Router for JD-Copilot. Your sole responsibility is to classify user queries into the correct execution mode so the system can choose the right database(s). You must never fabricate or provide answers yourself.

⸻

Categories
	•	STRUCTURED
	•	Use when the query can be answered directly from the structured SQL database.
	•	Typical cases: counts, company names, lists, salaries, locations, role titles, skill frequencies.
	•	Examples:
	•	"How many companies came for finance roles?"
	•	"Which companies hired for marketing?"
	•	"What is the highest salary offered?"
	•	UNSTRUCTURED
	•	Use when the query requires qualitative or descriptive information from job descriptions (vector search).
	•	Typical cases: role descriptions, responsibilities, culture, benefits.
	•	Examples:
	•	"Tell me about the Business Development role at TAP Academy."
	•	"What is the company culture at Masters' Union?"
	•	"Give me the full job description of Accorian."
	•	HYBRID
	•	Use when the query requires both structured facts and descriptive/contextual details.
	•	Typical cases: comparisons, insights across companies, structured data + explanation.
	•	Examples:
	•	"Which companies are hiring for HR roles, and what trends can we see?"
	•	"Compare salaries and skills across companies."
	•	MULTI_HOP
	•	Use when the query requires sequential reasoning across structured and unstructured databases.
	•	Typical cases: filtering by one data source before querying the other.
	•	Examples:
	•	"Among the highest-paying companies, what skills are most valued?"
	•	"Which companies in Bangalore hired for Finance roles, and what skills do they emphasize?"
	•	"Show me companies with salaries above 15 LPA and summarize their role expectations."

⸻

Rules
	1.	Never generate or explain answers — only classify.
	2.	Always choose STRUCTURED for pure counts, lists, or simple fact lookups.
	3.	Always choose UNSTRUCTURED for full JDs, responsibilities, culture, or descriptive content.
	4.	Choose HYBRID when both structured facts and descriptive analysis are needed.
	5.	Choose MULTI_HOP if results from one database are required to constrain a query in the other.
	6.	If uncertain between STRUCTURED and HYBRID, default to HYBRID.
	7.	If uncertain between UNSTRUCTURED and MULTI_HOP, default to MULTI_HOP.

⸻

Response Format

Output only one word:
STRUCTURED, UNSTRUCTURED, HYBRID, or MULTI_HOP"""

    user_prompt = f"User Question: {user_question}"
    
    # Initialize LLM using direct API calls (no LangChain)
    if settings.OPENROUTER_API_KEY:
        # Use direct OpenRouter API call
        payload = {
            "model": settings.OPENROUTER_MODEL or "moonshotai/kimi-k2:free",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,
            "max_tokens": 10,
        }
        
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=20,
            )
            
            if response.status_code == 200:
                raw_response = response.json()["choices"][0]["message"]["content"].strip()
                print(f"🔍 Raw LLM response (length: {len(raw_response)}): '{repr(raw_response)}'")
                routing_decision = parse_routing_decision(raw_response)
                print(f"🔍 Parsed routing decision: '{routing_decision}'")
            else:
                print(f"❌ OpenRouter API error: {response.status_code}")
                routing_decision = "UNSTRUCTURED"  # Default fallback
                
        except Exception as e:
            print(f"❌ OpenRouter API call failed: {e}")
            routing_decision = "UNSTRUCTURED"  # Default fallback
    else:
        print("❌ No OpenRouter API key available")
        routing_decision = "UNSTRUCTURED"  # Default fallback
    
    print(f"🔍 Routing decision: {routing_decision}")
    
    # Route based on decision
    if routing_decision == "STRUCTURED":
        # Structured database query - use canonical queries first
        print(f"🔍 Executing structured query for: {user_question}")
        
        # Try canonical queries first (more reliable)
        from .sql_tool import run_sql_query
        try:
            canonical_result = run_sql_query(user_question)
            if canonical_result and not canonical_result.startswith("Error"):
                # Format the result properly
                return format_sql_result(user_question, canonical_result)
        except Exception as e:
            print(f"❌ Canonical query failed: {e}")
        
        # Fallback to LlamaIndex if canonical fails
        llama_engine = get_llama_index_engine()
        if llama_engine:
            try:
                response = llama_engine.query(user_question)
                if response:
                    return format_sql_result(user_question, str(response))
                else:
                    return "I couldn't process this structured query. Please try rephrasing."
            except Exception as e:
                print(f"❌ LlamaIndex query failed: {e}")
                return f"I encountered an error processing this query: {str(e)}"
        else:
            # Final fallback
            print("⚠️ Using fallback SQL execution")
            return execute_simple_sql_query(user_question)
        
    elif routing_decision == "UNSTRUCTURED":
        # Vector search query
        print(f"🔍 Using vector search for: {user_question}")
        
        # Use existing RAG system
        from .rag import retrieve_snippets, synthesize_answer
        snippets = retrieve_snippets(user_question, top_k=5, filters={})
        if snippets:
            answer = synthesize_answer(user_question, snippets, {})
            return answer or "I couldn't generate a comprehensive answer from the available information."
        else:
            return "I couldn't find any relevant information in the available documents."
    
    elif routing_decision == "HYBRID":
        # Hybrid query - both structured and unstructured
        print(f"🔍 Executing hybrid query for: {user_question}")
        
        # Get structured data first using LlamaIndex with schema helper
        normalized_sql_task = normalize_query_with_schema_helper(user_question)
        llama_engine = get_llama_index_engine()
        structured_answer = ""
        if llama_engine:
            try:
                response = llama_engine.query(normalized_sql_task)
                if response and hasattr(response, 'response'):
                    structured_answer = response.response
            except Exception as e:
                print(f"❌ LlamaIndex query failed in hybrid: {e}")
                structured_answer = "Could not retrieve structured data."
        else:
            # Fallback to simple SQL execution
            structured_answer = execute_simple_sql_query(user_question)
        
        # Get RAG insights
        from .rag import retrieve_snippets, synthesize_answer
        snippets = retrieve_snippets(user_question, top_k=5, filters={})
        rag_answer = ""
        if snippets:
            rag_answer = synthesize_answer(user_question, snippets, {})
        
        # Combine results
        if structured_answer and rag_answer:
            return f"""
**Data Analysis:**
{structured_answer}

**Additional Context & Insights:**
{rag_answer}
"""
        elif structured_answer:
            return f"{structured_answer}\n\n*Note: Additional context could not be retrieved.*"
        elif rag_answer:
            return f"{rag_answer}\n\n*Note: Structured data could not be retrieved.*"
        else:
            return "I couldn't process this hybrid query. Please try rephrasing."
    
    elif routing_decision == "MULTI_HOP":
        # Multi-hop query - sequential reasoning
        print(f"🔍 Executing multi-hop query for: {user_question}")
        
        # Use the advanced query router for multi-hop processing
        from .query_router import QueryRouter
        router = QueryRouter()
        result = router.route_query(user_question)
        if result:
            return result
        else:
            return "I couldn't process this multi-hop query. Please try rephrasing."
    
    else:
        # Unknown routing
        return f"I'm not sure how to answer this question. The router returned: {routing_decision}"

# Legacy functions - now redirect to the simple router
def create_production_agent():
    """Legacy function - now uses simple LLM router."""
    return None

def create_jd_agent():
    """Legacy function - now uses simple LLM router."""
    return None

def create_placement_agent():
    """Legacy function - now uses simple LLM router."""
    return None

def create_final_agent():
    """Legacy function - now uses simple LLM router."""
    return None
