"""
Advanced LLM-based Query Router with Custom OpenRouter Integration
Routes queries to structured database or vector search based on user intent.
Uses LlamaIndex's NLSQLTableQueryEngine and intelligent multi-hop decomposition.
"""

import json
import sqlite3
import requests
from typing import Any, Dict, List, Optional, Tuple, AsyncIterator

from .config import get_settings
from .database import PlacementDatabase
from .rag import retrieve_snippets, synthesize_answer, get_pinecone_index

# LlamaIndex imports for intelligent Text-to-SQL
try:
    from llama_index.core.llms import CustomLLM, CompletionResponse, LLMMetadata
    from llama_index.core.llms.callbacks import llm_completion_callback
    from llama_index.core import SQLDatabase, Settings
    from llama_index.core.query_engine import NLSQLTableQueryEngine
    from llama_index.core.embeddings import BaseEmbedding
    from sqlalchemy import create_engine
    
    # Disable default tokenization to avoid tiktoken dependency
    Settings.tokenizer = None
    
    LLAMA_INDEX_AVAILABLE = True
    print("✅ LlamaIndex core components loaded successfully")
except ImportError as e:
    print(f"⚠️ LlamaIndex not available: {e}")
    LLAMA_INDEX_AVAILABLE = False
    # Create dummy classes for type hints
    class CustomLLM: pass
    class CompletionResponse: pass
    class LLMMetadata: pass
    class SQLDatabase: pass
    class NLSQLTableQueryEngine: pass
    class HuggingFaceEmbedding: pass
    class MockEmbedding: pass

class OpenRouterLLM(CustomLLM):
    """
    Proper OpenRouter wrapper that doesn't inherit from OpenAI class
    to avoid model name validation issues
    """
    model: str
    api_key: str
    temperature: float = 0.1
    max_tokens: int = 512
    api_base: str = "https://openrouter.ai/api/v1"

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=8192,
            num_output=self.max_tokens,
            model_name=self.model,
            # Disable tokenization to avoid tiktoken dependency
            tokenizer=None,
        )

    def _is_sql_prompt(self, prompt: str) -> bool:
        p = prompt.lower()
        # Heuristic: LlamaIndex Text-to-SQL prompt contains per-table column summaries
        return ("table 'roles' has columns" in p and "table 'companies' has columns" in p) or "write a sql" in p

    def _sql_guardrails(self) -> str:
        # Use local schema context and hard rules to avoid column confusion
        try:
            ctx = get_table_context_for_engine()
        except Exception:
            ctx = ""
        rules = (
            "You are generating SQL over the given schema.\n"
            "Rules:\n"
            "1) Map MBA domains like Marketing, Finance, HR, Operations, Analytics to roles.specialization (NOT companies.industry).\n"
            "2) To count companies for a specialization, JOIN roles to companies and COUNT(DISTINCT companies.id).\n"
            "3) Prefer explicit qualified columns (table.column).\n"
            "4) Do not infer new columns; only use listed schema.\n\n"
            "Examples:\n"
            "- Q: How many companies came for Marketing?\n"
            "  SQL: SELECT COUNT(DISTINCT c.id) FROM companies c JOIN roles r ON r.company_id = c.id WHERE r.specialization = 'Marketing';\n"
            "- Q: List companies that recruited for Finance\n"
            "  SQL: SELECT DISTINCT c.company_name FROM companies c JOIN roles r ON r.company_id = c.id WHERE r.specialization = 'Finance';\n"
        )
        return f"{ctx}\n\n{rules}"

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "JD-Copilot"
        }
        messages = [{"role": "user", "content": prompt}]
        try:
            if self._is_sql_prompt(prompt):
                messages = [{"role": "system", "content": self._sql_guardrails()}, {"role": "user", "content": prompt}]
        except Exception:
            # Fallback to original single-message behavior
            messages = [{"role": "user", "content": prompt}]
        payload = {"model": self.model, "messages": messages, "temperature": self.temperature, "max_tokens": self.max_tokens}
        
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=15,  # Reduced timeout
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return CompletionResponse(text=content)
        except requests.Timeout:
            print(f"⏰ OpenRouter API timeout for model {self.model}")
            return CompletionResponse(text="Error: Request timeout")
        except Exception as e:
            print(f"❌ OpenRouter API request failed: {e}")
            return CompletionResponse(text=f"Error: {e}")

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any):
        response = self.complete(prompt, **kwargs)
        yield response

