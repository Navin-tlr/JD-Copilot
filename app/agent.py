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
from .rag import retrieve_snippets, synthesize_answer

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

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "JD-Copilot"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        
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
            sql_database = SQLDatabase(engine)

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

            # Create NLSQLTableQueryEngine with explicit embedding
            _sql_query_engine = NLSQLTableQueryEngine(
                sql_database=sql_database,
                llm=llm,
                embed_model=embed_model,
                verbose=True
            )

            print("✅ NLSQLTableQueryEngine initialized successfully!")

        except Exception as e:
            print(f"❌ Failed to initialize SQL query engine: {e}")
            return None

    return _sql_query_engine

def get_vector_index():
    """Vector index functionality disabled for now."""
    print("⚠️ Vector index functionality disabled - focusing on SQL queries")
    return None

def decompose_multi_hop_query(user_question: str) -> List[str]:
    """Use LLM to decompose multi-hop queries into sequential sub-questions."""
    settings = get_settings()

    if not settings.OPENROUTER_API_KEY:
        print("❌ No OpenRouter API key for query decomposition")
        return [user_question]

    prompt = f"""You are a query decomposition expert. Break down complex multi-hop questions into sequential sub-questions that can be answered step-by-step.

Multi-hop query: {user_question}

Rules:
1. Identify if this is truly a multi-hop query (requires sequential reasoning)
2. If multi-hop, break it into 2-3 logical sub-questions
3. Each sub-question should be answerable independently
4. Later questions should reference results from earlier questions
5. If not multi-hop, return the original question as a single item

Output format: JSON array of strings
Example: ["How many companies came for placements?", "Among these companies, how many are in marketing?"]

Return only the JSON array:"""

    try:
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": settings.OPENROUTER_MODEL or "moonshotai/kimi-k2:free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 300,
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=20
        )

        if response.status_code == 200:
            result = response.json()["choices"][0]["message"]["content"]
            
            # Clean up markdown code blocks if present
            result = result.strip()
            if result.startswith("```json"):
                result = result[7:]
            if result.startswith("```"):
                result = result[3:]
            if result.endswith("```"):
                result = result[:-3]
            result = result.strip()

            # Try to parse as JSON
            try:
                sub_questions = json.loads(result)
                if isinstance(sub_questions, list) and len(sub_questions) > 0:
                    print(f"🔧 Decomposed into {len(sub_questions)} sub-questions: {sub_questions}")
                    return sub_questions
            except json.JSONDecodeError:
                print(f"⚠️ Failed to parse decomposition response: {result}")

        # Fallback: return original question
        return [user_question]

    except Exception as e:
        print(f"❌ Query decomposition failed: {e}")
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
            response = engine.query(user_question)
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
        snippets = retrieve_snippets(user_question, top_k=5, filters={})
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
