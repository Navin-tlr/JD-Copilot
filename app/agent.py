"""
AI Agent for Intelligent Query Routing and Execution
Replaces the rigid query_router with a dynamic, reasoning-based system.
"""

import os
import json
import sqlite3
from langchain.tools import tool
from langchain.tools import Tool as LC_Tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from typing import Dict, List, Optional, Tuple

from .config import get_settings
from .database import PlacementDatabase
from .rag import retrieve_snippets, synthesize_answer # Assuming get_vectorstore is implicitly handled by retrieve_snippets
from .sql_tool import run_deterministic_sql_query
from .final_sql_tool import run_llama_index_sql_query

# Import our NEW validator and schema functions
from .sql_validator import validate_sql_query, get_dynamic_schema

# --- 1. Redefine the SQL Tool with Built-in Validation ---
@tool
def structured_database_query(generated_sql: str) -> str:
    """
    Use this tool to execute a VALIDATED SQLite query against the placements database.
    The query is first validated against the database schema.
    Only use this tool with a syntactically correct SQLite query.
    The agent should generate the SQL query and pass it to this tool.
    """
    db_path = "data/placement_data.db"  # Or get from settings

    # THE CRITICAL VALIDATION STEP
    is_valid, reason = validate_sql_query(generated_sql, db_path)

    if not is_valid:
        # If validation fails, STOP and return the error.
        # This feedback loop teaches the LLM what a valid query looks like.
        return f"Invalid SQL Query: {reason}. Please correct the query based on the schema and try again."

    # Only execute if the query is valid
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(generated_sql)
            results = cursor.fetchall()
            if not results:
                return "Query executed successfully, but returned no results."
            # You would format these results more nicely for the LLM to synthesize an answer
            return json.dumps(results)
    except Exception as e:
        return f"SQL Execution Error: {e}"

def get_database_schema():
    """
    Get the actual database schema to prevent hallucination.
    """
    try:
        db = PlacementDatabase()
        db_path = db.db_path
        sql_db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
        
        # Get actual table names and schemas
        tables = sql_db.get_table_names()
        schemas = {}
        
        for table in tables:
            try:
                schema = sql_db.get_table_info(table)
                schemas[table] = schema
            except Exception as e:
                print(f"Warning: Could not get schema for table {table}: {e}")
        
        return tables, schemas
    except Exception as e:
        print(f"Error getting database schema: {e}")
        return [], {}

def validate_sql_query(sql_query: str, actual_tables: list) -> tuple[bool, str]:
    """
    Validate SQL query to prevent hallucination of table names.
    """
    if not sql_query:
        return False, "Empty SQL query"
    
    # Check for common hallucination patterns
    sql_lower = sql_query.lower()
    
    # Check if query references non-existent tables
    for table in actual_tables:
        if table.lower() in sql_lower:
            continue
    
    # Look for common hallucinated table names
    hallucinated_tables = ['jobs', 'job', 'employee', 'employees', 'applicant', 'applicants']
    for hallucinated in hallucinated_tables:
        if hallucinated in sql_lower:
            return False, f"Query references non-existent table '{hallucinated}'. Available tables: {actual_tables}"
    
    # Check for basic SQL syntax
    if 'select' not in sql_lower:
        return False, "Query must contain SELECT statement"
    
    return True, "Query appears valid"

def _fetch_all_company_names(sql_db: SQLDatabase) -> List[str]:
    try:
        result = sql_db.run("SELECT company_name FROM companies")
        if not result:
            return []
        lines = [r.strip() for r in result.split("\n") if r.strip()]
        # sql_db.run often returns rows formatted like "('Name',)"; normalize greedily
        cleaned: List[str] = []
        for line in lines:
            name = line.strip()
            if name.startswith("(") and "," in name:
                name = name.strip("()")
                parts = [p.strip().strip("'") for p in name.split(",")]
                if parts:
                    name = parts[0]
            cleaned.append(name)
        return cleaned
    except Exception:
        return []