# Global query engines
_sql_query_engine = None
_vector_index = None

def get_sql_query_engine():
    """Initialize and return the LlamaIndex NLSQLTableQueryEngine."""
    global _sql_query_engine

    if _sql_query_engine is None and LLAMA_INDEX_AVAILABLE:
        try:
            from sqlalchemy import create_engine

            # Connect to SQLite database
            engine = create_engine("sqlite:///data/placement_data.db")
            
            # Create comprehensive table information with semantic intent mapping
            custom_table_info = {
                "companies": """Companies that offer job roles to students.
Columns: id, company_name, company_type, industry, location, batch_year
SEMANTIC MAPPING:
- 'industry' = company's business sector (Technology, Finance, Healthcare, etc.) - NOT job specializations
- When users ask about "companies in tech/finance sector" → use companies.industry  
- When users ask about "companies for Marketing/Finance jobs" → use roles.specialization (different concept!)

EXAMPLES:
- "Tech companies" → WHERE companies.industry LIKE '%Tech%'
- "Companies for Marketing roles" → JOIN roles WHERE roles.specialization = 'Marketing'""",
                
                "roles": """Job positions offered by companies to students.
Columns: id, company_id, title, specialization, location, role_description, source_chunk_id
SEMANTIC MAPPING:
- 'specialization' = MBA functional area (Marketing, Finance, HR, Operations, Analytics, Strategy, IT)
- 'title' = specific job title (Analyst, Manager, Consultant, etc.)
- When users ask about job domains/functions → ALWAYS use roles.specialization
- When users ask about job titles → use roles.title

CRITICAL INTENT MAPPING:
Marketing/Finance/HR/Operations/Analytics/Strategy/IT questions → roles.specialization
Job titles like Analyst/Manager/Consultant → roles.title
Company counting for domains → JOIN companies, COUNT(DISTINCT companies.id)

EXAMPLES:
- "Marketing jobs" → WHERE roles.specialization = 'Marketing'
- "How many companies for Finance?" → SELECT COUNT(DISTINCT c.id) FROM companies c JOIN roles r ON r.company_id = c.id WHERE r.specialization = 'Finance'""",
                
                "offers": """Salary and placement statistics for roles.
Columns: id, role_id, batch_year, salary_min_lpa, salary_max_lpa, expected_hires
SEMANTIC MAPPING:
- salary questions → use salary_min_lpa, salary_max_lpa
- hiring numbers → use expected_hires
- year-specific data → filter by batch_year""",
                
                "skills": """Technical and soft skills required for roles.
Columns: id, role_id, skill_name, skill_type, skill_priority
SEMANTIC MAPPING:
- skill requirements → skill_name
- skill categories → skill_type""",
                
                "requirements": """Educational and experience requirements for roles.
Columns: id, role_id, requirement_text, requirement_type, requirement_priority
SEMANTIC MAPPING:
- education requirements → requirement_type = 'education'
- experience requirements → requirement_type = 'experience'  
- responsibilities → requirement_type = 'responsibility'""",
                
                "specializations": "Reference table for MBA specializations (Marketing, Finance, HR, etc.)"
            }

            sql_database = SQLDatabase(engine, custom_table_info=custom_table_info)

            # Initialize OpenRouter LLM using CustomLLM wrapper
            settings = get_settings()
            if settings.OPENROUTER_API_KEY:
                llm = OpenRouterLLM(
                    model=settings.OPENROUTER_MODEL or "mistralai/mistral-medium-3.1",
                    api_key=settings.OPENROUTER_API_KEY,
                    temperature=0.0
                )
                print(f"✅ OpenRouter LLM initialized with model: {llm.model}")
            else:
                print("❌ No OpenRouter API key available")
                return None

            # Create mock embedding to avoid external dependencies
            class MockEmbedding(BaseEmbedding):
                def _get_query_embedding(self, query: str):
                    return [0.0] * 384
                    
                def _get_text_embedding(self, text: str):
                    return [0.0] * 384
                    
                async def _aget_query_embedding(self, query: str):
                    return [0.0] * 384
                    
                async def _aget_text_embedding(self, text: str):
                    return [0.0] * 384
                    
                @property
                def embed_batch_size(self) -> int:
                    return 10
                    
            embed_model = MockEmbedding()

            # Create NLSQLTableQueryEngine with explicit embedding and custom prompt
            from llama_index.core.prompts import PromptTemplate
            
            # Custom Text-to-SQL prompt that emphasizes intent understanding
            text_to_sql_prompt = PromptTemplate(
                """You are an expert at converting natural language questions into SQL queries for a placement database.

DATABASE SCHEMA WITH INTENT MAPPING:
{schema}

CRITICAL RULES FOR INTENT UNDERSTANDING:
1. Job Domain Questions (Marketing, Finance, HR, Operations, Analytics, Strategy, IT):
   - These refer to MBA specializations → Use roles.specialization column
   - IMPORTANT: Specializations in database are UPPERCASE (MARKETING, FINANCE, HR, OPERATIONS, etc.)
   - Use UPPER() function or direct uppercase values for case-insensitive matching
   - Example: "Marketing jobs" → WHERE roles.specialization = 'MARKETING' OR WHERE UPPER(roles.specialization) = UPPER('Marketing')

2. Company Industry Questions (Tech, Healthcare, Banking sector):
   - These refer to company business sectors → Use companies.industry column  
   - Example: "Tech companies" → WHERE companies.industry LIKE '%Tech%'

3. Counting Companies for Job Domains:
   - Always JOIN roles to companies and COUNT(DISTINCT companies.id)
   - Example: "How many companies for Finance?" → COUNT(DISTINCT c.id) FROM companies c JOIN roles r ON r.company_id = c.id WHERE r.specialization = 'FINANCE'

4. Only use columns that exist in the schema. Do not invent columns.

5. Use explicit table aliases and qualified column names for clarity.

6. For specialization matching, always use UPPERCASE values: MARKETING, FINANCE, HR, OPERATIONS, BUSINESS ANALYTICS

QUESTION: {query_str}

Generate ONLY the SQL query, no explanation:"""
            )

            _sql_query_engine = NLSQLTableQueryEngine(
                sql_database=sql_database,
                llm=llm,
                embed_model=embed_model,
                text_to_sql_prompt=text_to_sql_prompt,
                verbose=True
            )

            print("✅ NLSQLTableQueryEngine initialized successfully!")

        except Exception as e:
            print(f"❌ Failed to initialize SQL query engine: {e}")
            return None

    return _sql_query_engine

