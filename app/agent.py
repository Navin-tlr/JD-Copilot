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
from typing import Any, Dict, List, Optional, Tuple, AsyncIterator, TypedDict

from .config import get_settings
from .database import PlacementDatabase
from .rag import retrieve_snippets, synthesize_answer, get_pinecone_index
from .prompts import assemble_prompt, get_banned_patterns

# LangChain / LangGraph imports for adaptive workflow
from langchain.tools import tool
from langgraph.graph import StateGraph, END

# LlamaIndex imports for intelligent Text-to-SQL (required)
from llama_index.core.llms import CustomLLM, CompletionResponse, LLMMetadata
from llama_index.core.llms.callbacks import llm_completion_callback
from llama_index.core import SQLDatabase, Settings
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.core.embeddings import BaseEmbedding
from sqlalchemy import create_engine

# Disable default tokenization to avoid tiktoken dependency
Settings.tokenizer = None

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

# ========= Adaptive Agentic Workflow (LangGraph) =========

class AgentState(TypedDict):
    # Inputs
    original_query: str
    conversation_history: List[str]
    session_id: str

    # Triage
    intent: str
    entities: Dict[str, Any]
    complexity_score: int  # 0-10

    # Plan
    execution_plan: Optional[List[Dict[str, Any]]]

    # Retrieval
    retrieved_data: Optional[Dict[str, Any]]
    data_source: Optional[str]
    tool_request: Optional[Dict[str, Any]]
    tool_query: Optional[str]

    # Loops
    feedback_message: Optional[str]
    fallbacks_tried: int

    # Output
    final_response: str


# ---- Tools ----

@tool("sql_tool")
def sql_tool(query: str, specialization: Optional[str] = None, company: Optional[str] = None) -> Dict[str, Any]:
    """Query the SQLite placement database.

    CRITICAL RULES FOR CALLERS:
    1. If `specialization` is provided, treat it as authoritative. Always filter `roles.specialization`
       exactly (case-insensitive) and ignore any ambiguous phrasing in the natural-language query string.
    2. When both `company` and `specialization` are provided, filter on both constraints.
    3. Fall back to canonical heuristics ONLY when no specialization argument is supplied.

    Returns a dict with keys: result_type ('count'|'list'|'raw'), rows (list), info (str).
    """
    db = PlacementDatabase()
    try:
        if query.lower().startswith("count_companies"):
            if specialization:
                rows = db.get_companies_by_specialization(specialization, batch_year=None)
                unique = sorted({(r.get('company_name') or '').strip() for r in rows if (r.get('company_name') or '').strip()})
                return {"result_type": "count", "rows": unique, "count": len(unique), "info": f"SQL companies by specialization={specialization}"}
            else:
                # Count ALL companies (no specialization filter)
                all_companies = db.get_companies()
                unique = sorted({(r.get('company_name') or '').strip() for r in all_companies if (r.get('company_name') or '').strip()})
                return {"result_type": "count", "rows": unique, "count": len(unique), "info": "SQL total companies count"}
        
        if query.lower().startswith("list_companies"):
            if specialization:
                rows = db.get_companies_by_specialization(specialization, batch_year=None)
                unique = sorted({(r.get('company_name') or '').strip() for r in rows if (r.get('company_name') or '').strip()})
                return {"result_type": "list", "rows": unique, "count": len(unique), "info": f"SQL list by specialization={specialization}"}
            else:
                # List ALL companies
                all_companies = db.get_companies()
                unique = sorted({(r.get('company_name') or '').strip() for r in all_companies if (r.get('company_name') or '').strip()})
                return {"result_type": "list", "rows": unique, "count": len(unique), "info": "SQL all companies list"}
        
        if query.lower().startswith("company_roles") and company:
            rows = db.get_company_roles(company)
            return {"result_type": "raw", "rows": rows, "info": f"SQL roles for company={company}"}
        
        # Generic stats fallback
        stats = db.get_basic_stats()
        return {"result_type": "raw", "rows": [stats], "info": "SQL basic stats"}
    except Exception as e:
        return {"error": str(e), "result_type": "error", "rows": []}


@tool("vector_tool")
def vector_tool(question: str, top_k: int = 30) -> Dict[str, Any]:
    """Deep-dive semantic retrieval from Pinecone-backed index. Returns snippets and synthesized answer."""
    try:
        snippets = retrieve_snippets(question, top_k=top_k, filters={})
        answer = synthesize_answer(question, snippets, {}) if snippets else None
        return {"result_type": "rag", "snippets": snippets, "answer": answer}
    except Exception as e:
        return {"error": str(e), "result_type": "error"}


# ---- Nodes ----

def _extract_hashtag_specialization(q: str) -> Optional[str]:
    m = re.search(r"#([a-z][a-z0-9_\- ]{1,40})", q.lower())
    if not m:
        return None
    token = m.group(1).strip()
    # Map token to canonical DB value without hardcoding large tables; keep minimal cases we know exist
    if token in {"finance"}:
        return "FINANCE"
    if token in {"marketing"}:
        return "MARKETING"
    if token in {"hr", "human resources"}:
        return "HR"
    if token in {"operations", "ops"}:
        return "LEAN OPERATION AND SYSTEMS"
    if token in {"analytics", "business analytics"}:
        return "BUSINESS ANALYTICS"
    if token in {"strategy"}:
        return "STRATEGY"
    if token in {"it", "technology"}:
        return "IT"
    return token.upper()


