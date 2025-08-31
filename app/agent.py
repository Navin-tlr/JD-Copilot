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

# LlamaIndex imports for robust SQL querying
from llama_index.core import SQLDatabase, ServiceContext
from llama_index.core.llms import LLM, LLMMetadata, ChatMessage, ChatResponse, CompletionResponse
from llama_index.core.query_engine import NLSQLTableQueryEngine
from typing import Optional, List
from pydantic import Field

# Custom OpenRouter LLM wrapper for LlamaIndex
class OpenRouterLLM(LLM):
    """Custom LLM wrapper for OpenRouter API to work with LlamaIndex."""
    
    model: str = Field(default="google/gemini-2.5-pro-exp-03-25", description="OpenRouter model name")
    api_key: str = Field(default=None, description="OpenRouter API key")
    
    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=8192,    # adjust based on model
            num_output=512,         # typical safe default
            is_chat_model=True,
            is_function_calling_model=False
        )
    
    def complete(self, prompt: str, **kwargs) -> CompletionResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": 0,
            "max_tokens": 512
        }
        resp = requests.post("https://openrouter.ai/api/v1/completions", json=payload, headers=headers)
        text = resp.json()["choices"][0]["text"]
        return CompletionResponse(text=text)
    
    def chat(self, messages: List[ChatMessage], **kwargs) -> ChatResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": 0,
            "max_tokens": 512
        }
        resp = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
        text = resp.json()["choices"][0]["message"]["content"]
        return ChatResponse(message=ChatMessage(role="assistant", content=text))
    
    def stream_complete(self, prompt, **kwargs):
        """Stream completion (not implemented for simplicity)."""
        raise NotImplementedError("Streaming not implemented for OpenRouter LLM")
    
    def stream_chat(self, messages, **kwargs):
        """Stream chat (not implemented for simplicity)."""
        raise NotImplementedError("Streaming not implemented for OpenRouter LLM")
    
    def acomplete(self, prompt, **kwargs):
        """Async complete (not implemented for simplicity)."""
        raise NotImplementedError("Async not implemented for OpenRouter LLM")
    
    def achat(self, messages, **kwargs):
        """Async chat (not implemented for simplicity)."""
        raise NotImplementedError("Async not implemented for OpenRouter LLM")
    
    def astream_complete(self, prompt, **kwargs):
        """Async stream complete (not implemented for simplicity)."""
        raise NotImplementedError("Async not implemented for OpenRouter LLM")
    
    def astream_chat(self, messages, **kwargs):
        """Async stream chat (not implemented for simplicity)."""
        raise NotImplementedError("Async not implemented for OpenRouter LLM")

# Global LlamaIndex query engine for structured queries
_llama_index_engine = None

def get_llama_index_engine():
    """Initialize and return the LlamaIndex SQL query engine."""
    global _llama_index_engine
    
    if _llama_index_engine is None:
        try:
            # Connect to SQLite database using SQLAlchemy connection string
            from sqlalchemy import create_engine
            engine = create_engine("sqlite:///data/placement_data.db")
            sql_database = SQLDatabase(engine)
            
            # Create strict guardrailed prompt for Text2SQL
            TEXT2SQL_PROMPT = """You are an expert SQL query generator for the JD-Copilot system.
Your job is to translate user questions into SAFE SQLite queries against the given schema.

SCHEMA (you may ONLY use these tables and columns):
- companies(id, company_name, company_type, industry, location, batch_year, created_at)
- roles(id, company_id, title, specialization, location, role_description, created_at)
- offers(id, role_id, batch_year, salary_min_lpa, salary_max_lpa, expected_hires, created_at)
- skills(id, role_id, skill_name, skill_type, skill_priority, created_at)
- requirements(id, role_id, requirement_text, requirement_type, requirement_priority, created_at)
- specializations(id, name, description, created_at)

STRICT RULES:
1. Use ONLY the tables and columns listed above. Never invent new tables or columns.
2. If the user's question cannot be answered from this schema, respond with:
   I cannot answer this question with the available data.
3. Always return a full, runnable SQL SELECT statement. Do not return explanations or partial queries.
4. Prefer the simplest valid query. 
   - Example: For "How many companies?", use `SELECT COUNT(*) FROM companies;`
   - Only use JOINs if the question explicitly requires role, salary, skill, or requirement details.
5. Never hallucinate rows or output imaginary results. Query only what exists in the database.
"""
            
            # Initialize custom OpenRouter LLM
            settings = get_settings()
            if settings.OPENROUTER_API_KEY:
                llm = OpenRouterLLM(
                    model="moonshotai/kimi-k2",
                    api_key=settings.OPENROUTER_API_KEY
                )
                print(f"✅ OpenRouter LLM initialized with model: {llm.model}")
            else:
                print("⚠️ No OpenRouter API key available for LlamaIndex. Using fallback.")
                return None
            
            # Configure service context to avoid embedding model issues
            service_context = ServiceContext.from_defaults(
                llm=llm,
                embed_model=None  # Disable embeddings for SQL queries
            )
            
            _llama_index_engine = NLSQLTableQueryEngine(
                sql_database=sql_database,
                service_context=service_context,
                text2sql_prompt=TEXT2SQL_PROMPT
            )
            
            print("✅ LlamaIndex SQL query engine initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize LlamaIndex engine: {e}")
            _llama_index_engine = None
    
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
            "model": "google/gemini-2.5-pro-exp-03-25",
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

def route_query(user_question: str) -> str:
    """
    Simple LLM-based query router that determines whether to use structured DB or vector search.
    """
    settings = get_settings()
    
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
            "model": "google/gemini-2.5-pro-exp-03-25",
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
        # Structured database query - use LlamaIndex NLSQLTableQueryEngine
        print(f"🔍 Executing structured query for: {user_question}")
        
        # Normalize the query using the schema helper
        normalized_sql_task = normalize_query_with_schema_helper(user_question)
        
        # Use LlamaIndex for robust SQL querying
        llama_engine = get_llama_index_engine()
        if llama_engine:
            try:
                response = llama_engine.query(normalized_sql_task)
                if response and hasattr(response, 'response'):
                    return response.response
                else:
                    return "I couldn't process this structured query. Please try rephrasing."
            except Exception as e:
                print(f"❌ LlamaIndex query failed: {e}")
                return f"I encountered an error processing this query: {str(e)}"
        else:
            # Fallback to simple SQL execution
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