def get_table_context_for_engine() -> str:
    """
    Generates a detailed, context-rich string describing tables for the LlamaIndex engine.
    This is crucial for guiding the LLM to make correct inferences.
    """
    return """Database Schema with Context:

Table 'companies':
  Description: Lists the companies offering roles. Contains company name, industry, and location.
  IMPORTANT: The 'industry' column refers to the company's general business sector (e.g., 'E-commerce', 'Software'). This is NOT the same as role specializations.
  Columns: id (INTEGER), company_name (TEXT), company_type (TEXT), industry (TEXT), location (TEXT), batch_year (TEXT), created_at (TIMESTAMP)

Table 'roles':
  Description: Contains job roles offered by companies.
  CRITICAL: The 'specialization' column is used for questions about MBA domains like 'Marketing', 'Finance', 'HR', 'Operations', etc. 
  When users ask about "marketing", "finance", etc., they are referring to this 'specialization' column, NOT the company's industry.
  Always JOIN this table with 'companies' to link roles to companies.
  Columns: id (INTEGER), company_id (INTEGER), title (TEXT), specialization (TEXT), location (TEXT), role_description (TEXT), created_at (TIMESTAMP)

Table 'offers':
  Description: Contains salary and hiring data for roles. 'salary_max_lpa' is in Lakhs Per Annum.
  Columns: id (INTEGER), role_id (INTEGER), batch_year (TEXT), salary_min_lpa (REAL), salary_max_lpa (REAL), expected_hires (INTEGER), created_at (TIMESTAMP)

Table 'skills':
  Description: Lists specific skills required for each role.
  Columns: id (INTEGER), role_id (INTEGER), skill_name (TEXT), skill_type (TEXT), skill_priority (INTEGER), created_at (TIMESTAMP)

Table 'requirements':
  Description: Lists educational or other requirements for each role.
  Columns: id (INTEGER), role_id (INTEGER), requirement_text (TEXT), requirement_type (TEXT), requirement_priority (INTEGER), created_at (TIMESTAMP)

Table 'specializations':
  Description: Reference table for MBA specializations.
  Columns: id (INTEGER), name (TEXT), description (TEXT), created_at (TIMESTAMP)

FOREIGN KEY RELATIONSHIPS:
- roles.company_id → companies.id
- offers.role_id → roles.id
- skills.role_id → roles.id
- requirements.role_id → roles.id
"""

