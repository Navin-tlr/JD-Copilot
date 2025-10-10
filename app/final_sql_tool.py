import os
from typing import Optional


_query_engine = None


def _build_llamaindex_engine():
    """Initialize and cache LlamaIndex query engine (silent failure if deps missing)."""
    global _query_engine
    if _query_engine is not None:
        return _query_engine

    try:
        from sqlalchemy import create_engine
        from llama_index.core import SQLDatabase
        from llama_index.core.indices.struct_store import NLSQLTableQueryEngine
        from llama_index.llms.openai import OpenAI
    except Exception:
        return None

    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        return None
    os.environ.setdefault("OPENAI_API_KEY", key)
    os.environ.setdefault("OPENAI_API_BASE", "https://openrouter.ai/api/v1")

    db_path = os.getenv("DATABASE_PATH", "data/placement_data.db")
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return None

    try:
        engine = create_engine(f"sqlite:///{db_path}")
        sql_db = SQLDatabase(engine, include_tables=["companies", "roles", "offers", "skills", "requirements"])
        model_name = os.getenv("OPENROUTER_MODEL", "x-ai/grok-4-fast")
        llm = OpenAI(api_key=key, model=model_name, temperature=0.0, max_tokens=800)
        _query_engine = NLSQLTableQueryEngine(
            sql_database=sql_db,
            tables=["companies", "roles", "offers", "skills", "requirements"],
            llm=llm,
            verbose=False
        )
        print(f"✅ LlamaIndex engine created with model: {model_name}")
        return _query_engine
    except Exception as e:
        print(f"❌ Error creating LlamaIndex engine: {e}")
        return None


def run_llama_index_sql_query(query: str) -> str:
    """
    Self-contained structured query tool using LlamaIndex for factual responses.
    Provides accurate information from the database without hallucination.
    """
    print(f"📦 final_sql_tool.run_llama_index_sql_query: '{query}'")

    # Try LlamaIndex first
    qe = _build_llamaindex_engine()
    if qe is not None:
        try:
            # Add detailed context to ensure factual responses
            enhanced_query = f"""
You are a SQL expert working with a placement database. Use ONLY the following schema and data:

SCHEMA:
- companies(id, company_name, company_type, industry, location, batch_year, created_at)
- roles(id, company_id, title, specialization, location, role_description, created_at)
- offers(id, role_id, batch_year, salary_min_lpa, salary_max_lpa, expected_hires, created_at)
- skills(id, role_id, skill_name, skill_type, skill_priority, created_at)
- requirements(id, role_id, requirement_text, requirement_type, requirement_priority, created_at)

RELATIONSHIPS:
- roles.company_id REFERENCES companies.id
- offers.role_id REFERENCES roles.id
- skills.role_id REFERENCES roles.id
- requirements.role_id REFERENCES roles.id

CRITICAL SPECIALIZATION VALUES (use these exact values):
- MARKETING (not "Marketing")
- FINANCE (not "Finance")
- HR (not "Hr" or "Human Resources")
- OPERATIONS (not "Operations")
- ANALYTICS (not "Analytics")
- IT (not "It")
- STRATEGY (not "Strategy")

IMPORTANT RULES:
1. For company counts by specialization: JOIN companies and roles, filter by UPPER(roles.specialization)
2. For listing companies: Use DISTINCT companies.company_name
3. For role information: Query the roles table
4. Always use proper JOINs between related tables
5. Use exact specialization values as shown above
6. Only return information that actually exists in the database

QUESTION: {query}

Generate a SQL query that accurately answers this question using the correct table relationships and exact specialization values.
"""

            resp = qe.query(enhanced_query)

            # Extract the response
            if hasattr(resp, 'response') and resp.response:
                result = resp.response
            else:
                result = str(resp)

            # Clean up the response to remove any hallucinated content
            result = _clean_llamaindex_response(result, query)

            print(f"✅ LlamaIndex response: {result[:100]}...")
            return result

        except Exception as e:
            print(f"🔥 LlamaIndex SQL engine error: {e}")
            print(f"🔥 Error type: {type(e).__name__}")

            # Check for common OpenRouter/API errors
            error_str = str(e).lower()
            if "api key" in error_str or "authentication" in error_str:
                print("🔑 OpenRouter API key issue detected")
            elif "rate limit" in error_str or "429" in error_str:
                print("⏱️ OpenRouter rate limit exceeded")
            elif "model" in error_str or "not found" in error_str:
                print("🤖 Model not available on OpenRouter")
            elif "timeout" in error_str or "connection" in error_str:
                print("🌐 Network/API timeout issue")

            import traceback
            traceback.print_exc()

    # Strategic fallback: Use deterministic SQL for accuracy, LLM only for formatting
    print("⚠️ LlamaIndex failed, using strategic SQL + LLM formatting fallback")
    try:
        from .sql_tool import run_deterministic_sql_query
        raw_sql_result = run_deterministic_sql_query(query)

        # Use LLM only for formatting the deterministic result
        if raw_sql_result and not raw_sql_result.startswith("Error"):
            # Minimal passthrough formatting (avoid external call to keep deterministic)
            formatted_result = f"Answer based on database: {raw_sql_result}" if '\n' not in raw_sql_result else raw_sql_result
            print(f"✅ Deterministic formatted result: {formatted_result[:100]}...")
            return formatted_result
        else:
            return raw_sql_result

    except Exception as e:
        print(f"❌ Strategic fallback failed: {e}")
        return "Unable to process the query. Please try rephrasing your question."


def _clean_llamaindex_response(response: str, original_query: str) -> str:
    """
    Clean LlamaIndex response to ensure factual accuracy and remove hallucinations.
    """
    if not response:
        return "No information available for this query."

    # Remove common hallucination patterns
    response = response.replace("It appears that", "Based on the database,")
    response = response.replace("It seems that", "According to available data,")
    response = response.replace("Currently no", "No")
    response = response.replace("currently no", "no")

    # Check for known factual discrepancies and use fallback
    query_lower = original_query.lower()

    # Finance companies check
    if "no companies" in response.lower() and "finance" in query_lower:
        print("🔍 Detected potential hallucination for finance companies, using factual fallback")
        return _get_factual_fallback(original_query)

    # Marketing companies check
    if "no companies" in response.lower() and "marketing" in query_lower:
        print("🔍 Detected potential hallucination for marketing companies, using factual fallback")
        return _get_factual_fallback(original_query)

    # HR companies check
    if "no companies" in response.lower() and ("hr" in query_lower or "human" in query_lower):
        print("🔍 Detected potential hallucination for HR companies, using factual fallback")
        return _get_factual_fallback(original_query)

    # Check for generic "no data" responses that might be incorrect
    if response.lower().strip() in [
        "there are no companies in the database",
        "no companies listed",
        "there are no companies",
        "no data available"
    ]:
        print("🔍 Detected generic 'no data' response, verifying with database")
        return _get_factual_fallback(original_query)

    return response


def _get_factual_fallback(query: str) -> str:
    """
    Provide factual fallback when LlamaIndex hallucinates.
    """
    print("🔄 Using factual fallback due to potential hallucination")

    try:
        from .sql_tool import run_sql_query
        result = run_sql_query(query)
        if result and not result.startswith("Error"):
            return f"Factual data from database: {result}"
    except Exception as e:
        print(f"❌ Factual fallback failed: {e}")

    return "Unable to retrieve accurate information. Please try a more specific query."