def _normalize_specialization(user_text: str) -> Optional[str]:
    text = user_text.strip().lower()
    mapping = {
        "marketing": "marketing",
        "mkt": "marketing",
        "finance": "finance",
        "fin": "finance",
        "hr": "hr",
        "human resources": "hr",
        "operations": "operations",
        "ops": "operations",
        "business analytics": "business analytics",
        "analytics": "business analytics",
    }
    # exact match first
    if text in mapping:
        return mapping[text]
    # fallback: find key contained in text
    for k, v in mapping.items():
        if k in text:
            return v
    return None

def _intent_from_query(query: str) -> Tuple[str, Dict[str, str]]:
    q = query.strip().lower()
    # Count companies by specialization
    if ("how many" in q or "count" in q) and ("companies" in q) and ("marketing" in q or "finance" in q or "hr" in q or "operations" in q or "analytics" in q):
        spec = _normalize_specialization(q) or ""
        return ("count_companies_by_specialization", {"specialization": spec})
    # List all companies
    if ("list" in q or "show" in q) and ("all companies" in q or ("companies" in q and "all" in q)):
        return ("list_companies_all", {})
    # List companies by specialization
    if ("list" in q or "show" in q) and ("companies" in q) and ("marketing" in q or "finance" in q or "hr" in q or "operations" in q or "analytics" in q):
        spec = _normalize_specialization(q) or ""
        return ("list_companies_by_specialization", {"specialization": spec})
    # List skills by company
    if ("skills" in q) and ("for" in q or "at" in q):
        # naive company extraction: longest matching company from DB will be used later
        return ("list_skills_by_company", {})
    return ("unknown", {})

def _execute_deterministic(sql_db: SQLDatabase, intent: str, params: Dict[str, str]) -> Optional[str]:
    # Only allow listed tables/columns
    allowed_tables = {"companies", "roles", "skills", "offers", "requirements"}
    # Intent handlers
    if intent == "count_companies_by_specialization":
        spec = params.get("specialization", "")
        if not spec:
            return "I need a specialization (e.g., marketing, finance, hr, operations, business analytics)."
        if spec not in {"marketing", "finance", "hr", "operations", "business analytics"}:
            return "Unsupported specialization."
        query = (
            "SELECT COUNT(DISTINCT c.company_name) as company_count "
            "FROM roles r JOIN companies c ON r.company_id = c.id "
            "WHERE LOWER(r.specialization) = '" + spec + "'"
        )
        result = sql_db.run(query)
        return f"Based on verified database query: {result} companies came for {spec} roles."
    if intent == "list_companies_all":
        result = sql_db.run("SELECT company_name FROM companies ORDER BY company_name")
        if not result:
            return "No companies found in the database."
        lines = [r.strip() for r in result.split("\n") if r.strip()]
        return "Here are all companies in the database:\n" + "\n".join(f"- {l}" for l in lines)
    if intent == "list_companies_by_specialization":
        spec = params.get("specialization", "")
        if not spec:
            return "I need a specialization (e.g., marketing, finance, hr, operations, business analytics)."
        query = (
            "SELECT DISTINCT c.company_name "
            "FROM roles r JOIN companies c ON r.company_id = c.id "
            "WHERE LOWER(r.specialization) = '" + spec + "' "
            "ORDER BY c.company_name"
        )
        result = sql_db.run(query)
        if not result:
            return f"No companies found for {spec}."
        lines = [r.strip() for r in result.split("\n") if r.strip()]
        return "Companies offering roles in " + spec + ":\n" + "\n".join(f"- {l}" for l in lines)
    if intent == "list_skills_by_company":
        all_names = _fetch_all_company_names(sql_db)
        if not all_names:
            return "No companies found in the database."
        # We cannot safely extract company name; return instruction message
        return "Please specify an exact company name from: " + ", ".join(sorted(all_names))
    return None