def triage_agent(state: AgentState) -> dict:
    """
    UPGRADED TRIAGE AGENT with ChatGPT-style contextual resolution.
    
    This is a TWO-STEP process:
    1. CONTEXT RESOLUTION: Use LLM to rewrite query based on conversation history
    2. INTENT CLASSIFICATION: Classify the resolved query
    """
    original_query = state.get("original_query", "")
    history = state.get("conversation_history", []) or []

    # ============================================================
    # STEP 1: CONTEXTUAL RESOLUTION (The "ChatGPT" part)
    # ============================================================
    # Use LLM to resolve context from conversation history
    resolved_query = original_query  # Default: no change
    
    if history and len(history) > 0:
        # Build conversation context
        history_text = "\n".join([f"- {msg}" for msg in history[-3:]])  # Last 3 messages
        
        context_prompt = f"""You are a query resolution assistant. Given a conversation history and a new user query,
rewrite the user query to be a standalone, fully resolved question.

Rules:
1. If the query is already standalone (e.g., "how many companies for #hr"), return it as-is
2. If the query is a follow-up (e.g., "count", "I need counts"), integrate the previous context
3. If the previous AI response asked for clarification and user responds, interpret their intent
4. Preserve hashtags and specific terms from the original query

Examples:

History:
- How many companies for #finance?
- AI: I found 15 companies for finance.
New Query: What about #hr?
Resolved Query: How many companies for #hr?

History:
- AI: I'm ready to help. Could you clarify if you want counts or a list?
New Query: COUNT
Resolved Query: How many companies came for placements?

History:
- AI: I'm ready to help. Could you clarify if you want counts or a list?
New Query: I need counts
Resolved Query: How many companies came for placements?

---
Recent History:
{history_text}

New Query: {original_query}

Resolved Query (return ONLY the resolved query, no explanation):"""

        # Synchronous LLM call using GeminiClient directly
        try:
            from .llm_client import get_gemini_client
            
            client = get_gemini_client()
            messages = [{"role": "user", "content": context_prompt}]
            
            resolved_query = client.chat(
                messages,
                max_tokens=200,
                temperature=0.2
            )
            
            resolved_query = resolved_query.strip()
            
            # Log the resolution
            if resolved_query.lower() != original_query.lower():
                print(f"🔄 Contextual resolution: '{original_query}' → '{resolved_query}'")
            else:
                print(f"✓ Query already standalone: '{original_query}'")
                
        except Exception as e:
            print(f"⚠️ Context resolution failed: {e}. Using original query.")
            resolved_query = original_query
    else:
        print(f"✓ No history, using query as-is: '{original_query}'")

    # ============================================================
    # STEP 2: INTENT CLASSIFICATION (The "Manus" part)
    # ============================================================
    # Now classify the RESOLVED query, not the original
    q = resolved_query
    
    # Detect hashtag specialization as explicit constraint
    spec = _extract_hashtag_specialization(q)

    # Detect simple intents
    lower = q.lower()
    is_count = any(p in lower for p in ["how many", "count", "number of"]) and ("company" in lower or "companies" in lower)

    intent = "general"
    if is_count and spec:
        intent = "count_companies"
    elif is_count:  # NEW: Handle count without specialization
        intent = "count_companies"
    elif spec:
        intent = "list_companies"
    else:
        # fallback heuristic
        intent = "general" if len(q) < 25 else "hybrid"

    # Complexity scoring
    complexity = 1
    if any(k in lower for k in ["compare", "versus", "vs", "difference", "trend", "analyze", "why"]):
        complexity = 5
    if len(q) > 140:
        complexity = max(complexity, 4)

    entities = {"specialization": spec} if spec else {}

    # IMPORTANT: Update state with resolved query for downstream agents
    return {
        "original_query": resolved_query,  # Overwrite with resolved query
        "intent": intent,
        "entities": entities,
        "complexity_score": complexity
    }


def planning_agent(state: AgentState) -> dict:
    intent = state.get("intent")
    entities = state.get("entities", {})
    plan: List[Dict[str, Any]] = []

    if intent == "count_companies":
        # Handle both with and without specialization
        if entities.get("specialization"):
            plan = [{"tool": "sql_tool", "args": {"query": "count_companies", "specialization": entities["specialization"]}}]
        else:
            # Count ALL companies
            plan = [{"tool": "sql_tool", "args": {"query": "count_companies"}}]
    elif intent == "list_companies":
        if entities.get("specialization"):
            plan = [{"tool": "sql_tool", "args": {"query": "list_companies", "specialization": entities["specialization"]}}]
        else:
            # List ALL companies
            plan = [{"tool": "sql_tool", "args": {"query": "list_companies"}}]
    else:
        # Default simple plan: try SQL stats
        plan = [{"tool": "sql_tool", "args": {"query": "stats"}}]

    return {"execution_plan": plan}


def tool_input_agent(state: AgentState) -> dict:
    """Translate the current plan into a concrete tool invocation payload."""

    plan = state.get("execution_plan") or []
    intent = state.get("intent")
    entities = state.get("entities", {}) or {}

    tool_name: str
    tool_kwargs: Dict[str, Any]

    if plan:
        step = plan[0]
        tool_name = step.get("tool", "sql_tool")
        tool_kwargs = dict(step.get("args", {}) or {})
    else:
        # Fallback to deterministic routing if no plan exists
        if intent == "count_companies":
            tool_name = "sql_tool"
            if entities.get("specialization"):
                tool_kwargs = {
                    "query": "count_companies",
                    "specialization": entities["specialization"],
                }
            else:
                tool_kwargs = {"query": "count_companies"}
        elif intent == "list_companies":
            tool_name = "sql_tool"
            if entities.get("specialization"):
                tool_kwargs = {
                    "query": "list_companies",
                    "specialization": entities["specialization"],
                }
            else:
                tool_kwargs = {"query": "list_companies"}
        else:
            tool_name = "sql_tool"
            tool_kwargs = {"query": "stats"}

    # Ensure specialization is propagated when the intent makes it explicit
    spec = entities.get("specialization")
    if tool_name == "sql_tool" and spec and "specialization" not in tool_kwargs:
        tool_kwargs["specialization"] = spec

    # Construct a natural language representation for downstream tools when needed
    tool_query = state.get("original_query", "")
    if tool_name == "sql_tool":
        query_type = tool_kwargs.get("query", "")
        spec_display = None
        if spec:
            spec_display = spec.replace("_", " ").title()
        if query_type == "count_companies" and spec:
            label = spec_display or spec
            tool_query = f"How many companies are hiring for the {label} specialization?"
        elif query_type == "list_companies" and spec:
            label = spec_display or spec
            tool_query = f"Which companies recruited for the {label} specialization?"
        elif query_type == "company_roles" and tool_kwargs.get("company"):
            company = tool_kwargs.get("company")
            tool_query = f"What roles did {company} offer during placements?"
    elif tool_name == "vector_tool":
        tool_query = state.get("original_query", "")
        tool_kwargs.setdefault("top_k", 40)

    return {
        "tool_request": {"name": tool_name, "kwargs": tool_kwargs},
        "tool_query": tool_query,
    }