def get_vector_index():
    """Initialize and return a Pinecone-backed query adapter for unstructured queries.

    This returns an object with `.as_query_engine()` which returns an object with `.query(question)`.
    The returned `.query()` returns an object with a `response` attribute (string) so it integrates with
    the existing `execute_unstructured_query()` logic.
    """
    settings = get_settings()

    # Ensure Pinecone is configured via rag.get_pinecone_index()
    try:
        index = get_pinecone_index()
    except Exception as e:
        print(f"⚠️ Pinecone not available: {e}")
        return None

    # Adapter that provides a minimal query engine API
    class PineconeQueryAdapter:
        def __init__(self, index):
            self._index = index

        def as_query_engine(self):
            return self

        def query(self, question: str):
            # Use existing retrieve_snippets + synthesize_answer to produce a response
            try:
                snippets = retrieve_snippets(question, top_k=15, filters={})
                answer = synthesize_answer(question, snippets, {})
                class Resp:
                    def __init__(self, text: str):
                        self.response = text
                return Resp(answer or "I couldn't generate a comprehensive answer.")
            except Exception as e:
                class RespErr:
                    def __init__(self, text: str):
                        self.response = text
                return RespErr(f"I encountered an error in vector retrieval: {e}")

    return PineconeQueryAdapter(index)

def decompose_multi_hop_query(user_question: str) -> List[str]:
    """
    Query decomposition is disabled as per user request to prevent hallucinations.
    This function now returns the original question directly.
    """
    print("ℹ️ Query decomposition is disabled. Processing the query directly.")
    return [user_question]

def execute_multi_hop_query(sub_questions: List[str]) -> str:
    """Execute a sequence of sub-questions and combine results."""
    results = []
    context = {}

    for i, question in enumerate(sub_questions, 1):
        print(f"🔍 Executing sub-question {i}: {question}")

        # Route each sub-question
        result = route_single_query(question, context)

        # Store result for context
        context[f"step_{i}_result"] = result
        results.append(f"**Step {i}:** {question}\n{result}")

    # Combine all results
    combined = "\n\n".join(results)
    return f"**Multi-Hop Analysis:**\n\n{combined}"