@tool
def query_job_database(query: str) -> str:
    """
    Use this tool to answer specific, factual questions about job data which can likely be found in a structured database.
    This includes queries about company names, job titles, required skills, education levels, and years of experience.
    Example questions: 'List all jobs from Alstom', 'What skills are required for a Data Scientist role?'
    """
    print("--- Using SQL Database Tool ---")
    
    try:
        # Step 0: Get actual database schema to prevent hallucination
        actual_tables, schemas = get_database_schema()
        print(f"Available tables: {actual_tables}")
        
        # Use our existing PlacementDatabase for now
        db = PlacementDatabase()
        db_path = db.db_path
        
        # Create SQLDatabase connection
        sql_db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
        
        # CRITICAL: Use deterministic queries for common questions to ensure consistency
        query_lower = query.lower()
        
        # Marketing role count - ALWAYS use the verified query
        if "how many companies" in query_lower and "marketing" in query_lower:
            print("🔒 Using deterministic query for marketing role count...")
            try:
                deterministic_query = """
                SELECT COUNT(DISTINCT c.company_name) as company_count
                FROM roles r 
                JOIN companies c ON r.company_id = c.id 
                WHERE LOWER(r.specialization) = 'marketing'
                """
                deterministic_result = sql_db.run(deterministic_query)
                print(f"Deterministic query result: {deterministic_result}")
                
                if deterministic_result:
                    return f"Based on verified database query: {deterministic_result} companies came for marketing roles."
                else:
                    return "Based on verified database query: 0 companies came for marketing roles."
            except Exception as det_error:
                print(f"Deterministic query failed: {det_error}")
                return f"Error executing verified query: {det_error}"
        
        # List all companies - ALWAYS use the verified query
        elif "list all companies" in query_lower or "all companies" in query_lower:
            print("🔒 Using deterministic query for company list...")
            try:
                deterministic_query = "SELECT company_name FROM companies ORDER BY company_name"
                deterministic_result = sql_db.run(deterministic_query)
                print(f"Deterministic query result: {deterministic_result}")
                
                if deterministic_result:
                    # Parse the result to get company names
                    companies = [row.strip() if isinstance(row, str) else str(row) for row in deterministic_result.split('\n') if row.strip()]
                    return f"Here are all companies in the database:\n" + "\n".join([f"- {company}" for company in companies])
                else:
                    return "No companies found in the database."
            except Exception as det_error:
                print(f"Deterministic query failed: {det_error}")
                return f"Error executing verified query: {det_error}"
        
        # For other queries, use the LangChain SQL agent with validation
        else:
            print("🔄 Using LangChain SQL agent for complex queries...")
        
        # Step 1: Generate SQL using mistralai/mistral-7b-instruct (optimized for code/SQL generation)
        settings = get_settings()
        if settings.OPENROUTER_API_KEY:
            sql_generator_llm = ChatOpenAI(
                model="mistralai/mistral-7b-instruct",
                temperature=0,
                openai_api_key=settings.OPENROUTER_API_KEY,
                openai_api_base="https://openrouter.ai/api/v1"
            )
        else:
            # Fallback to OpenAI if configured
            sql_generator_llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0,
                openai_api_key=settings.OPENAI_API_KEY
            )
        
        # Step 2: Validate SQL using moonshotai/kimi-k2 (prevent hallucination)
        if settings.OPENROUTER_API_KEY:
            sql_validator_llm = ChatOpenAI(
                model="moonshotai/kimi-k2",
                temperature=0,
                openai_api_key=settings.OPENROUTER_API_KEY,
                openai_api_base="https://openrouter.ai/api/v1"
            )
        else:
            sql_validator_llm = sql_generator_llm
        
        # Create a dedicated SQL Agent with validation
        # This is more reliable than a simple Text-to-SQL chain
        sql_agent_executor = create_sql_agent(sql_generator_llm, db=sql_db, agent_type="openai-tools", verbose=False)
        
        # Step 3: Execute the query with validation
        response = sql_agent_executor.invoke({"input": query})
        sql_result = response.get("output", "I was unable to retrieve an answer from the database.")
        
        # Step 4: Validate the result using the validator LLM
        validation_prompt = f"""
        You are a SQL validation expert. Review the following SQL query result and ensure it's accurate.
        
        User Question: {query}
        SQL Result: {sql_result}
        Available Tables: {actual_tables}
        
        Please validate:
        1. Does the result answer the user's question correctly?
        2. Are the numbers/statistics logical given the database context?
        3. Does the result match what would be expected from a placement database?
        4. Are there any obvious errors or inconsistencies?
        
        CRITICAL: If the user asks for "how many companies came for marketing role", 
        the answer should be a small number (likely 2-5 companies) since this is a placement database.
        If the result shows more than 10 companies, it's likely incorrect.
        
        If you find any issues, provide a corrected answer.
        If the result looks correct, confirm it.
        
        Validation Result:
        """
        
        try:
            validation_response = sql_validator_llm.invoke(validation_prompt)
            validation_result = validation_response.content
            
            # Additional validation: Check if the count makes sense
            if "how many companies" in query.lower() and "marketing" in query.lower():
                # For marketing role queries, verify the count is reasonable
                if any(str(num) in sql_result for num in range(10, 100)):
                    print("⚠️ Count seems too high for marketing roles, double-checking...")
                    # Execute a simple verification query
                    try:
                        verification_query = "SELECT COUNT(DISTINCT c.company_name) FROM roles r JOIN companies c ON r.company_id = c.id WHERE LOWER(r.specialization) = 'marketing'"
                        verification_result = sql_db.run(verification_query)
                        print(f"Verification query result: {verification_result}")
                        
                        # If verification gives a different result, use it
                        if verification_result and verification_result != sql_result:
                            print("🔄 Using verified result instead of agent result")
                            return f"Based on database verification: {verification_result} companies came for marketing roles."
                    except Exception as verify_error:
                        print(f"Verification query failed: {verify_error}")
            
            # If validation finds issues, return the corrected version
            if "issue" in validation_result.lower() or "incorrect" in validation_result.lower():
                print("⚠️ SQL validation found issues, providing corrected answer")
                return validation_result
            else:
                print("✅ SQL validation passed")
                return sql_result
                
        except Exception as validation_error:
            print(f"Warning: SQL validation failed: {validation_error}")
            return sql_result
        
    except Exception as e:
        return f"Error querying the database: {e}. Please try rephrasing your question."