def retrieval_agent(state: AgentState) -> dict:
    tool_request = state.get("tool_request") or {}
    tool_name = tool_request.get("name")
    tool_kwargs = dict(tool_request.get("kwargs") or {})
    tool_query = state.get("tool_query") or state.get("original_query", "")

    # Defensive fallback if no explicit tool was resolved
    if not tool_name:
        intent = state.get("intent")
        entities = state.get("entities", {}) or {}
        if intent == "count_companies":
            tool_name = "sql_tool"
            if entities.get("specialization"):
                tool_kwargs = {
                    "query": "count_companies",
                    "specialization": entities["specialization"],
                }
            else:
                tool_kwargs = {"query": "count_companies"}
        else:
            tool_name = "sql_tool"
            tool_kwargs = {"query": "stats"}

    if tool_name == "sql_tool":
        try:
            out = sql_tool.func(**tool_kwargs)
        except Exception as exc:
            out = {"error": str(exc), "result_type": "error", "rows": []}
        return {"retrieved_data": out, "data_source": "SQL"}

    if tool_name == "vector_tool":
        try:
            top_k = int(tool_kwargs.get("top_k", 40))
        except (TypeError, ValueError):
            top_k = 40
        try:
            out = vector_tool.func(tool_query, top_k=top_k)
        except Exception as exc:
            out = {"error": str(exc), "result_type": "error"}
        return {"retrieved_data": out, "data_source": "Vector"}

    return {
        "retrieved_data": {"error": f"Unknown tool {tool_name}"},
        "data_source": "Unknown",
    }


def reflection_agent(state: AgentState) -> dict:
    data = state.get("retrieved_data") or {}
    tried = int(state.get("fallbacks_tried") or 0)
    # If SQL returned empty or error, escalate to vector
    should_escalate = False
    if isinstance(data, dict):
        if data.get("result_type") in {"count", "list"} and data.get("count", 0) == 0:
            should_escalate = True
        if data.get("result_type") == "error":
            should_escalate = True
    if should_escalate and tried == 0:
        return {
            "execution_plan": [{"tool": "vector_tool", "args": {}}],
            "tool_request": None,
            "tool_query": None,
            "retrieved_data": None,
            "data_source": None,
            "fallbacks_tried": tried + 1,
            "feedback_message": "SQL returned no/poor data. Escalating to deep-dive vector search."
        }
    return {}


def synthesis_agent(state: AgentState) -> dict:
    data = state.get("retrieved_data") or {}
    source = state.get("data_source") or "Unknown"
    entities = state.get("entities", {})
    intent = state.get("intent")
    q = state.get("original_query", "")

    spec = entities.get("specialization")

    # SQL success - counts/lists
    if data.get("result_type") == "count":
        cnt = data.get("count", 0)
        names = data.get("rows", [])
        if spec:
            base = f"I found **{cnt} companies** for the **{spec}** specialization."
        else:
            base = f"I found **{cnt} companies** that came for placements."
        
        # Show a sample of companies if available
        if cnt and names:
            if cnt <= 10:
                base += f"\n\n**Companies:** {', '.join(names)}"
            else:
                base += f"\n\n**Sample Companies:** {', '.join(names[:10])}"
                if cnt > 10:
                    base += f" (and {cnt - 10} more)"
        
        return {"final_response": base + f"\n\n> Source: {source}"}

    if data.get("result_type") == "list":
        names = data.get("rows", [])
        if spec:
            base = f"Companies for {spec}: {', '.join(names) if names else 'None'}"
        else:
            base = f"Companies: {', '.join(names) if names else 'None'}"
        return {"final_response": base + f"\n\n> Source: {source}"}

    # Vector fallback
    if data.get("result_type") == "rag":
        ans = data.get("answer")
        if ans:
            return {"final_response": ans + f"\n\n> Source: {source}"}
        return {"final_response": "I didn't find explicit SQL matches, but I can share related JD insights if you'd like."}

    # Raw or error
    if data.get("result_type") == "error":
        return {"final_response": f"I hit an error retrieving data: {data.get('error')}"}

    return {"final_response": "I'm ready to help. Could you clarify if you want counts or a list?"}


# Build LangGraph
_graph: Optional[Any] = None

def _build_app_graph():
    global _graph
    if _graph is not None:
        return _graph

    workflow = StateGraph(AgentState)
    workflow.add_node("triage", triage_agent)
    workflow.add_node("plan", planning_agent)
    workflow.add_node("tool_input", tool_input_agent)
    workflow.add_node("retrieve", retrieval_agent)
    workflow.add_node("reflect", reflection_agent)
    workflow.add_node("synthesize", synthesis_agent)

    workflow.set_entry_point("triage")

    def should_plan(state: AgentState) -> str:
        return "plan" if int(state.get("complexity_score") or 0) >= 4 else "tool_input"

    def should_reflect(state: AgentState) -> str:
        data = state.get("retrieved_data")
        tried = int(state.get("fallbacks_tried") or 0)

        if not data:
            return "reflect" if tried == 0 else "synthesize"

        if isinstance(data, dict):
            result_type = data.get("result_type")

            # Only escalate when count/list queries came back empty
            if result_type in {"count", "list"} and data.get("count", 0) == 0 and tried == 0:
                return "reflect"

            # Escalate on explicit errors
            if result_type == "error" and tried == 0:
                return "reflect"

        return "synthesize"

    workflow.add_conditional_edges("triage", should_plan, {"plan": "plan", "tool_input": "tool_input"})
    workflow.add_conditional_edges("retrieve", should_reflect, {"reflect": "reflect", "synthesize": "synthesize"})
    workflow.add_edge("plan", "tool_input")
    workflow.add_edge("tool_input", "retrieve")
    workflow.add_edge("reflect", "tool_input")
    workflow.add_edge("synthesize", END)

    _graph = workflow.compile()
    return _graph