def route_single_query(user_question: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Route a single query to the appropriate engine."""
    settings = get_settings()

    # Get database schema for routing decision
    schema = get_database_schema()
    schema_json = json.dumps(schema, indent=2)

    # Enhanced routing prompt
    system_prompt = """You are the Query Router for JD-Copilot. Classify queries into: STRUCTURED, UNSTRUCTURED, HYBRID.

Categories:
• STRUCTURED: Pure database queries (counts, lists, salaries, company names)
• UNSTRUCTURED: Qualitative info from documents (descriptions, culture, benefits)
• HYBRID: Both structured facts and qualitative analysis

Output only one word: STRUCTURED, UNSTRUCTURED, or HYBRID"""

    user_prompt = f"Query: {user_question}\n\nDatabase Schema: {schema_json}"

    # Use OpenRouter for routing decision
    if settings.OPENROUTER_API_KEY:
        try:
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": settings.OPENROUTER_MODEL or "moonshotai/kimi-k2:free",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.0,
                "max_tokens": 10,
            }

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=20,
            )

            if response.status_code == 200:
                raw_response = response.json()["choices"][0]["message"]["content"].strip().upper()
                routing_decision = raw_response
            else:
                routing_decision = "UNSTRUCTURED"
        except Exception as e:
            print(f"❌ Routing API call failed: {e}")
            routing_decision = "UNSTRUCTURED"
    else:
        routing_decision = "UNSTRUCTURED"

    print(f"🔍 Routing decision: {routing_decision}")

    # Execute based on routing decision
    if routing_decision == "STRUCTURED":
        return execute_structured_query(user_question)
    elif routing_decision == "UNSTRUCTURED":
        return execute_unstructured_query(user_question)
    elif routing_decision == "HYBRID":
        return execute_hybrid_query(user_question)
    else:
        return "I couldn't determine how to process this query."

def execute_structured_query(user_question: str) -> str:
    """Execute structured database query using LlamaIndex."""
    print(f"🔍 Executing structured query: {user_question}")

    engine = get_sql_query_engine()
    if engine:
        try:
            # The context is now built into the engine during initialization
            response = engine.query(user_question)

            # Intercept and correct common column mix-up: industry vs specialization
            corrected = _maybe_rewrite_specialization_answer(user_question, response)
            if corrected is not None:
                return corrected

            if hasattr(response, 'response'):
                return _summarize_sql_with_llm(user_question, response.response)
            else:
                return _summarize_sql_with_llm(user_question, str(response))
        except Exception as e:
            print(f"❌ SQL query failed: {e}")
            return f"I encountered an error processing this query: {str(e)}"
    else:
        return "SQL query engine not available."

def execute_unstructured_query(user_question: str) -> str:
    """Execute unstructured query using vector search."""
    print(f"🔍 Executing unstructured query: {user_question}")

    index = get_vector_index()
    if index:
        try:
            query_engine = index.as_query_engine()
            response = query_engine.query(user_question)
            if hasattr(response, 'response'):
                return response.response
            else:
                return str(response)
        except Exception as e:
            print(f"❌ Vector query failed: {e}")
            return f"I encountered an error processing this query: {str(e)}"
    else:
        # Fallback to existing RAG system
        snippets = retrieve_snippets(user_question, top_k=15, filters={})
        if snippets:
            answer = synthesize_answer(user_question, snippets, {})
            return answer or "I couldn't generate a comprehensive answer."
        else:
            return "I couldn't find relevant information."

def execute_hybrid_query(user_question: str) -> str:
    """Execute hybrid query combining structured and unstructured data."""
    print(f"🔍 Executing hybrid query: {user_question}")

    structured_result = execute_structured_query(user_question)
    unstructured_result = execute_unstructured_query(user_question)

    return f"""
**Structured Data:**
{structured_result}

**Additional Context:**
{unstructured_result}
"""

def get_database_schema() -> Dict[str, List[str]]:
    """Get the actual database schema."""
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

def _summarize_sql_with_llm(question: str, sql_result: str) -> str:
    """Use LLM to summarize SQL results in natural language."""
    settings = get_settings()

    if not settings.OPENROUTER_API_KEY:
        return sql_result

    prompt = f"""Summarize this SQL query result for the user question.

Question: {question}
Result: {sql_result}

Rules:
- If result contains company names, format as: "X companies came for placements — they are: A, B, C"
- If result contains only counts, format as: "X companies came for placements"
- Keep it concise and natural
- Use only the data present in the result

Summary:"""

    try:
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": settings.OPENROUTER_MODEL or "moonshotai/kimi-k2:free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 150,
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )

        if response.status_code == 200:
            result = response.json()["choices"][0]["message"]["content"]
            return result.strip()
        else:
            return sql_result

    except Exception as e:
        print(f"❌ SQL summarization failed: {e}")
        return sql_result


# -------- Specialization correction guardrails --------

MBA_SPECIALIZATIONS = [
    "MARKETING", "FINANCE", "HR", "HUMAN RESOURCES", "OPERATIONS", "STRATEGY", "IT", "ANALYTICS"
]

def _extract_specialization_from_question(question: str) -> Optional[str]:
    q = question.lower()
    mapping = {
        "marketing": "MARKETING",
        "finance": "FINANCE", 
        "human resources": "HR",
        "hr": "HR",
        "operations": "OPERATIONS",
        "strategy": "STRATEGY",
        "it": "IT",
        "analytics": "BUSINESS ANALYTICS",
        "business analytics": "BUSINESS ANALYTICS",
    }
    # check multi-word first
    if "business analytics" in q:
        return mapping["business analytics"]
    if "human resources" in q:
        return mapping["human resources"]
    for key, val in mapping.items():
        if key in q:
            return val
    return None

def _maybe_rewrite_specialization_answer(user_question: str, llm_response: Any) -> Optional[str]:
    """If the generated SQL incorrectly uses companies.industry for MBA domain queries, fix it.

    Strategy: detect MBA specialization intent from the question and check the response metadata for a SQL query
    that filters by companies.industry. If so, compute the correct result via roles.specialization using PlacementDatabase
    and return a clean natural-language answer.
    """
    try:
        spec = _extract_specialization_from_question(user_question)
        if not spec:
            return None

        # Read generated SQL if available
        sql_meta = None
        if hasattr(llm_response, "metadata") and isinstance(llm_response.metadata, dict):
            sql_meta = llm_response.metadata.get("sql_query")

        if not sql_meta and hasattr(llm_response, "source_nodes"):
            # Fallback: try first source node metadata
            nodes = getattr(llm_response, "source_nodes", []) or []
            if nodes:
                node_meta = getattr(nodes[0].node, "metadata", {})
                sql_meta = node_meta.get("sql_query")

        # If model used companies.industry in SQL while the question is specialization-focused, correct it
        if sql_meta and "companies" in sql_meta and "industry" in sql_meta.lower():
            db = PlacementDatabase()
            companies = db.get_companies_by_specialization(spec, batch_year=None)
            norm = {}
            for c in companies:
                name = (c.get("company_name") or "").strip()
                if not name:
                    continue
                key = name.lower()
                norm[key] = name  # keep the nicely cased version
            count = len(norm)
            if count == 0:
                return f"0 companies came for {spec}."
            names = ", ".join(sorted(norm.values()))
            return f"{count} companies came for {spec} — they are: {names}."

        return None
    except Exception as e:
        print(f"⚠️ Specialization guard failed: {e}")
        return None

def route_query(user_question: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Main query routing function with intelligent multi-hop support.
    """
    print(f"🔍 Processing query: {user_question}")

    # Check if this is a multi-hop query
    sub_questions = decompose_multi_hop_query(user_question)

    if len(sub_questions) > 1:
        print(f"🔧 Multi-hop query detected with {len(sub_questions)} steps")
        return execute_multi_hop_query(sub_questions)
    else:
        # Single query
        return route_single_query(user_question, context)

# Legacy functions for backward compatibility
def create_production_agent():
    """Legacy function - now uses advanced LLM router."""
    return None

def create_jd_agent():
    """Legacy function - now uses advanced LLM router."""
    return None

def create_placement_agent():
    """Legacy function - now uses advanced LLM router."""
    return None

def create_final_agent():
    """Legacy function - now uses advanced LLM router."""
    return None