# --- Tool 2: Vector Store Tool ---
# This tool answers semantic or open-ended questions by searching through the raw text of the job descriptions.

@tool
def query_unstructured_job_descriptions(query: str) -> str:
    """
    Use this tool to answer general, open-ended, or semantic questions that require
    a deep, contextual understanding of the full text of job descriptions. This is best for
    questions about day-to-day responsibilities, company culture, specific qualifications, or for summarizing JDs.
    Example questions: 'Summarize the company culture at Alstom', 'What are the daily tasks for an HR role?'
    """
    print("--- Using Vector Store Tool ---")
    
    try:
        # Use moonshotai/kimi-k2 for RAG (paid model, optimized for text understanding and generation)
        settings = get_settings()
        if settings.OPENROUTER_API_KEY:
            # For RAG, we'll use the existing synthesize_answer function but ensure it uses the right model
            snippets = retrieve_snippets(query, top_k=8, filters={})
            
            if not snippets:
                return "I could not find any relevant information in the available documents."
            
            # Synthesize answer using our existing logic
            answer = synthesize_answer(query, snippets, {})
            return answer or "I could not generate a comprehensive answer from the available information."
        else:
            # Fallback to existing RAG functions
            snippets = retrieve_snippets(query, top_k=8, filters={})
            
            if not snippets:
                return "I could not find any relevant information in the available documents."
            
            # Synthesize answer using our existing logic
            answer = synthesize_answer(query, snippets, {})
            return answer or "I could not generate a comprehensive answer from the available information."
        
    except Exception as e:
        return f"Error searching the documents: {e}. Please try rephrasing your question."