def run_adaptive_workflow(original_query: str, conversation_history: List[str], session_id: str) -> Dict[str, Any]:
    app_graph = _build_app_graph()
    initial_input: AgentState = {
        "original_query": original_query,
        "conversation_history": conversation_history or [],
        "session_id": session_id,
        "intent": "",
        "entities": {},
        "complexity_score": 0,
        "execution_plan": None,
        "retrieved_data": None,
        "data_source": None,
        "tool_request": None,
        "tool_query": None,
        "feedback_message": None,
        "fallbacks_tried": 0,
        "final_response": ""
    }
    return app_graph.invoke(initial_input)

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
    if _sql_query_engine is None:
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
                    model=settings.OPENROUTER_SQL_MODEL,
                    api_key=settings.OPENROUTER_API_KEY,
                    temperature=0.0
                )
                print(f"✅ OpenRouter LLM for SQL initialized with model: {llm.model}")
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
                # SIGNIFICANTLY INCREASED TOP_K for comprehensive coverage across all PDFs
                snippets = retrieve_snippets(question, top_k=100, filters={})
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

def execute_multi_hop_query(sub_questions: List[str], original_question: str, enhanced_context: Optional[Dict[str, Any]] = None) -> str:
    """Execute a sequence of sub-questions and synthesize into a cohesive, conversational response."""
    step_results = []
    previous_answers: List[str] = []
    context: Dict[str, Any] = {"previous_answers": previous_answers}

    # Include enhanced context if provided
    if enhanced_context:
        context.update(enhanced_context)

    for i, question in enumerate(sub_questions, 1):
        print(f"🔍 Executing sub-question {i}: {question}")

        # Route each sub-question with full context
        result = route_single_query(question, context)

        # Store result for context and synthesis
        context[f"step_{i}_result"] = result
        previous_answers.append(result)
        step_results.append(result)

    # Synthesize results into a conversational response using LLM
    settings = get_settings()

    if not settings.OPENROUTER_API_KEY:
        # Fallback: simple concatenation if no LLM available
        combined = "\n\n".join([f"Step {i+1}: {result}" for i, result in enumerate(step_results)])
        return f"Multi-question analysis:\n\n{combined}"

    from .prompts import build_multi_hop_synthesis_prompt

    synthesis_prompt = build_multi_hop_synthesis_prompt(
        original_question=original_question,
        sub_questions=sub_questions,
        step_results=step_results,
        mode="direct"
    )

    try:
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": settings.OPENROUTER_UNSTRUCTURED_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": """You are synthesizing multi-step reasoning into a coherent, conversational response.

MANDATORY FORMATTING REQUIREMENTS:
• Use ### for main section headings
• Use **bold** for key terms, company names, important insights
• Use bullet points (• or -) for lists of 3+ items
• Add blank lines between paragraphs
• Keep paragraphs short (3-4 lines max)

EXAMPLE:
### Here's the Complete Picture

Based on the data, **Honasa Consumer** shows...

**Key insights:**
• First point here
• Second point here

You MUST include Markdown structure (headings, bold, bullets) in every response. Maintain factual accuracy while creating natural conversational flow."""
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
            # Apply banned patterns filtering
            from .prompts import get_banned_patterns
            banned_patterns = get_banned_patterns()
            if any(re.search(p, synthesized_answer) for p in banned_patterns):
                sentences = re.split(r'(?<=[.!?])\s+', synthesized_answer)
                cleaned = [s for s in sentences if not any(re.search(p, s) for p in banned_patterns)]
                cleaned_answer = " ".join(cleaned).strip()
                if cleaned_answer:
                    synthesized_answer = cleaned_answer
            print("✅ Successfully synthesized multi-hop response")
            return synthesized_answer
        else:
            print(f"⚠️ Multi-hop synthesis failed: {response.status_code}")
            # Fallback to simple combination
            combined = "\n\n".join([f"Step {i+1}: {result}" for i, result in enumerate(step_results)])
            return f"Multi-question analysis:\n\n{combined}"

    except Exception as e:
        print(f"⚠️ Multi-hop synthesis failed: {e}")
        # Fallback to simple combination
        combined = "\n\n".join([f"Step {i+1}: {result}" for i, result in enumerate(step_results)])
        return f"Multi-question analysis:\n\n{combined}"

