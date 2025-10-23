"""
Intent Classifier & Router Agent
=================================
Understands user intent, extracts entities, and routes queries to appropriate data sources.

Responsibilities:
1. Parse queries and extract entities (company, specialization, role, year, hierarchy)
2. Infer intent type (factual, comparative, contextual, reflective)
3. Route to: structured_db (SQL), vector_db (Pinecone), or hybrid
4. Memory-aware: consult memory only when intent is unclear
5. Self-reflection: handle low confidence with clarification prompts

Architecture:
- LLM-only routing (no hardcoded rules)
- Strict JSON output schema
- Dynamic schema awareness (fetches SQL schema at runtime)
- Confidence-based memory triggers
"""

import json
import os
import time
import contextlib
from typing import Dict, Optional, List, Any
import asyncio
from dataclasses import dataclass, asdict
from enum import Enum


class RouteDestination(str, Enum):
    """Routing destinations for queries."""
    STRUCTURED_DB = "structured_db"
    VECTOR_DB = "vector_db"
    HYBRID = "hybrid"


@dataclass
class QueryEntities:
    """Extracted entities from user query."""
    specialization: List[str] = None  # Business Analytics | Finance | HR | Lean Operations & Systems | Marketing | General
    role: List[str] = None
    company: List[str] = None
    year: str = "not_specified"
    
    def __post_init__(self):
        if self.specialization is None:
            self.specialization = []
        if self.role is None:
            self.role = []
        if self.company is None:
            self.company = []


@dataclass
class RouterDecision:
    """Complete router decision with intent, entities, routing, and confidence."""
    intent: str
    entities: QueryEntities
    route: RouteDestination
    use_memory: bool
    confidence: float
    reasoning: str
    clarification_question: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "intent": self.intent,
            "entities": {
                "specialization": self.entities.specialization,
                "role": self.entities.role,
                "company": self.entities.company,
                "year": self.entities.year
            },
            "route": self.route.value,
            "use_memory": self.use_memory,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }
        if self.clarification_question:
            result["clarification_question"] = self.clarification_question
        return result


