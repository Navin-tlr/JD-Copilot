"""
Advanced LLM-based Query Router with Custom OpenRouter Integration
Routes queries to structured database or vector search based on user intent.
Uses LlamaIndex's NLSQLTableQueryEngine and intelligent multi-hop decomposition.
"""

import json
import sqlite3
import requests
import time
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, AsyncIterator

from .config import get_settings
from .database import PlacementDatabase
from .rag import retrieve_snippets, synthesize_answer, get_pinecone_index
from .prompts import assemble_prompt, get_banned_patterns

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
                timeout=180,  # Extended per user request (3 minutes)
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
LAST_ROUTE_TYPE: str | None = None
# Holds timing breakdown for last routed query
LAST_TIMINGS: Dict[str, float] = {}

def get_sql_query_engine():
    """Initialize and return the LlamaIndex NLSQLTableQueryEngine."""
    global _sql_query_engine

    init_start = None
    init_duration = 0.0
    if _sql_query_engine is None and LLAMA_INDEX_AVAILABLE:
        init_start = time.perf_counter()
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
                    model=(
                        (settings.OPENROUTER_MODEL if (settings.OPENROUTER_MODEL and "grok" not in settings.OPENROUTER_MODEL.lower()) else "deepseek/deepseek-r1-distill-llama-70b")
                    ),
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
            
            # Custom Text-to-SQL prompt that emphasizes intent understanding and error handling
            text_to_sql_prompt = PromptTemplate(
                """You are an expert at converting natural language questions into SQL queries for a placement database.

DATABASE SCHEMA WITH INTENT MAPPING:
{schema}

CRITICAL RULES:
1.  **Strict Schema Adherence**: Only use the tables and columns provided in the schema. Do not invent columns or assume relationships.
2.  **Intent Mapping**:
    *   **Job Domains** (e.g., Marketing, Finance, HR): Map to `roles.specialization`. These are stored in UPPERCASE. Use `UPPER()` for matching.
    *   **Company Industries** (e.g., Tech, Healthcare): Map to `companies.industry`.
3.  **Counting Companies**: When counting companies for a job domain, you MUST `JOIN roles` to `companies` and `COUNT(DISTINCT companies.id)`.
4.  **Error Condition**: If the user's question CANNOT be answered using the provided schema (e.g., asking for "B2B companies" when there is no 'B2B' category), you MUST return the single phrase **QUERY_ERROR** and nothing else.

EXAMPLES:
*   **User Question**: "How many companies for Finance?"
    *   **SQL**: `SELECT COUNT(DISTINCT c.id) FROM companies c JOIN roles r ON r.company_id = c.id WHERE r.specialization = 'FINANCE'`
*   **User Question**: "list b2b companies"
    *   **SQL**: `QUERY_ERROR`
*   **User Question**: "top 5 paying companies"
    *   **SQL**: `SELECT c.company_name FROM companies c JOIN roles r ON c.id = r.company_id JOIN offers o ON r.id = o.role_id ORDER BY o.salary_max_lpa DESC LIMIT 5`

QUESTION: {query_str}

Generate ONLY the SQL query or QUERY_ERROR. Do not provide any explanation.
"""
            )

            _sql_query_engine = NLSQLTableQueryEngine(
                sql_database=sql_database,
                llm=llm,
                embed_model=embed_model,
                text_to_sql_prompt=text_to_sql_prompt,
                verbose=True
            )

            print("✅ NLSQLTableQueryEngine initialized successfully!")
            if init_start is not None:
                init_duration = (time.perf_counter() - init_start) * 1000.0

        except Exception as e:
            print(f"❌ Failed to initialize SQL query engine: {e}")
            return None
    # Store initialization duration (0 if reused)
    if init_duration:
        # Only record if this call performed initialization
        global LAST_TIMINGS
        LAST_TIMINGS['engine_init_ms'] = init_duration
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
                # INCREASED TOP_K for comprehensive JD analysis - get more snippets for complete information
                snippets = retrieve_snippets(question, top_k=50, filters={})
                answer = synthesize_answer(question, snippets, {})
                class Resp:
                    def __init__(self, text: str):
                        self.response = text
                # CRITICAL FIX: Don't fallback to generic message - use the actual answer
                if answer:
                    return Resp(answer)
                else:
                    return Resp("I could not find relevant information to answer your question based on the available documents.")
            except Exception as e:
                class RespErr:
                    def __init__(self, text: str):
                        self.response = text
                return RespErr(f"I encountered an error in vector retrieval: {e}")

    return PineconeQueryAdapter(index)