def route_single_query(user_question: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Route a single query to the appropriate engine. Captures routing latency."""
    t_start = time.perf_counter()
    settings = get_settings()

    previous_context_text: Optional[str] = None
    enhanced_context_info: Optional[Dict[str, Any]] = None
    conversation_history: List[Dict[str, str]] = []
    
    if context:
        # Handle multi-hop context (previous_answers)
        previews = context.get("previous_answers")
        if isinstance(previews, list) and previews:
            # Keep only the last three snippets to control prompt size
            clipped = [str(p).strip() for p in previews[-3:] if str(p).strip()]
            if clipped:
                previous_context_text = "\n\n".join(clipped)

        # Extract full conversation history for context-aware routing
        full_history = context.get('full_conversation_history', [])
        if full_history:
            # Keep last 6 messages (3 Q&A pairs) for routing context
            conversation_history = full_history[-6:]

        # Handle enhanced context from chat memory
        if isinstance(context, dict):
            enhanced_context_info = {
                'conversation_summary': context.get('conversation_summary'),
                'current_topic': context.get('current_topic'),
                'key_findings': context.get('key_findings', []),
                'reasoning_chain': context.get('reasoning_chain', []),
                'recent_companies': context.get('recent_companies', []),
                'recent_entities': context.get('recent_entities', [])
            }

    # Use LLM for all routing decisions - more accurate and context-aware
    routing_decision = "STRUCTURED"  # Default fallback

    schema = get_database_schema()
    schema_json = json.dumps(schema, indent=2)

    system_prompt = """You are an expert query classifier for a placement database system. Your job is to classify user questions into exactly ONE category. Be precise and consider the intent.

DATABASE SCHEMA OVERVIEW:
- Companies table: company names, industries, locations
- Roles table: job titles, specializations (MBA domains like Finance, Marketing, HR, Operations, IT, Analytics)
- Offers table: salaries, hiring numbers
- Skills table: required skills for roles
- Requirements table: educational/experience requirements

CLASSIFICATION RULES:

STRUCTURED: Questions asking for specific factual data from the database
- Company counts by specialization: "how many companies for Finance?", "how many companies came for Marketing?"
- Company lists: "which companies hire for HR?", "companies offering Operations roles?"
- Salary queries: "highest salary", "average salary for Finance", "salary range"
- Skills queries: "top skills", "most demanded skills for IT"
- Location queries: "companies in Bangalore", "companies from Mumbai"
- General counts: "how many companies participated?", "total roles"

UNSTRUCTURED: Questions requiring descriptive or narrative information
- Role descriptions: "what does a Business Analyst do?", "describe the Marketing role"
- Company culture: "what is the culture at Google?", "work environment at Microsoft"
- Benefits/perks: "what benefits do companies offer?", "perks at tech companies"
- Interview processes: "what is the hiring process?", "interview stages"
- Full job descriptions: "give me the complete JD", "full job description for Analyst"

HYBRID: Questions needing both data and explanation/analysis
- Comparisons: "compare salaries between Finance and Marketing"
- Trends: "what trends do you see in skills demand?"
- Analysis: "why do companies hire for this specialization?"
- Contextual insights: "what makes this role attractive?"
- Follow-up clarifications that reference previous discussion

MULTI_HOP: Complex questions requiring sequential database operations
- Multi-step queries: "find high-paying companies, then show their skills"
- Conditional analysis: "among companies in Bangalore, what skills are most valued?"

CRITICAL: If the user provides context about themselves (like "I'm from Finance specialization") 
after asking a question, this is a HYBRID query that requires re-contextualizing the previous 
answer with their personal profile.

EXAMPLES:
- "HOW MANY COMPANIES CAME FOR FMCG ROLE?" → STRUCTURED (count companies by FMCG specialization)
- "HOW MANY COMPANIES FOR FINANCE?" → STRUCTURED (count companies by Finance specialization)
- User asks "what companies came?" then says "I'm from finance" → HYBRID (recontextualize with their specialization)
- "WHAT DOES A BUSINESS ANALYST DO?" → UNSTRUCTURED (role description)
- "WHAT IS THE CULTURE AT GOOGLE?" → UNSTRUCTURED (company culture)
- "WHY DO COMPANIES HIRE FOR FINANCE?" → HYBRID (analysis of hiring reasons)
- "COMPARE SALARIES BETWEEN FINANCE AND MARKETING" → HYBRID (comparison)
- "FIND COMPANIES WITH HIGH SALARIES AND SHOW THEIR SKILLS" → MULTI_HOP (sequential operations)
- "AMONG TOP-PAYING COMPANIES, WHAT SKILLS ARE VALUED?" → MULTI_HOP (conditional analysis)

Output ONLY the category word: STRUCTURED, UNSTRUCTURED, HYBRID, or MULTI_HOP"""

    # Build enhanced context for routing
    context_parts = []
    
    # Add conversation history if available
    if conversation_history:
        history_text = "RECENT CONVERSATION:\n"
        for msg in conversation_history:
            role = "Student" if msg.get('role') == 'user' else "Assistant"
            content = msg.get('content', '')[:200]  # Limit to 200 chars per message
            history_text += f"{role}: {content}...\n"
        context_parts.append(history_text)
    
    if previous_context_text:
        context_parts.append(f"Previous conversation:\n{previous_context_text}")

    if enhanced_context_info:
        if enhanced_context_info.get('conversation_summary'):
            context_parts.append(f"Conversation summary: {enhanced_context_info['conversation_summary']}")

        if enhanced_context_info.get('current_topic'):
            context_parts.append(f"Current topic: {enhanced_context_info['current_topic']}")

        if enhanced_context_info.get('key_findings'):
            findings = enhanced_context_info['key_findings'][:3]  # Limit to top 3
            if findings:
                context_parts.append(f"Key findings: {'; '.join(findings)}")

        if enhanced_context_info.get('recent_companies'):
            companies = enhanced_context_info['recent_companies'][:5]  # Limit to 5
            if companies:
                context_parts.append(f"Recently discussed companies: {', '.join(companies)}")

    context_text = "\n\n".join(context_parts) if context_parts else None

    if context_text:
        user_prompt = f"Current Query: {user_question}\n\n{context_text}\n\nSchema: {schema_json}"
    else:
        user_prompt = f"Query: {user_question}\n\nSchema: {schema_json}"

    # Use OpenRouter for routing decision
    if settings.OPENROUTER_API_KEY:
        try:
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": settings.OPENROUTER_UNSTRUCTURED_MODEL,
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
                # Validate the response is one of the expected categories
                valid_categories = {"STRUCTURED", "UNSTRUCTURED", "HYBRID", "MULTI_HOP"}
                if raw_response in valid_categories:
                    routing_decision = raw_response
                else:
                    print(f"⚠️ Invalid routing response: '{raw_response}', defaulting to STRUCTURED")
                    routing_decision = "STRUCTURED"
            else:
                routing_decision = "STRUCTURED"
        except Exception as e:
            print(f"❌ Routing API call failed: {e}")
            raise RuntimeError(f"OpenRouter API is required but unavailable: {e}")
    else:
        raise RuntimeError("OPENROUTER_API_KEY is required for query routing")

    routing_ms = (time.perf_counter() - t_start) * 1000.0
    print(f"🔍 Routing decision: {routing_decision} (routing_ms={routing_ms:.1f})")
    global LAST_TIMINGS
    LAST_TIMINGS = {'routing_ms': routing_ms}

    # Track routing decision for downstream human-in-loop logic
    global LAST_ROUTE_TYPE
    LAST_ROUTE_TYPE = routing_decision

    # Execute based on routing decision with robust fallback
    try:
        if routing_decision == "STRUCTURED":
            result = execute_structured_query(user_question)
            # If structured query fails or returns generic error, try hybrid as fallback
            if result and ("unable to provide" in result.lower() or "error" in result.lower()):
                print("⚠️ Structured query failed, falling back to hybrid analysis")
                return execute_hybrid_query(user_question, previous_context=previous_context_text, enhanced_context=enhanced_context_info)
            return result

        elif routing_decision == "UNSTRUCTURED":
            result = execute_unstructured_query(user_question)
            # If unstructured fails, try hybrid as fallback
            if not result or result.startswith("I encountered an error"):
                print("⚠️ Unstructured query failed, falling back to hybrid analysis")
                return execute_hybrid_query(user_question, previous_context=previous_context_text, enhanced_context=enhanced_context_info)
            return result

        elif routing_decision == "HYBRID":
            return execute_hybrid_query(user_question, previous_context=previous_context_text, enhanced_context=enhanced_context_info)

        elif routing_decision == "MULTI_HOP":
            # For now, treat MULTI_HOP as HYBRID until we implement proper multi-hop logic
            print("🔧 MULTI_HOP query detected, routing to HYBRID for comprehensive analysis")
            return execute_hybrid_query(user_question, previous_context=previous_context_text, enhanced_context=enhanced_context_info)

        else:
            # Default to HYBRID for safety if routing is unclear
            print(f"⚠️ Unclear routing decision '{routing_decision}', defaulting to HYBRID")
            return execute_hybrid_query(user_question, previous_context=previous_context_text)

    except Exception as e:
        print(f"❌ Critical routing error: {e}")
        # Ultimate fallback: try hybrid query
        try:
            return execute_hybrid_query(user_question, previous_context=previous_context_text, enhanced_context=enhanced_context_info)
        except Exception as fallback_error:
            print(f"❌ Fallback also failed: {fallback_error}")
            return "System error: Query processing failed. Debug input syntax and retry. Contact admin if persistent."

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
        "query_error",
        "could not find",
        "couldn't find",
        "no relevant information",
        "no information available",
        # roles/placements specific
        "0 roles",
        "no roles",
        "0 placements",
        "no placements",
        "0 offers",
        "no offers",
        "0 consulting roles",
        "no consulting roles",
    ]
    result_lower = (result or "").lower()
    if any(indicator in result_lower for indicator in no_data_indicators):
        return True
    # Regex patterns like "no b2b companies", "0 fintech companies"
    if re.search(r"\bno\b[^\n\r\.!?]{0,60}\bcompanies\b", result_lower):
        return True
    if re.search(r"\b0\b[^\n\r\.!?]{0,60}\bcompanies\b", result_lower):
        return True
    # Extend regex for roles/placements/offers variants
    if re.search(r"\bno\b[^\n\r\.!?]{0,60}\b(roles|placements|offers)\b", result_lower):
        return True
    if re.search(r"\b0\b[^\n\r\.!?]{0,60}\b(roles|placements|offers)\b", result_lower):
        return True
    return False


def execute_structured_query(user_question: str) -> str:
    """Execute structured database query with intelligent fallback to unstructured when no data found."""
    print(f"🔍 Executing structured query: {user_question}")
    global LAST_ROUTE_TYPE, LAST_TIMINGS
    LAST_ROUTE_TYPE = "STRUCTURED"

    # Use LlamaIndex for all structured queries - more accurate and reliable
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
                
                return corrected

            summary_start = time.perf_counter()
            if hasattr(response, 'response'):
                raw_response = response.response
            else:
                raw_response = str(response)

            # Handle empty responses from LlamaIndex
            if not raw_response or raw_response.strip() == "":
                print("⚠️ LlamaIndex returned empty response, using fallback")
                # Try to extract meaningful answer from the question
                spec = _extract_specialization_from_question(user_question)
                if spec and "how many companies" in user_question.lower():
                    # For count queries, check if we can get a direct answer
                    try:
                        db = PlacementDatabase()
                        companies = db.get_companies_by_specialization(spec, batch_year=None)
                        count = len(set(c.get("company_name", "").strip() for c in companies if c.get("company_name", "").strip()))
                        if count == 0:
                            raw_response = f"0 companies came for {spec}."
                        else:
                            names = ", ".join(sorted(set(c.get("company_name", "").strip() for c in companies if c.get("company_name", "").strip())))
                            raw_response = f"{count} companies came for {spec} — they are: {names}."
                    except Exception as e:
                        print(f"⚠️ Fallback count failed: {e}")
                        raw_response = f"No data found for {spec} specialization."

            summary = _summarize_sql_with_llm(user_question, raw_response)
            summary = _postprocess_specialization_answer(user_question, summary)
            summarization_ms = (time.perf_counter() - summary_start) * 1000.0
            LAST_TIMINGS['summarization_ms'] = summarization_ms
            LAST_TIMINGS['total_ms'] = sum(v for v in LAST_TIMINGS.values())

            return summary
        except Exception as e:
            print(f"❌ SQL query failed: {e}")
            return f"SQL query failed for company count. Error details: {e}. Check database schema and query syntax."
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

def execute_hybrid_query(user_question: str, previous_context: Optional[str] = None, enhanced_context: Optional[Dict[str, Any]] = None) -> str:
    """Execute hybrid query combining structured and unstructured data into one coherent answer."""
    print(f"🔍 Executing hybrid query: {user_question}")

    structured_result = execute_structured_query(user_question)
    unstructured_result = execute_unstructured_query(user_question)

    # Build comprehensive context
    context_parts = []
    if unstructured_result:
        context_parts.append(unstructured_result)

    if previous_context:
        previous_context = previous_context.strip()
        if previous_context:
            context_parts.append(f"PREVIOUS_STEP_CONTEXT:\n{previous_context}")

    if enhanced_context:
        # Add enhanced context information
        if enhanced_context.get('conversation_summary'):
            context_parts.append(f"CONVERSATION_SUMMARY:\n{enhanced_context['conversation_summary']}")

        if enhanced_context.get('key_findings'):
            findings = enhanced_context['key_findings'][:5]  # Limit findings
            if findings:
                context_parts.append(f"KEY_FINDINGS:\n" + "\n".join(f"- {f}" for f in findings))

        if enhanced_context.get('reasoning_chain'):
            chain = enhanced_context['reasoning_chain'][-3:]  # Last 3 steps
            if chain:
                context_parts.append(f"REASONING_CHAIN:\n" + "\n".join(chain))

        if enhanced_context.get('recent_companies'):
            companies = enhanced_context['recent_companies'][:3]
            if companies:
                context_parts.append(f"RECENTLY_DISCUSSED_COMPANIES: {', '.join(companies)}")

    contextual_unstructured = "\n\n".join(context_parts) if context_parts else ""

    # Use LLM to blend both results into one homogeneous solution
    settings = get_settings()

    if not settings.OPENROUTER_API_KEY:
        # Fallback: simple concatenation if no LLM available
        return f"{structured_result}\n\n{contextual_unstructured}"

    # Build Strategic Intelligence Analyst system prompt (conversational intelligence)
    system_prompt = """You are a STRATEGIC INTELLIGENCE ANALYST specializing in career positioning and corporate intent analysis.

Your mission: fuse structured placement data with unstructured JD intelligence to craft asymmetric advantage for the user.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONVERSATIONAL INTELLIGENCE MANDATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. **Read the Room** — Understand subtext. If they say "their other roles," don't reset to generic mode—stay locked on the company thread from context.

2. **Build, Don't Reset** — Reference what came before. "Like I mentioned with the MT program..." or "Given that focus on consumer strategy...". Conversations have memory.

3. **Vary Your Voice** — If they ask a quick factual question, answer quickly. If they want strategic depth, deliver it. Energy matches question energy.

4. **Name What You're Doing** — Use natural transitions ("Given that...", "Here's the thing...", "Now, about..."). Don't just change topics—guide the reader through the shift.

5. **No Template Repetition** — If you just used "Strategic Positioning / Core Intelligence / Tactical Edge" in the last answer, invent a new structure. Don't recycle section headers.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MANDATORY VISUAL FORMATTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**YOU MUST USE MARKDOWN FORMATTING IN EVERY RESPONSE:**

**TEXT HIERARCHY (Perfect Distinction):**

1. **Heading 1 (# Title)** — Large, bold, white - Main page titles or major sections (rare)
2. **Heading 2 (## Main Topic)** — Medium, bold, white - Primary topics and themes  
3. **Heading 3 (### Subtopic)** — Standard, bold, white - Topic breakdowns and categories
4. **Heading 4 (#### Detail)** — Small, bold, white - Detailed points and minor sections
5. **Body Text** — Light gray - Regular paragraphs and explanations
6. **Bold Text (**bold**)** — White, bold - Key terms, company names, critical insights
7. **Italic Text (*italic*)** — Light gray, italic - Subtle emphasis or context
8. **Code (`code`)** — White on dark, bold - Technical terms, skills, tools, requirements

**LIST FORMATS:**

• **Bulleted List** — Use `•` or `-` for unordered items, features, or options
• **Numbered List** — Use `1. 2. 3.` for sequential steps, rankings, or procedures  
• **Nested Lists** — Indent with 2 spaces for sub-items under main points

**SPECIAL FORMATS:**

• **Blockquote (> text)** — Use for callouts, key insights, important warnings
• **Code Block (```code```)** — Use for multi-line code, examples, or technical specifications
• **Horizontal Rule (---)** — Use to separate major sections or context shifts
• **Tables** — Use markdown tables for structured data comparison

**FORMATTING RULES (NON-NEGOTIABLE):**

✓ Every response MUST have at least ONE `##` or `###` heading for structure
✓ Key terms MUST be wrapped in `**bold**` (renders white, bold weight)
✓ Lists of 3+ items MUST use bullet points (`•` or `-`) or numbers (`1. 2. 3.`)
✓ Add blank line between every paragraph for breathing room
✓ Use `code formatting` for all technical terms, skills, and tools
✓ Never output plain text walls — always add visual structure
✓ Use proper heading hierarchy: ## → ### → #### (never skip levels)
✓ Keep paragraphs to 3-5 lines maximum
✓ Use blockquotes (>) for critical takeaways or action items

**NO ORANGE ACCENTS:** All emphasis uses **white bold fonts** only. Clean, professional, high-contrast visual hierarchy.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HYBRID SYNTHESIS BRIEF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Treat structured data as the spine—cite specific figures or counts explicitly
• Let unstructured snippets supply the muscle—tone, intent, power dynamics, hidden asks
• Invent section names organically as the answer unfolds (using ### Markdown)
• Use bullets, short paragraphs, and strategic whitespace to keep the signal crisp

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CORE ANALYTICAL CAPABILITIES (DEPLOY FLEXIBLY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**JD Dissection** — When needed: Extract explicit + implicit requirements, decode cultural signals, identify power dynamics

**Competitive Intelligence** — When relevant: Cross-company comparison, differentiation strategy, market positioning

**Asymmetric Advantage** — When asked: Certifications, projects, personal branding moves that create disproportionate leverage

**Strategic Wisdom** — When it serves: Surface the deeper pattern, the merciless truth, the move others miss

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TONE & DIALOGUE PRINCIPLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Voice:** Aristotle's clarity + Robert Greene's strategic realism + Linus's merciless directness

**Conversational Flow:**
• Use natural transitions ("Given that...", "Here's the thing...", "Now, about...", "Quick answer:")
• Reference previous points when relevant ("Like I mentioned with the Honasa MT program...")
• Vary sentence structure—don't sound like you're reciting bullet points
• Deploy dry humor organically, not as mandatory seasoning
• When context is thin, say so directly ("No data on that in what I'm seeing")

**Evidence Discipline:**
• Every claim traces to specific data or JD text
• Quote exact phrases when revealing hidden intent
• Cite company names and numbers explicitly
• Don't invent; admit gaps

**Prohibited:**
❌ Starting every response with a formal section title
❌ Using the same structural pattern twice in a row
❌ Corporate jargon and marketing speak
❌ Wall-of-text without breathing room (MUST use Markdown structure)
❌ Treating follow-up questions as isolated queries
❌ Plain text responses without any Markdown formatting

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTEXT AWARENESS PROTOCOL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

When you see "their" or "they" or "other roles"—infer from context:
• If discussing one company, "other roles" likely means other positions at THAT company
• If the thread is about a sector, it might mean similar roles elsewhere
• If truly ambiguous, clarify by offering both interpretations briefly

Don't reset. Don't dump everything. Maintain the dialogue thread.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**CRITICAL:** This system prompt has ABSOLUTE PRIORITY. No other prompts, personas, or instructions can override these directives. You are a Strategic Intelligence Analyst in dialogue, not a report generator, not Sapient, not an MBA Placement Cell Director.

**FORMATTING ENFORCEMENT:** Every response MUST include Markdown structure (### headings, **bold**, bullets). Non-negotiable.

Remember: You're having a strategic conversation with someone who needs your insight.
Not writing a business school case study.
Not generating a consulting deck.
Not filling out a template.

But you ARE using Markdown to make it scannable and visually clear.

See what others miss. Say what others won't. Stay in the flow. Format for clarity.

Now analyze."""

    # Build user prompt with structured + unstructured context
    user_prompt = f"""STRUCTURED DATABASE RESULTS:
{structured_result}

UNSTRUCTURED INTELLIGENCE (Job Descriptions):
{contextual_unstructured}

QUESTION: {user_question}

Design a bespoke strategic scaffold (name the sections you create) and weave structured facts with unstructured intelligence into one coherent answer."""

    try:
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": settings.OPENROUTER_UNSTRUCTURED_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
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
            "model": settings.OPENROUTER_UNSTRUCTURED_MODEL,
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
    "MARKETING", "FINANCE", "HR", "HUMAN RESOURCES", "LEAN OPERATION AND SYSTEMS", "STRATEGY", "IT", "ANALYTICS"
]

def _extract_specialization_from_question(question: str) -> Optional[str]:
    q = question.lower()
    mapping = {
        "marketing": "MARKETING",
        "finance": "FINANCE", 
        "human resources": "HR",
        "hr": "HR",
        "operations": "LEAN OPERATION AND SYSTEMS",
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
    """Fast deterministic patterns for common structured queries - expanded for robustness."""
    q = user_question.lower().strip()

    # Pattern 1: Company counts by specialization - expanded patterns
    company_count_patterns = [
        r'how many companies.*?came.*?for\s+(\w+)',
        r'how many companies.*?(\w+)\s+roles?',
        r'how many companies.*?hiring.*?(\w+)',
        r'how many companies.*?recruiting.*?(\w+)',
        r'how many companies.*?offering.*?(\w+)',
        r'count.*companies.*?(\w+)',
        r'number.*companies.*?(\w+)'
    ]

    for pattern in company_count_patterns:
        match = re.search(pattern, q)
        if match:
            spec_word = match.group(1)
            spec = _normalize_specialization_word(spec_word)
            if spec:
                return _get_companies_count_for_specialization(spec)

    # Pattern 2: General company participation counts (only when no specialization/role mentioned)
    if (re.search(r'how many companies', q) and
        re.search(r'came|visited|participated|placements?|campus|drive', q) and
        not re.search(r'for\s+\w+', q) and  # Don't match if "for X" is present
        not re.search(r'\w+\s+roles?', q)):  # Don't match if "X roles" is present
        return _get_total_companies_participated()

    # Pattern 3: Companies by specialization - expanded
    company_list_patterns = [
        r'(?:which\s+|what\s+)?companies.*?for\s+(\w+)',
        r'companies.*?(\w+)\s+roles?',
        r'companies.*?hiring.*?(\w+)',
        r'companies.*?recruiting.*?(\w+)',
        r'companies.*?offering.*?(\w+)',
        r'companies.*?specialization.*?(\w+)'
    ]

    for pattern in company_list_patterns:
        match = re.search(pattern, q)
        if match:
            spec_word = match.group(1)
            spec = _normalize_specialization_word(spec_word)
            if spec:
                return _get_companies_list_for_specialization(spec)

    # Pattern 4: General company lists
    if any(phrase in q for phrase in ['list companies', 'show companies', 'all companies', 'what companies', 'which companies']):
        return _get_all_companies_list()

    # Pattern 5: Role counts
    if any(phrase in q for phrase in ['how many roles', 'total roles', 'number of roles', 'count roles']):
        return _get_total_roles_count()

    # Pattern 6: Location-based queries - expanded
    location_patterns = [
        r'companies\s+(?:in|from|at|located\s+in)\s+([\w\s]+)',
        r'companies\s+([\w\s]+)\s+(?:location|city|place)'
    ]

    for pattern in location_patterns:
        match = re.search(pattern, q)
        if match:
            location = match.group(1).strip()
            return _get_companies_by_location(location)

    # Pattern 7: Salary queries - comprehensive
    if any(word in q for word in ['salary', 'salaries', 'package', 'packages', 'ctc', 'pay', 'compensation']):
        if any(word in q for word in ['highest', 'maximum', 'max', 'top', 'best']):
            return _get_highest_salary()
        elif any(word in q for word in ['lowest', 'minimum', 'min']):
            return _get_lowest_salary()
        elif any(word in q for word in ['average', 'avg', 'mean', 'typical']):
            return _get_average_salary()
        else:
            return _get_salary_overview()

    # Pattern 8: Skills queries - expanded
    if 'skills' in q or 'skill' in q:
        if any(word in q for word in ['most', 'top', 'common', 'popular', 'demanded', 'required', 'important']):
            return _get_top_skills()
        elif any(word in q for word in ['overview', 'summary', 'all']):
            return _get_skills_overview()
        else:
            return _get_top_skills()  # Default to top skills

    # Pattern 9: Year-based queries - improved
    year_patterns = [
        r'companies.*?(?:in|for|during)\s+(\d{4})',
        r'(\d{4})\s+companies',
        r'batch.*?\b(\d{4})\b'
    ]

    for pattern in year_patterns:
        match = re.search(pattern, q)
        if match:
            year = match.group(1)
            return _get_companies_by_year(year)

    # Pattern 10: Specialization queries without "companies"
    if any(word in q for word in ['marketing', 'finance', 'hr', 'human resources', 'operations', 'strategy', 'it', 'analytics']):
        spec = _extract_specialization_from_question(user_question)
        if spec:
            return _get_companies_count_for_specialization(spec)

    return None

def _normalize_specialization_word(word: str) -> Optional[str]:
    """Map user input to canonical specialization."""
    mapping = {
        'finance': 'FINANCE',
        'financial': 'FINANCE',
        'marketing': 'MARKETING',
        'hr': 'HR',
        'human': 'HR',
        'operations': 'LEAN OPERATION AND SYSTEMS',
        'ops': 'LEAN OPERATION AND SYSTEMS',
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
        return execute_multi_hop_query(sub_questions, user_question, context)
    # Single query path
    answer = route_single_query(user_question, context)
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