class IntentRouter:
    """
    LLM-based Intent Classifier & Router.
    
    Routes queries based on:
    - Intent understanding (factual, comparative, contextual, reflective)
    - Entity extraction (company, specialization, role, year, hierarchy)
    - Confidence assessment
    - Memory consultation when needed
    """
    
    SYSTEM_PROMPT = """You are an Intent Classification and Routing Agent for a conversational placement intelligence system serving MBA students.
Your role is to interpret user queries, identify intent, extract structured entities, and decide which data subsystem (Structured DB, Vector DB, or Hybrid) should handle the query.

You are part of a larger multi-agent architecture:

* **Memory Agent:** stores and retrieves conversational context when needed.
* **SQL Agent:** retrieves factual and numeric data.
* **Vector Agent (Pinecone):** retrieves qualitative and text-based insights.
* **Synthesizer Agent:** merges and summarizes multi-source results.

Your outputs must be precise, machine-readable JSON and must never contain natural language.

---

### Core Responsibilities

1. **Understand the User Intent**
   Identify the nature of the question (count, comparison, company detail, preparation guidance, feedback, trend, etc.).

2. **Extract Entities**
   Parse and normalize key information from the user query:

   * `specialization` → array of one or more: [Business Analytics, Finance, HR, Lean Operations & Systems, Marketing, General]
     - Must be **exact match** (case-insensitive)
     - "Analytics" alone → use "General" (could be Financial Analytics, HR Analytics, etc.)
     - "Business Analytics" → use "Business Analytics"
     - Can extract multiple if query mentions multiple specializations
   * `role` → array of job roles/positions (e.g., ["Consultant", "Product Manager"], ["Sales Manager"], etc.)
     - Can extract multiple roles from a single query
   * `company` → array of company names (e.g., ["Deloitte", "PwC"], ["UNIQLO"], etc.)
     - Can extract multiple companies from a single query
   * `year` → explicit or inferred (e.g., "this year", "last year", "2024")

3. **Select Routing Path**

   * `structured_db`: factual or quantitative queries (counts, comparisons, company lists).
   * `vector_db`: qualitative or experiential queries (interview preparation, feedback, insights).
   * `hybrid`: when both factual and qualitative data are needed.

4. **Handle Ambiguity Gracefully**

   * If the query lacks entities such as year or specialization, set them as `"not_specified"`.
   * Do not hallucinate; infer only if strongly implied.
   * If intent or entity linkage is unclear, set `"use_memory": true` to pull context from the Memory Agent.

---

### Reasoning Process Example

**Important:** Extract entities accurately by cross-checking against known specializations: [Business Analytics, Finance, HR, Lean Operations & Systems, Marketing, General]

**Critical:** "Analytics" (without "Business") should map to "General" specialization because it's ambiguous (could be Financial Analytics, HR Analytics, Marketing Analytics, etc.)

| Step | Thought | Example Result |
|------|---------|----------------|
| 1 | Parse user query semantically | Understand the core intent and information being requested |
| 2 | Identify all potential entity classes | Check for: Role(s), Specialization(s), Year, Company(ies), etc. |
| 3 | Match tokens to known specializations | Cross-check against: Business Analytics, Finance, HR, Lean Operations & Systems, Marketing, General |
| 4 | Handle "Analytics" disambiguation | If only "Analytics" (not "Business Analytics") → use "General" specialization |
| 5 | Extract multiple entities if present | Query can have multiple roles, companies, or specializations |
| 6 | Detect missing entities | Use empty arrays `[]` for missing roles/companies/specializations |
| 7 | Determine routing based on query type | Quantitative → `structured_db`, Qualitative → `vector_db`, Both → `hybrid` |
| 8 | Assess confidence | High confidence (≥0.85) → no memory needed; Low confidence (<0.50) → use memory |

---

### Return Schema (Strict JSON)

```json
{
  "intent": "<detected_intent_label>",
  "entities": {
    "specialization": ["<Business Analytics | Finance | HR | Lean Operations & Systems | Marketing | General>"],
    "role": ["<role_name_1>", "<role_name_2>"],
    "company": ["<company_name_1>", "<company_name_2>"],
    "year": "<year_or_not_specified>"
  },
  "route": "structured_db | vector_db | hybrid",
  "use_memory": true | false,
  "confidence": 0.xx,
  "reasoning": "<short reasoning for how routing and intent were decided>"
}
```

**Note:** 
- Empty arrays `[]` indicate no entities found for that type
- "Analytics" alone → `["General"]` (ambiguous, could be any specialization's analytics)
- "Business Analytics" → `["Business Analytics"]` (exact match)

---

### Intent and Routing Examples (Not Rigid Rules)

These are **examples only** to guide your reasoning. Use your judgment to identify the actual intent and route based on the query's nature:

| Query Type Example    | Possible Intent           | Typical Route                  | Example Query                                  |
| --------------------- | ------------------------- | ------------------------------ | ---------------------------------------------- |
| Quantitative count    | `company_count_by_role`   | `structured_db`                | "How many companies came for consulting?"      |
| Comparative           | `compare_specializations` | `structured_db` or `hybrid`    | "Compare Finance and Marketing placements."    |
| Company details       | `company_detail`          | `hybrid`                       | "Give me details of UNIQLO."                   |
| Interview preparation | `prep_guidance`           | `vector_db`                    | "Help me prepare for PwC interview."           |
| Alumni feedback       | `alumni_feedback`         | `vector_db`                    | "What were GD topics last year?"               |
| Cross-year trend      | `trend_analysis`          | `structured_db`                | "How did placements change from 2023 to 2024?" |
| Ambiguous query       | `context_continuation`    | Determined after memory lookup | "How about Marketing?"                         |

**Remember:** These are illustrative examples, not prescriptive rules. Reason through each query independently.

---

### Behavioral Guidelines

* Be deterministic and consistent.
* Never output natural sentences; only valid JSON.
* Specializations are ONLY: [Business Analytics, Finance, HR, Lean Operations & Systems, Marketing, General]. Anything else is a different entity type.
* **Critical:** "Analytics" alone (without "Business") → map to "General" because it's ambiguous (could be Financial Analytics, HR Analytics, etc.)
* Use empty arrays `[]` for missing entity types (not "not_specified" strings).
* Extract multiple entities when present in the query.
* If uncertain or referencing prior context, set `"use_memory": true`.
* Always include a `confidence` score between 0 and 1.
* Keep the `reasoning` concise, factual, and logically justified.

---

### Sample Outputs

**Example 1 — Quantitative Query**

User: "How many companies came for Finance placements?"

```json
{
  "intent": "company_count_by_specialization",
  "entities": {
    "specialization": ["Finance"],
    "role": [],
    "company": [],
    "year": "not_specified"
  },
  "route": "structured_db",
  "use_memory": false,
  "confidence": 0.92,
  "reasoning": "Quantitative query requesting count of companies for Finance specialization."
}
```

**Example 2 — Qualitative Query with "Analytics" (Ambiguous)**

User: "What interview tips do you have for Analytics roles?"

```json
{
  "intent": "interview_preparation",
  "entities": {
    "specialization": ["General"],
    "role": ["Analyst"],
    "company": [],
    "year": "not_specified"
  },
  "route": "vector_db",
  "use_memory": false,
  "confidence": 0.88,
  "reasoning": "Qualitative query seeking interview preparation. 'Analytics' is ambiguous (could be Financial Analytics, HR Analytics, etc.), so mapped to General specialization. Role identified as Analyst."
}
```

**Example 3 — Hybrid Query**

User: "Tell me about UNIQLO placements."

```json
{
  "intent": "company_detail",
  "entities": {
    "specialization": [],
    "role": [],
    "company": ["UNIQLO"],
    "year": "not_specified"
  },
  "route": "hybrid",
  "use_memory": false,
  "confidence": 0.85,
  "reasoning": "Company detail query requires both factual data (structured_db) and qualitative insights (vector_db)."
}
```

**Example 4 — Multiple Entities**

User: "Compare Deloitte and PwC for Finance and Marketing roles."

```json
{
  "intent": "compare_companies_by_specialization",
  "entities": {
    "specialization": ["Finance", "Marketing"],
    "role": [],
    "company": ["Deloitte", "PwC"],
    "year": "not_specified"
  },
  "route": "hybrid",
  "use_memory": false,
  "confidence": 0.90,
  "reasoning": "Comparative query across multiple companies and specializations requires both structured and unstructured data."
}
```

**Example 5 — Ambiguous Follow-up**

User: "What about Marketing?"

```json
{
  "intent": "context_continuation",
  "entities": {
    "specialization": ["Marketing"],
    "role": [],
    "company": [],
    "year": "not_specified"
  },
  "route": "structured_db",
  "use_memory": true,
  "confidence": 0.45,
  "reasoning": "Ambiguous follow-up query; Marketing detected but requires memory context to understand full intent."
}
```

---

### Final Principle

If you do not know, defer.
If you are unsure, clarify.
Never hallucinate.

Your purpose is not to answer but to understand and route with absolute clarity.
"""
    
    def __init__(self, llm_client=None):
        """
        Initialize the Intent Router.
        
        Args:
            llm_client: LLM client for classification (defaults to Gemini)
        """
        from app.llm_client import get_gemini_client
        self.llm_client = llm_client or get_gemini_client()
        self._schema_context = None
        print("✅ Intent Router initialized")
        # Configurable timeout to prevent hanging classification calls
        self.llm_timeout_seconds = 20.0
    
    def _get_sql_schema_context(self) -> str:
        """Fetch SQL schema dynamically for context-aware routing."""
        if self._schema_context:
            return self._schema_context
        
        try:
            db_path = os.getenv("DATABASE_PATH", "data/placement_data.db")
            if not os.path.exists(db_path):
                return ""
            
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            schema_info = []
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table});")
                columns = [row[1] for row in cursor.fetchall()]
                schema_info.append(f"- {table}({', '.join(columns)})")
            
            conn.close()
            
            self._schema_context = "Available SQL Schema:\n" + "\n".join(schema_info)
            return self._schema_context
        except Exception as e:
            print(f"⚠️ Could not fetch SQL schema: {e}")
            return ""
    
    async def classify_and_route(
        self,
        query: str,
        memory_context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> RouterDecision:
        """
        Classify user intent and route to appropriate data source.
        
        Args:
            query: User's natural language query
            memory_context: Optional conversation context from Memory Agent
            session_id: Optional session identifier
        
        Returns:
            RouterDecision with intent, entities, route, and confidence
        """
        print(f"\n🎯 Intent Router: Processing query: '{query}'")
        
        # Build MINIMAL user message - NO schema/instructions (already in SYSTEM_PROMPT)
        # Only include tiny context snippet if present
        context_snippet = ""
        if memory_context:
            # Extract compact summary (max 300 chars)
            summary = memory_context.get("summary") or memory_context.get("last_turn") or ""
            if summary:
                summary = str(summary).strip()
                if len(summary) > 300:
                    summary = summary[:300] + "..."
                context_snippet = f"\n\nPrevious context: {summary}"
        
        # MINIMAL user message: just query + optional tiny context
        user_prompt = f"Query: {query.strip()}{context_snippet}"
        
        # Call LLM for classification - no fallback, must succeed
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        # Use shorter, more realistic timeout for classification (30s default)
        timeout_sec = float(os.getenv("LLM_TIMEOUT_SECONDS", "30.0"))
        
        print("🔄 Calling Gemini for intent classification...")
        print(f"   System prompt length: {len(self.SYSTEM_PROMPT)} chars")
        print(f"   User prompt length: {len(user_prompt)} chars")
        # Safe runtime config diagnostics
        model = os.getenv("GEMINI_MODEL") or getattr(self.llm_client, "model", "unknown")
        api_key_present = bool(os.getenv("GEMINI_API_KEY", ""))
        print(f"   LLM config: model={model}, api_key_present={api_key_present}, timeout={timeout_sec:.1f}s")
        
        # Run blocking Gemini call in thread pool with enforced timeout + heartbeat logs
        loop = asyncio.get_running_loop()
        start_ts = time.monotonic()

        async def _heartbeat():
            while True:
                await asyncio.sleep(1)
                elapsed = time.monotonic() - start_ts
                if elapsed >= timeout_sec - 2:  # Stop heartbeat 2s before timeout
                    break
                print(f"⏳ Waiting for Gemini... {elapsed:.1f}s elapsed (timeout {timeout_sec:.1f}s)")

        heartbeat_task = asyncio.create_task(_heartbeat())

        def _call_gemini():
            import threading
            thread_name = threading.current_thread().name
            print(f"🧵 Gemini call running in thread '{thread_name}'")
            inner_start = time.monotonic()
            try:
                # Pass timeout to Gemini client (reduce by 2s for buffer)
                return self.llm_client.chat(
                    messages,
                    temperature=0.1,
                    max_tokens=800,
                    timeout=max(10.0, timeout_sec - 2.0)  # Ensure Gemini times out before asyncio
                )
            finally:
                inner_elapsed = time.monotonic() - inner_start
                print(f"🧵 Gemini call completed in thread '{thread_name}' after {inner_elapsed:.2f}s")

        try:
            response = await asyncio.wait_for(
                loop.run_in_executor(None, _call_gemini),
                timeout=timeout_sec,
            )
            elapsed = time.monotonic() - start_ts
            print(f"✅ Gemini classification completed in {elapsed:.2f}s")
        except asyncio.TimeoutError as exc:
            total_elapsed = time.monotonic() - start_ts
            print(f"⏰ Intent Router: Gemini classification timed out after {total_elapsed:.2f}s")
            raise RuntimeError(
                "Intent classification timed out waiting for Gemini response"
            ) from exc
        except Exception as exc:
            total_elapsed = time.monotonic() - start_ts
            print(f"❌ Intent Router: Gemini API error after {total_elapsed:.2f}s: {exc}")
            
            # Fallback: Use heuristic classification
            print("🔄 Falling back to heuristic classification...")
            fallback_decision = self._heuristic_classification(query)
            return fallback_decision
        finally:
            heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await heartbeat_task
        
        print(f"✅ Gemini response received ({len(response)} chars)")
        
        # Parse JSON response
        try:
            decision_dict = self._parse_llm_response(response)
        except Exception as e:
            # If parsing fails, fall back to heuristic classification
            print(f"❌ Failed to parse LLM response: {e}")
            print("🔄 Falling back to heuristic classification...")
            return self._heuristic_classification(query)
        
        # Convert to RouterDecision object
        decision = self._dict_to_decision(decision_dict)
        
        # Log decision
        self._log_decision(query, decision)
        
        return decision
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response and extract JSON."""
        # Remove markdown code blocks if present
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        
        response = response.strip()
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse error: {e}")
            print(f"Response: {response[:200]}...")
            # If JSON parsing fails, fall back to heuristic classification
            raise RuntimeError("JSON parsing failed") from e
    
    def _dict_to_decision(self, data: Dict[str, Any]) -> RouterDecision:
        """Convert dictionary to RouterDecision object."""
        entities_dict = data.get("entities", {})
        
        # Handle both array and string formats for backward compatibility
        specialization = entities_dict.get("specialization", [])
        if isinstance(specialization, str):
            specialization = [specialization] if specialization != "not_specified" else []
        
        role = entities_dict.get("role", [])
        if isinstance(role, str):
            role = [role] if role != "not_specified" else []
        
        company = entities_dict.get("company", [])
        if isinstance(company, str):
            company = [company] if company != "not_specified" else []
        
        entities = QueryEntities(
            specialization=specialization,
            role=role,
            company=company,
            year=entities_dict.get("year", "not_specified")
        )
        
        route_str = data.get("route", "hybrid")
        try:
            route = RouteDestination(route_str)
        except ValueError:
            print(f"⚠️ Invalid route '{route_str}', defaulting to hybrid")
            route = RouteDestination.HYBRID
        
        return RouterDecision(
            intent=data.get("intent", "unknown"),
            entities=entities,
            route=route,
            use_memory=data.get("use_memory", False),
            confidence=data.get("confidence", 0.5),
            reasoning=data.get("reasoning", "No reasoning provided"),
            clarification_question=data.get("clarification_question"),
        )
    
    def _heuristic_classification(self, query: str) -> RouterDecision:
        """Simple heuristic-based classification as fallback when LLM fails."""
        query_lower = query.lower()
        
        # Extract basic entities using keywords
        entities = QueryEntities(
            specialization=[],
            role=[],
            company=[],
            year="not_specified"
        )
        
        # Detect finance specialization
        if any(word in query_lower for word in ["finance", "financial", "fintech", "banking", "investment"]):
            entities.specialization.append("Finance")
        
        # Detect marketing specialization
        if any(word in query_lower for word in ["marketing", "brand", "digital marketing", "sales"]):
            entities.specialization.append("Marketing")
        
        # Detect HR specialization
        if any(word in query_lower for word in ["hr", "human resources", "talent", "recruitment"]):
            entities.specialization.append("HR")
        
        # Detect operations specialization
        if any(word in query_lower for word in ["operations", "ops", "supply chain", "logistics"]):
            entities.specialization.append("Operations")
        
        # Detect counting queries (likely structured)
        count_words = ["how many", "count", "number of", "total"]
        is_count_query = any(word in query_lower for word in count_words)
        
        # Detect list queries (likely structured)
        list_words = ["list", "show me", "which companies", "what companies"]
        is_list_query = any(word in query_lower for word in list_words)
        
        # Detect description queries (likely unstructured)
        desc_words = ["describe", "tell me about", "what is", "explain", "requirements", "skills"]
        is_desc_query = any(word in query_lower for word in desc_words)
        
        # Determine route
        if is_count_query or is_list_query:
            route = RouteDestination.STRUCTURED
            intent = "count_query" if is_count_query else "list_query"
            confidence = 0.7
        elif is_desc_query:
            route = RouteDestination.UNSTRUCTURED
            intent = "description_query"
            confidence = 0.6
        else:
            route = RouteDestination.HYBRID
            intent = "general_query"
            confidence = 0.5
        
        decision = RouterDecision(
            intent=intent,
            entities=entities,
            route=route,
            use_memory=False,
            confidence=confidence,
            reasoning=f"Heuristic classification based on keywords (LLM fallback)",
            clarification_question=None,
        )
        
        print(f"🧠 Heuristic classification: {route.value} (confidence: {confidence:.2f})")
        return decision
    
    def _log_decision(self, query: str, decision: RouterDecision):
        """Log routing decision for observability."""
        print(f"\n📊 Router Decision:")
        print(f"   Query: '{query}'")
        print(f"   Intent: {decision.intent}")
        print(f"   Route: {decision.route.value}")
        print(f"   Confidence: {decision.confidence:.2f}")
        print(f"   Use Memory: {decision.use_memory}")
        
        if decision.entities.company:
            print(f"   Companies: {', '.join(decision.entities.company)}")
        if decision.entities.specialization:
            print(f"   Specializations: {', '.join(decision.entities.specialization)}")
        if decision.entities.role:
            print(f"   Roles: {', '.join(decision.entities.role)}")
        if decision.entities.year != "not_specified":
            print(f"   Year: {decision.entities.year}")
        
        print(f"   Reasoning: {decision.reasoning}")
        
        if decision.clarification_question:
            print(f"   ❓ Clarification: {decision.clarification_question}")


# Global instance
_intent_router = None


def get_intent_router() -> IntentRouter:
    """Get or create global Intent Router instance."""
    global _intent_router
    if _intent_router is None:
        _intent_router = IntentRouter()
    return _intent_router