QUESTION_STARTERS = (
    "what", "which", "who", "where", "when", "why", "how",
    "is", "are", "do", "does", "did", "can", "could", "would", "should",
    "list", "give", "tell", "show", "provide", "explain"
)

CONNECTOR_SPLIT_PATTERN = re.compile(
    r"\b(?:and|also|plus|then|along with|as well as|besides|additionally)\s+(?=(?:" + "|".join(QUESTION_STARTERS) + r")\b)",
    re.IGNORECASE
)


def decompose_multi_hop_query(user_question: str) -> List[str]:
    """Split a user question into sequenced sub-questions when multiple asks are detected."""
    if not user_question:
        return [user_question]

    text = user_question.strip()
    if not text:
        return [user_question]

    # First pass: explicit question marks
    question_mark_parts = [part.strip(" ,;:") for part in re.split(r"\?\s*", text) if part.strip()]
    sub_questions: List[str] = []
    if len(question_mark_parts) > 1:
        for part in question_mark_parts:
            cleaned = part.rstrip(".;,")
            if not cleaned.endswith("?"):
                cleaned = cleaned + "?"
            sub_questions.append(cleaned)
        if sub_questions:
            print(f"ℹ️ Decomposed query into {len(sub_questions)} sub-questions via question marks.")
            return sub_questions

    # Second pass: connective phrases followed by new interrogative
    connector_parts = [seg.strip(" ,;:") for seg in re.split(CONNECTOR_SPLIT_PATTERN, text) if seg.strip(" ,;:")]
    if len(connector_parts) > 1:
        for part in connector_parts:
            cleaned = part.rstrip(".;,")
            if not cleaned.endswith("?"):
                cleaned = cleaned + "?"
            sub_questions.append(cleaned)
        if sub_questions:
            print(f"ℹ️ Decomposed query into {len(sub_questions)} sub-questions via connectors.")
            return sub_questions

    # Third pass: multiple interrogative starters without connectors or punctuation
    # DISABLED: This pass was too aggressive and incorrectly split single-intent
    # questions containing relative clauses (e.g., "...which will help...").
    # The first two passes (question marks, connectors) are more reliable.
    # starter_pattern = re.compile(r"\b(" + "|".join(QUESTION_STARTERS) + r")\b", re.IGNORECASE)
    # matches = list(starter_pattern.finditer(text))
    # if len(matches) > 1:
    #     segments: List[str] = []
    #     for idx, match in enumerate(matches):
    #         chunk_start = match.start()
    #         chunk_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
    #         chunk = text[chunk_start:chunk_end].strip(" ,;:")

    #         if idx == 0 and chunk_start > 0:
    #             prefix = text[:chunk_start].strip(" ,;:")
    #             if prefix:
    #                 chunk = f"{prefix} {chunk}".strip()

    #         if chunk:
    #             if not chunk.endswith("?"):
    #                 chunk = chunk.rstrip(".;,") + "?"
    #             segments.append(chunk)

    #     if segments:
    #         print(f"ℹ️ Decomposed query into {len(segments)} sub-questions via interrogative starters.")
    #         return segments

    return [text]

def execute_multi_hop_query(sub_questions: List[str]) -> str:
    """Execute a sequence of sub-questions and combine results."""
    results = []
    previous_answers: List[str] = []
    context: Dict[str, Any] = {"previous_answers": previous_answers}

    for i, question in enumerate(sub_questions, 1):
        print(f"🔍 Executing sub-question {i}: {question}")

        # Route each sub-question
        result = route_single_query(question, context)

        # Store result for context
        context[f"step_{i}_result"] = result
        previous_answers.append(result)
        results.append(f"**Step {i}:** {question}\n{result}")

    # Combine all results
    combined = "\n\n".join(results)
    return f"**Multi-question analysis**\n\n{combined}"