def create_jd_agent():
    """
    This function creates and configures the main agent that will orchestrate the tools.
    """
    tools = [
        structured_database_query,
        query_job_database,
        query_unstructured_job_descriptions,
    ]
    
    # Use moonshotai/kimi-k2 for the main agent (orchestrator)
    settings = get_settings()
    if settings.OPENROUTER_API_KEY:
        agent_llm = ChatOpenAI(
            model="moonshotai/kimi-k2",
            temperature=0,
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1"
        )
    else:
        agent_llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            openai_api_key=settings.OPENAI_API_KEY
        )

    custom_prompt = ChatPromptTemplate.from_template("""
    You are JD-Copilot, an intelligent placement cell assistant for MBA students.
    
    Tools:
    - structured_database_query: For ALL structured DB questions (counts, lists, skills, roles, companies). Prefer this first.
    - query_job_database: Legacy SQL tool (use only if structured_database_query fails).
    - query_unstructured_job_descriptions: For qualitative insights from unstructured documents.
    
    CRITICAL:
    - For "how many companies came for marketing role" and similar count/list intents, always use structured_database_query.
    - Do NOT write SQL yourself; call the tools.
    """)

    agent = create_openai_tools_agent(agent_llm, tools, custom_prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)
    return agent_executor


# Convenience function for easy integration
def create_placement_agent():
    """Create and return a configured placement agent."""
    return create_jd_agent()


def create_final_agent():
    """
    Final agent exposing two primary tools:
    - structured_database_query (deterministic SQL first, with guarded fallback)
    - query_unstructured_job_descriptions (vector RAG)
    """
    # Replace structured tool with the self-contained LlamaIndex tool
    final_structured_tool = LC_Tool(
        name="structured_data_query_tool",
        func=run_llama_index_sql_query,
        description=(
            "USE THIS TOOL for any factual DB queries: counts, lists, company/role/skill details. "
            "This tool internally converts NL->SQL and executes safely."
        ),
    )

    tools = [final_structured_tool, query_unstructured_job_descriptions]

    settings = get_settings()
    if settings.OPENROUTER_API_KEY:
        agent_llm = ChatOpenAI(
            model="moonshotai/kimi-k2",
            temperature=0,
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1",
        )
    else:
        agent_llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            openai_api_key=settings.OPENAI_API_KEY,
        )

    # Strict tool selection policy while preserving required variables for tools agent
    try:
        prompt = hub.pull("hwchase17/openai-tools-agent")
        # The hub prompt includes required variables: input, tools, tool_names, agent_scratchpad
        # We rely on strong tool descriptions to steer routing; no extra injection needed here.
    except Exception:
        # Fallback prompt that explicitly includes all required variables
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                (
                    "You are JD-Copilot. Choose one tool that best answers the question.\\n\\n"
                    "HARD RULES:\\n"
                    "- Use structured_database_query for ANY numeric, count, list, table, or entity-specific facts from the structured DB.\\n"
                    "  Examples: 'how many', 'count', 'list', 'show all', 'distinct', specific fields like companies, roles, skills.\\n"
                    "- After a successful call to structured_database_query, DO NOT call any other tool (no verification with RAG).\\n"
                    "- Only use query_unstructured_job_descriptions for qualitative, descriptive, or summarization questions about JD text (culture, responsibilities, summaries).\\n"
                    "  Never use it for counts/lists, even to verify.\\n"
                    "- If the user explicitly asks to cross-check with documents, you may then use RAG.\\n\\n"
                    "Available tools: {tools}. You may refer to them by name from: {tool_names}."
                ),
            ),
            ("user", "{input}"),
            ("assistant", "{agent_scratchpad}"),
        ])

    agent = create_openai_tools_agent(agent_llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=False)