def route_single_query(user_question: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Route a single query to the appropriate engine. Captures routing latency."""
    t_start = time.perf_counter()
    settings = get_settings()

    previous_context_text: Optional[str] = None
    if context:
        previews = context.get("previous_answers")
        if isinstance(previews, list) and previews:
            # Keep only the last three snippets to control prompt size
            clipped = [str(p).strip() for p in previews[-3:] if str(p).strip()]
            if clipped:
                previous_context_text = "\n\n".join(clipped)

    # Get database schema for routing decision
    schema = get_database_schema()
    schema_json = json.dumps(schema, indent=2)

    # Enhanced routing prompt with merciless directness
    system_prompt = """You are the Query Router for JD-Copilot. Your sole responsibility is to classify user queries into the correct execution mode so the system can choose the right database(s). You must never fabricate or provide answers yourself.

Tone Guidelines:
- **Merciless Directness**: Be brutally concise. Use imperatives and state facts without softening.
- **Career-Critical Focus**: Frame decisions as make-or-break for career advancement.
- **Eliminate Qualifiers**: Replace "important" with "non-negotiable", "valuable" with "career-critical".
- **Data Grounding**: Base decisions on verifiable patterns, not assumptions.
- **Strategic Metaphors**: Use combat metaphors sparingly but effectively (e.g., "career artillery", "battlefield awareness").

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
    8.	If the user packs multiple distinct questions in one sentence (multiple '?' or phrases like 'and what'), classify as MULTI_HOP so the planner answers every part.

⸻

Response Format

Output only one word:
STRUCTURED, UNSTRUCTURED, HYBRID, or MULTI_HOP"""

    if previous_context_text:
        user_prompt = (
            f"Query: {user_question}\n\n"
            f"Relevant previous context (keep for reference only, do NOT answer):\n{previous_context_text}\n\n"
            f"Database Schema: {schema_json}"
        )
    else:
        user_prompt = f"Query: {user_question}\n\nDatabase Schema: {schema_json}"

    # Use OpenRouter for routing decision
    if settings.OPENROUTER_API_KEY:
        try:
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": settings.OPENROUTER_MODEL or "deepseek/deepseek-r1-distill-llama-70b",
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
                timeout=180,
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

    routing_ms = (time.perf_counter() - t_start) * 1000.0
    print(f"🔍 Routing decision: {routing_decision} (routing_ms={routing_ms:.1f})")
    global LAST_TIMINGS
    LAST_TIMINGS = {'routing_ms': routing_ms}

    # Track routing decision for downstream human-in-loop logic
    global LAST_ROUTE_TYPE
    LAST_ROUTE_TYPE = routing_decision

    # Execute based on routing decision
    if routing_decision == "STRUCTURED":
        return execute_structured_query(user_question)
    elif routing_decision == "UNSTRUCTURED":
        return execute_unstructured_query(user_question)
    elif routing_decision == "HYBRID":
        return execute_hybrid_query(user_question, previous_context=previous_context_text)
    elif routing_decision == "MULTI_HOP":
        # For now, treat MULTI_HOP as HYBRID until we implement proper multi-hop logic
        print("🔧 MULTI_HOP query detected, routing to HYBRID for comprehensive analysis")
        return execute_hybrid_query(user_question, previous_context=previous_context_text)
    else:
        # Default to HYBRID for safety if routing is unclear
        print(f"⚠️ Unclear routing decision '{routing_decision}', defaulting to HYBRID")
        return execute_hybrid_query(user_question, previous_context=previous_context_text)

def _is_no_data_result(result: str) -> bool:
    """Check if result indicates no data was found."""
    no_data_indicators = [
        "0 companies",
        "no companies",
        "unable to provide",
        "query error",
        "no data available",
        "not found",
        "no results",
        "empty result",
        "query_error"
    ]
    result_lower = (result or "").lower()
    if any(indicator in result_lower for indicator in no_data_indicators):
        return True
    # Regex patterns like "no b2b companies", "0 fintech companies"
    if re.search(r"\bno\b[^\n\r\.!?]{0,60}\bcompanies\b", result_lower):
        return True
    if re.search(r"\b0\b[^\n\r\.!?]{0,60}\bcompanies\b", result_lower):
        return True
    return False

def _offer_deep_dive_mode(user_question: str, structured_result: str) -> str:
    """Offer deep-dive mode using unstructured database when structured search returns no data."""
    return f"""{structured_result}

🎯 **DEEP-DIVE MODE AVAILABLE**

The structured database has limited matches for your query. However, I can activate **Deep-Dive Mode** to search through thousands of detailed job descriptions and company profiles for comprehensive analysis.

**Deep-Dive Mode Benefits:**
• Searches actual job description text, not just categories
• Finds hidden opportunities (e.g., "B2B Sales" roles listed as "Business Development")  
• Analyzes company culture, requirements, and detailed role descriptions
• Provides qualitative insights beyond just numbers

**🔑 Do you consent to Deep-Dive Mode?**
Reply with **"yes"** or **"deep-dive"** to proceed with unstructured database analysis.

**⚡ Or ask a different structured query for instant results.**"""

def execute_structured_query(user_question: str) -> str:
    """Execute structured database query with intelligent fallback to unstructured when no data found."""
    print(f"🔍 Executing structured query: {user_question}")
    global LAST_ROUTE_TYPE, LAST_TIMINGS
    LAST_ROUTE_TYPE = "STRUCTURED"

    # Try fast deterministic patterns first
    fast_start = time.perf_counter()
    fast_result = _try_fast_deterministic_query(user_question)
    if fast_result is not None:
        fast_ms = (time.perf_counter() - fast_start) * 1000.0
        LAST_TIMINGS = {
            'fast_deterministic_ms': fast_ms,
            'sql_generation_ms': 0.0,
            'summarization_ms': 0.0,
            'total_ms': fast_ms
        }
        print(f"✅ Fast deterministic answer: {fast_result[:100]}... (fast_ms={fast_ms:.1f})")
        
        # Check if result indicates no data found
        if _is_no_data_result(fast_result):
            return _offer_deep_dive_mode(user_question, fast_result)
        
        return fast_result

    # Fallback to LlamaIndex for complex queries
    engine = get_sql_query_engine()
    if engine:
        try:
            sql_start = time.perf_counter()
            response = engine.query(user_question)
            sql_gen_ms = (time.perf_counter() - sql_start) * 1000.0
            LAST_TIMINGS['sql_generation_ms'] = sql_gen_ms
            
            # Intercept and correct common column mix-up: industry vs specialization
            corrected = _maybe_rewrite_specialization_answer(user_question, response)
            if corrected is not None:
                LAST_TIMINGS['summarization_ms'] = 0.0  # skip summarization path
                LAST_TIMINGS['total_ms'] = sum(v for v in LAST_TIMINGS.values())
                
                # Check if corrected result indicates no data
                if _is_no_data_result(corrected):
                    return _offer_deep_dive_mode(user_question, corrected)
                
                return corrected

            summary_start = time.perf_counter()
            if hasattr(response, 'response'):
                summary = _summarize_sql_with_llm(user_question, response.response)
            else:
                summary = _summarize_sql_with_llm(user_question, str(response))
            summary = _postprocess_specialization_answer(user_question, summary)
            summarization_ms = (time.perf_counter() - summary_start) * 1000.0
            LAST_TIMINGS['summarization_ms'] = summarization_ms
            LAST_TIMINGS['total_ms'] = sum(v for v in LAST_TIMINGS.values())
            
            # Check if final result indicates no data
            if _is_no_data_result(summary):
                return _offer_deep_dive_mode(user_question, summary)
            
            return summary
        except Exception as e:
            print(f"❌ SQL query failed: {e}")
            error_msg = f"Unable to provide the count of companies for B2B sales due to a query error—more details on the SQL and database are needed to resolve it."
            return _offer_deep_dive_mode(user_question, error_msg)
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
            # CRITICAL FIX: Don't fallback to generic message - use the actual answer
            if answer:
                return answer
            else:
                return "I could not find relevant information to answer your question based on the available documents."
        else:
            return "I couldn't find relevant information."

def execute_hybrid_query(user_question: str, previous_context: Optional[str] = None) -> str:
    """Execute hybrid query combining structured and unstructured data into one coherent answer."""
    print(f"🔍 Executing hybrid query: {user_question}")

    structured_result = execute_structured_query(user_question)
    unstructured_result = execute_unstructured_query(user_question)

    contextual_unstructured = unstructured_result or ""
    if previous_context:
        previous_context = previous_context.strip()
        if previous_context:
            contextual_unstructured = (
                contextual_unstructured +
                ("\n\n" if contextual_unstructured else "") +
                "PREVIOUS_STEP_CONTEXT:\n" + previous_context
            )

    # Use LLM to blend both results into one homogeneous solution
    settings = get_settings()

    if not settings.OPENROUTER_API_KEY:
        # Fallback: simple concatenation if no LLM available
        return f"{structured_result}\n\n{contextual_unstructured}"

    synthesis_prompt = assemble_prompt(
        user_question=user_question,
        structured_result=structured_result,
        unstructured_result=contextual_unstructured,
        mode="direct",
        persona="placement_cell",
    )

    try:
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": settings.OPENROUTER_MODEL or "deepseek/deepseek-r1-distill-llama-70b",
            "messages": [
                {
                    "role": "system",
                    "content": "You are the MBA Placement Cell speaking with Linus Torvalds' dry precision. Obey all instructions in the user message without deviation."
                },
                {"role": "user", "content": synthesis_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 2000,
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            synthesized_answer = result["choices"][0]["message"]["content"].strip()
            # Lightweight post-processing guard to reduce residual hallucination/hype
            banned_patterns = get_banned_patterns()
            if any(re.search(p, synthesized_answer) for p in banned_patterns):
                sentences = re.split(r'(?<=[.!?])\s+', synthesized_answer)
                cleaned = [s for s in sentences if not any(re.search(p, s) for p in banned_patterns)]
                cleaned_answer = " ".join(cleaned).strip()
                if cleaned_answer:
                    synthesized_answer = cleaned_answer
            print("✅ Successfully synthesized hybrid response (factual mode)")
            return synthesized_answer
        else:
            print(f"⚠️ OpenRouter synthesis failed: {response.status_code}")
            return f"{structured_result}\n\nAdditional insights: {contextual_unstructured}"

    except Exception as e:
        print(f"⚠️ Hybrid synthesis failed: {e}")
        return f"{structured_result}\n\n{contextual_unstructured}"

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
            "model": settings.OPENROUTER_MODEL or "deepseek/deepseek-r1-distill-llama-70b",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 150,
        }
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=180
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

def _try_fast_deterministic_query(user_question: str) -> Optional[str]:
    """Fast deterministic patterns for common structured queries - 100% accurate, sub-10ms."""
    q = user_question.lower().strip()
    
    # Pattern 1: "how many companies came for <specialization>?"
    match = re.search(r'how many companies.*?came.*?for\s+(\w+)', q)
    if match:
        spec_word = match.group(1)
        spec = _normalize_specialization_word(spec_word)
        if spec:
            return _get_companies_count_for_specialization(spec)

    if re.search(r'how many companies', q) and re.search(r'came|visited|participated', q):
        if any(token in q for token in ['placement', 'placements', 'campus', 'drive']):
            return _get_total_companies_participated()
    
    # Pattern 2: "companies for <specialization>" or "which companies came for <specialization>"
    match = re.search(r'(?:which\s+)?companies.*?for\s+(\w+)', q)
    if match:
        spec_word = match.group(1)
        spec = _normalize_specialization_word(spec_word)
        if spec:
            return _get_companies_list_for_specialization(spec)
    
    # Pattern 3: "list companies" or "show companies" or "all companies"
    if any(phrase in q for phrase in ['list companies', 'show companies', 'all companies']):
        return _get_all_companies_list()
    
    # Pattern 4: "how many roles" or "total roles"
    if any(phrase in q for phrase in ['how many roles', 'total roles', 'number of roles']):
        return _get_total_roles_count()
    
    # Pattern 5: "companies in <location>" or "companies from <location>"
    match = re.search(r'companies\s+(?:in|from)\s+([\w\s]+)', q)
    if match:
        location = match.group(1).strip()
        return _get_companies_by_location(location)
    
    # Pattern 6: "salary" or "salaries" or "packages" - highest/lowest/average
    if any(word in q for word in ['salary', 'salaries', 'package', 'packages', 'ctc']):
        if any(word in q for word in ['highest', 'maximum', 'max', 'top']):
            return _get_highest_salary()
        elif any(word in q for word in ['lowest', 'minimum', 'min']):
            return _get_lowest_salary()
        elif any(word in q for word in ['average', 'avg', 'mean']):
            return _get_average_salary()
        else:
            return _get_salary_overview()
    
    # Pattern 7: "skills" - most common/required
    if 'skills' in q or 'skill' in q:
        if any(word in q for word in ['most', 'top', 'common', 'popular']):
            return _get_top_skills()
        else:
            return _get_skills_overview()
    
    # Pattern 8: "what companies" or "which companies" (general)
    if any(phrase in q for phrase in ['what companies', 'which companies']) and 'for' not in q:
        return _get_all_companies_list()
    
    # Pattern 9: Year-based queries "companies in 2024" or "2024 companies"
    year_match = re.search(r'(?:companies.*?(?:in|for)\s+)?(\d{4})', q)
    if year_match:
        year = year_match.group(1)
        return _get_companies_by_year(year)
    
    return None

def _normalize_specialization_word(word: str) -> Optional[str]:
    """Map user input to canonical specialization."""
    mapping = {
        'finance': 'FINANCE',
        'financial': 'FINANCE',
        'marketing': 'MARKETING',
        'hr': 'HR',
        'human': 'HR',
        'operations': 'OPERATIONS',
        'ops': 'OPERATIONS',
        'strategy': 'STRATEGY',
        'strategic': 'STRATEGY',
        'it': 'IT',
        'tech': 'IT',
        'analytics': 'BUSINESS ANALYTICS',
        'analysis': 'BUSINESS ANALYTICS',
    }
    return mapping.get(word.lower())

def _get_companies_count_for_specialization(spec: str) -> str:
    """Direct DB query for company count by specialization."""
    try:
        db = PlacementDatabase()
        companies = db.get_companies_by_specialization(spec, batch_year=None)
        company_names = set()
        for c in companies:
            name = (c.get("company_name") or "").strip()
            if name:
                company_names.add(name)
        count = len(company_names)
        if count == 0:
            return f"0 companies came for {spec}."
        names = ", ".join(sorted(company_names))
        return f"{count} companies came for {spec} — they are: {names}."
    except Exception as e:
        print(f"❌ Fast specialization count failed: {e}")
        return None

def _get_companies_list_for_specialization(spec: str) -> str:
    """Direct DB query for companies by specialization."""
    try:
        db = PlacementDatabase()
        companies = db.get_companies_by_specialization(spec, batch_year=None)
        company_names = set()
        for c in companies:
            name = (c.get("company_name") or "").strip()
            if name:
                company_names.add(name)
        if not company_names:
            return f"No companies came for {spec}."
        names = ", ".join(sorted(company_names))
        return f"Companies for {spec}: {names}."
    except Exception as e:
        print(f"❌ Fast specialization list failed: {e}")
        return None

def _get_all_companies_list() -> str:
    """Direct DB query for all companies."""
    try:
        db_path = "data/placement_data.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT company_name FROM companies ORDER BY company_name;")
            companies = [row[0] for row in cursor.fetchall()]
        if not companies:
            return "No companies found in the database."
        return f"All companies ({len(companies)}): " + ", ".join(companies) + "."
    except Exception as e:
        print(f"❌ Fast all companies list failed: {e}")
        return None


def _get_total_companies_participated() -> str:
    """Total distinct companies that participated in the placement drives."""
    try:
        db_path = "data/placement_data.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(DISTINCT company_name) FROM companies;")
            total = cursor.fetchone()[0] or 0
            cursor.execute("SELECT DISTINCT company_name FROM companies ORDER BY company_name LIMIT 5;")
            sample = [row[0] for row in cursor.fetchall()]
        if total == 0:
            return "0 companies are recorded in the placement database."
        sample_text = f" Sample recruiters: {', '.join(sample)}." if sample else ""
        return f"{total} companies participated in the placements.{sample_text}"
    except Exception as e:
        print(f"❌ Fast total companies count failed: {e}")
        return None


def _get_total_roles_count() -> str:
    """Direct DB query for total roles count."""
    try:
        db_path = "data/placement_data.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM roles;")
            count = cursor.fetchone()[0]
        return f"Total roles: {count}"
    except Exception as e:
        print(f"❌ Fast roles count failed: {e}")
        return None

def _get_companies_by_location(location: str) -> str:
    """Direct DB query for companies by location (checks both companies and roles tables)."""
    try:
        db_path = "data/placement_data.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Handle Bangalore/Bengaluru equivalency for accuracy
            search_terms = []
            location_lower = location.lower()
            if 'bangalore' in location_lower or 'bengaluru' in location_lower:
                search_terms = ['%bangalore%', '%bengaluru%']
            else:
                search_terms = [f'%{location}%']
            
            # Build dynamic query for all search terms
            where_conditions = []
            params = []
            for term in search_terms:
                where_conditions.append("(UPPER(c.location) LIKE UPPER(?) OR UPPER(r.location) LIKE UPPER(?))")
                params.extend([term, term])
            
            where_clause = " OR ".join(where_conditions)
            
            query = f"""
                SELECT DISTINCT c.company_name
                FROM companies c
                LEFT JOIN roles r ON c.id = r.company_id
                WHERE {where_clause}
                ORDER BY c.company_name;
            """
            
            cursor.execute(query, params)
            companies = [row[0] for row in cursor.fetchall()]
            
        if not companies:
            return f"No companies found in {location}."
        return f"Companies in {location} ({len(companies)}): " + ", ".join(companies) + "."
    except Exception as e:
        print(f"❌ Fast companies by location failed: {e}")
        return None

def _get_highest_salary() -> str:
    """Direct DB query for highest salary."""
    try:
        db_path = "data/placement_data.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MAX(salary_max_lpa), c.company_name, r.title 
                FROM offers o 
                JOIN roles r ON o.role_id = r.id 
                JOIN companies c ON r.company_id = c.id
                WHERE salary_max_lpa IS NOT NULL
            """)
            result = cursor.fetchone()
        if result and result[0]:
            return f"Highest salary: ₹{result[0]} LPA offered by {result[1]} for {result[2]} role."
        return "No salary information available."
    except Exception as e:
        print(f"❌ Fast highest salary failed: {e}")
        return None

def _get_lowest_salary() -> str:
    """Direct DB query for lowest salary."""
    try:
        db_path = "data/placement_data.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MIN(salary_min_lpa), c.company_name, r.title 
                FROM offers o 
                JOIN roles r ON o.role_id = r.id 
                JOIN companies c ON r.company_id = c.id
                WHERE salary_min_lpa IS NOT NULL AND salary_min_lpa > 0
            """)
            result = cursor.fetchone()
        if result and result[0]:
            return f"Lowest salary: ₹{result[0]} LPA offered by {result[1]} for {result[2]} role."
        return "No salary information available."
    except Exception as e:
        print(f"❌ Fast lowest salary failed: {e}")
        return None

def _get_average_salary() -> str:
    """Direct DB query for average salary."""
    try:
        db_path = "data/placement_data.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT AVG(salary_min_lpa), AVG(salary_max_lpa) FROM offers WHERE salary_min_lpa IS NOT NULL AND salary_max_lpa IS NOT NULL;")
            result = cursor.fetchone()
        if result and result[0]:
            avg_min = round(result[0], 1)
            avg_max = round(result[1], 1)
            return f"Average salary range: ₹{avg_min} - ₹{avg_max} LPA"
        return "No salary information available."
    except Exception as e:
        print(f"❌ Fast average salary failed: {e}")
        return None

def _get_salary_overview() -> str:
    """Direct DB query for salary overview."""
    try:
        db_path = "data/placement_data.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MIN(salary_min_lpa), MAX(salary_max_lpa), AVG(salary_min_lpa), AVG(salary_max_lpa), COUNT(*) FROM offers WHERE salary_min_lpa IS NOT NULL;")
            result = cursor.fetchone()
        if result and result[4] > 0:
            min_sal, max_sal, avg_min, avg_max, count = result
            return f"Salary overview ({count} offers): Range ₹{min_sal}-₹{max_sal} LPA, Average ₹{round(avg_min,1)}-₹{round(avg_max,1)} LPA"
        return "No salary information available."
    except Exception as e:
        print(f"❌ Fast salary overview failed: {e}")
        return None

def _get_top_skills() -> str:
    """Direct DB query for top skills with company coverage and specific tool highlights."""
    try:
        db_path = "data/placement_data.db"
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA group_concat_max_len = 100000;")
            cursor = conn.cursor()

            normalize_case = """
                CASE 
                    WHEN UPPER(s.skill_name) LIKE '%EXCEL%' AND UPPER(s.skill_name) NOT LIKE '%EXCELLENT%' THEN 'Excel'
                    WHEN UPPER(s.skill_name) LIKE '%GOOGLE SHEETS%' THEN 'Google Sheets'
                    WHEN UPPER(s.skill_name) LIKE '%COMMUNICATION%' THEN 'Communication Skills'
                    WHEN UPPER(s.skill_name) LIKE '%OFFICE%' THEN 'Microsoft Office Suite'
                    WHEN UPPER(s.skill_name) LIKE '%COLD%' THEN 'Cold Calling & Emailing'
                    WHEN UPPER(s.skill_name) LIKE '%ZOHO BOOKS%' AND s.skill_name NOT LIKE '%Bonus%' THEN 'Zoho Books'
                    WHEN UPPER(s.skill_name) LIKE '%TALLY%' AND s.skill_name NOT LIKE '%Bonus%' THEN 'Tally'
                    WHEN UPPER(s.skill_name) LIKE '%LINKEDIN%' OR UPPER(s.skill_name) LIKE '%SOCIAL MEDIA%' THEN 'Social Media & LinkedIn'
                    WHEN UPPER(s.skill_name) LIKE '%CRM%' THEN 'CRM Tools'
                    ELSE s.skill_name
                END
            """

            top_query = f"""
                WITH normalized AS (
                    SELECT 
                        {normalize_case} AS normalized_skill,
                        c.company_name AS company_name,
                        TRIM(s.skill_name) AS raw_skill
                    FROM skills s
                    JOIN roles r ON s.role_id = r.id
                    JOIN companies c ON r.company_id = c.id
                    WHERE LENGTH(s.skill_name) < 100
                )
                SELECT normalized_skill, COUNT(DISTINCT company_name) AS company_count
                FROM normalized
                GROUP BY normalized_skill
                ORDER BY company_count DESC
                LIMIT 10;
            """

            cursor.execute(top_query)
            top_rows = cursor.fetchall()
            if not top_rows:
                return "No skills data available."

            top_skills = [row[0] for row in top_rows]
            placeholders = ",".join(["?"] * len(top_skills))

            detail_query = f"""
                WITH normalized AS (
                    SELECT 
                        {normalize_case} AS normalized_skill,
                        c.company_name AS company_name,
                        TRIM(s.skill_name) AS raw_skill
                    FROM skills s
                    JOIN roles r ON s.role_id = r.id
                    JOIN companies c ON r.company_id = c.id
                    WHERE LENGTH(s.skill_name) < 100
                )
                SELECT normalized_skill, company_name, raw_skill
                FROM normalized
                WHERE normalized_skill IN ({placeholders})
            """

            cursor.execute(detail_query, top_skills)
            detail_rows = cursor.fetchall()

        detail_map: Dict[str, Dict[str, Any]] = {
            skill: {"count": count, "companies": set(), "raw_skills": defaultdict(set)}
            for skill, count in top_rows
        }

        for normalized_skill, company_name, raw_skill in detail_rows:
            info = detail_map.get(normalized_skill)
            if not info:
                continue
            if company_name:
                info["companies"].add(company_name)
            if raw_skill:
                cleaned = raw_skill.strip()
                if cleaned:
                    info["raw_skills"][cleaned].add(company_name)

        def _format_samples(items: List[str], limit: int = 4) -> str:
            if not items:
                return ""
            ordered = sorted(items)
            if len(ordered) <= limit:
                return ", ".join(ordered)
            return ", ".join(ordered[:limit]) + f", +{len(ordered) - limit} more"

        summary_lines: List[str] = []
        for skill_name, count in top_rows:
            info = detail_map[skill_name]
            company_sample = _format_samples(list(info["companies"]))
            line = f"{skill_name} — {count} companies"
            if company_sample:
                line += f" (e.g., {company_sample})"

            raw_map = info["raw_skills"]
            specifics: List[str] = []
            for raw_skill, companies in sorted(raw_map.items(), key=lambda item: (-len(item[1]), item[0].lower())):
                raw_lower = raw_skill.lower()
                if raw_lower == skill_name.lower():
                    continue
                comp_sample = _format_samples(list(companies), limit=2)
                if comp_sample:
                    specifics.append(f"{raw_skill} ({comp_sample})")
                if len(specifics) >= 3:
                    break

            if specifics:
                line += f". Notable asks: {', '.join(specifics)}"

            summary_lines.append(line)

        summary = "Top skills in demand:\n" + "\n".join(f"- {line}" for line in summary_lines)
        return summary
    except Exception as e:
        print(f"❌ Fast top skills failed: {e}")
        return None

def _get_skills_overview() -> str:
    """Direct DB query for skills overview."""
    try:
        db_path = "data/placement_data.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(DISTINCT skill_name), COUNT(*) FROM skills;")
            unique_skills, total_entries = cursor.fetchone()
        return f"Skills overview: {unique_skills} unique skills across {total_entries} role requirements."
    except Exception as e:
        print(f"❌ Fast skills overview failed: {e}")
        return None

def _get_companies_by_year(year: str) -> str:
    """Direct DB query for companies by batch year."""
    try:
        db_path = "data/placement_data.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT company_name FROM companies WHERE batch_year LIKE ? ORDER BY company_name;", (f"%{year}%",))
            companies = [row[0] for row in cursor.fetchall()]
        if not companies:
            return f"No companies found for year {year}."
        return f"Companies in {year} ({len(companies)}): " + ", ".join(companies) + "."
    except Exception as e:
        print(f"❌ Fast companies by year failed: {e}")
        return None

def _postprocess_specialization_answer(user_question: str, answer: str) -> str:
    """Deterministically validate specialization answers and correct false zero results.

    If the question targets an MBA specialization and the summarized answer claims zero companies
    (or provides no numeric/company evidence) while the DB shows companies, replace with the
    authoritative count + company list.
    """
    try:
        spec = _extract_specialization_from_question(user_question)
        if not spec:
            return answer
        db = PlacementDatabase()
        companies = db.get_companies_by_specialization(spec, batch_year=None)
        normalized: Dict[str, str] = {}
        for c in companies:
            name = (c.get("company_name") or "").strip()
            if name:
                normalized[name.lower()] = name
        count = len(normalized)
        if count == 0:
            return f"0 companies came for {spec}."
        ans_lower = (answer or "").lower()
        has_digit = any(ch.isdigit() for ch in ans_lower)
        mentions_company = any(n in ans_lower for n in normalized.keys())
        claims_zero = "0 companies" in ans_lower or "no companies" in ans_lower
        if claims_zero or (not has_digit and not mentions_company):
            names = ", ".join(sorted(normalized.values()))
            return f"{count} companies came for {spec} — they are: {names}."
        return answer
    except Exception as e:
        print(f"⚠️ Specialization postprocess failed: {e}")
        return answer

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
    # Single query path
    answer = route_single_query(user_question, context)
    if _is_no_data_result(answer) and "DEEP-DIVE" not in (answer or ""):
        print("🛡️ Final guardrail: Forcing deep-dive offer for no-data result.")
        return _offer_deep_dive_mode(user_question, answer)
    return answer

def get_last_timings() -> Dict[str, float]:
    """Return a copy of the last timing measurements."""
    return dict(LAST_TIMINGS)

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