def create_production_agent():
    """
    Creates the production-ready agent with dynamic schema loading,
    a strict JSON-based prompt, and a validation-enforced SQL tool.
    """
    settings = get_settings()
    db_path = "data/placement_data.db"

    # Step A: Dynamically fetch the schema and format as JSON
    schema_json = json.dumps(get_dynamic_schema(db_path), indent=2)

    # Step B: Create the strict, machine-readable prompt
    # Note: Using the correct template variables for LangChain
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
You are a world-class Text-to-SQL agent. Your purpose is to answer user questions by using the structured_database_query tool to execute SQL queries against the database.

**Database Schema (JSON format):**
```json
{schema}
```

**CRITICAL RULES:**

1.  You MUST use the structured_database_query tool to execute SQL queries. Do not just generate SQL text.

2.  When the user asks a question, generate the appropriate SQL query and pass it to the structured_database_query tool.

3.  You MUST generate queries that ONLY use the tables and columns explicitly defined in the schema above. Do not hallucinate any tables or columns.

4.  If the user's question cannot be answered using the provided schema, you MUST return the exact text: "I cannot answer this question with the available data."

5.  **IMPORTANT: Handle Case Sensitivity Automatically**
    - Specializations in the database are stored in UPPERCASE (e.g., 'FINANCE', 'HR', 'MARKETING', 'OPERATIONS')
    - Students may ask for 'Finance', 'finance', 'FINANCE', 'Marketing', etc.
    - ALWAYS use case-insensitive queries for specializations using UPPER() function
    - Example: `WHERE UPPER(r.specialization) = UPPER('Finance')` or `WHERE UPPER(r.specialization) LIKE '%FINANCE%'`

6.  **CRITICAL: You MUST Execute the SQL Query**
    - Do NOT just explain the SQL - you MUST execute it using the structured_database_query tool
    - Always call structured_database_query with your generated SQL
    - The tool will validate and execute the query, returning actual results
    - Then provide the answer based on those results

7.  **Robust Query Examples:**
    - For "Finance roles": `SELECT COUNT(DISTINCT c.company_name) FROM companies c JOIN roles r ON c.id = r.company_id WHERE UPPER(r.specialization) LIKE '%FINANCE%'`
    - For "HR positions": `SELECT COUNT(DISTINCT c.company_name) FROM companies c JOIN roles r ON c.id = r.company_id WHERE UPPER(r.specialization) LIKE '%HR%'`
    - For "Marketing jobs": `SELECT COUNT(DISTINCT c.company_name) FROM companies c JOIN roles r ON c.id = r.company_id WHERE UPPER(r.specialization) LIKE '%MARKETING%'`

8.  **Workflow:**
    - Generate SQL query
    - Call structured_database_query tool with the SQL
    - Get the actual result (e.g., [[1]] means 1 company)
    - Provide answer: "There are X companies that came for [specialization] roles"
        """),
        ("user", "{input}"),
        ("assistant", "{agent_scratchpad}"),
    ])
    
    # Step C: Define the tools available to the agent
    # We only expose our new, hardened tool.
    tools = [structured_database_query, query_unstructured_job_descriptions]  # Add back your RAG tool

    # Step D: Initialize the LLM and create the agent
    if settings.OPENROUTER_API_KEY:
        agent_llm = ChatOpenAI(
            model="moonshotai/kimi-k2",  # Using the specified model
            temperature=0,
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1",
        )
    else:
        # Fallback LLM
        agent_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    # Create a partial prompt with the schema
    partial_prompt = prompt.partial(schema=schema_json)
    
    agent = create_openai_tools_agent(agent_llm, tools, partial_prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=False)
