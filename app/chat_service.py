import asyncio
import os
import re
import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional, Any
from dataclasses import dataclass

# Import your existing RAG components
from .agent import route_query
from .rag import retrieve_snippets, synthesize_answer
from .database import PlacementDatabase
from .config import get_settings
from .enhanced_chat_memory import EnhancedConversationMemory

@dataclass
class ChatMessage:
    id: str
    content: str
    sender: str  # 'user' or 'ai'
    timestamp: datetime
    session_id: str
    metadata: Optional[Dict] = None

@dataclass
class ChatSession:
    id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    metadata: Optional[Dict] = None
    name: Optional[str] = None  # Auto-generated session name

class ChatService:
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
        self.memories: Dict[str, EnhancedConversationMemory] = {}

        # Initialize your existing RAG components
        self.db = PlacementDatabase()
        
        # Memory limits (configurable via env)
        # Maximum concurrent sessions to keep in memory (default: 10)
        self.session_memory_limit: int = int(os.getenv("CHAT_SESSION_MEMORY_LIMIT", "10"))
        # Maximum messages to keep per session memory (default: 200)
        self.session_message_limit: int = int(os.getenv("CHAT_SESSION_MESSAGE_LIMIT", "200"))
    
    def _generate_session_name(self, first_message: str) -> str:
        """Generate a descriptive name from the first user message (ChatGPT-style)"""
        # Take first 40 chars and clean up
        name = first_message[:40].strip()
        # Remove trailing incomplete words
        if len(first_message) > 40:
            words = name.split()
            if len(words) > 1:
                name = ' '.join(words[:-1]) + "..."
        # Fallback if message is too short
        if len(name) < 5:
            name = f"Chat {datetime.now().strftime('%b %d')}"
        return name
    
    async def create_session(self, user_id: str, session_id: Optional[str] = None) -> str:
        """Create a new chat session. Allows explicit session IDs for external callers."""
        # Evict oldest session if we exceed configured session_memory_limit
        if len(self.sessions) >= self.session_memory_limit:
            # find oldest by last_activity
            oldest_session_id = min(self.sessions.items(), key=lambda kv: kv[1].last_activity)[0]
            print(f"🗑️ Session memory limit reached ({self.session_memory_limit}). Evicting oldest session: {oldest_session_id}")
            await self.delete_session(oldest_session_id)

        session_id = session_id or str(uuid.uuid4())
        session = ChatSession(
            id=session_id,
            user_id=user_id,
            created_at=datetime.now(),
            last_activity=datetime.now(),
            name=None  # Will be set after first message
        )
        self.sessions[session_id] = session
        # Use enhanced memory with bounded messages to avoid unbounded growth
        self.memories[session_id] = EnhancedConversationMemory(session_id, max_messages=self.session_message_limit, user_id=user_id)
        return session_id

    async def ensure_session(self, session_id: Optional[str], user_id: str) -> str:
        """Guarantee that a session exists and return the active session ID."""
        if not session_id:
            return await self.create_session(user_id)

        if session_id not in self.sessions:
            await self.create_session(user_id, session_id=session_id)

        return session_id
    
    async def send_message(self, session_id: str, content: str, user_id: str) -> AsyncGenerator[ChatMessage, None]:
        print(f"🔍 Backend received query: '{content}' from user {user_id}")

        # Create session if it doesn't exist
        session_id = await self.ensure_session(session_id, user_id)

        memory = self.memories[session_id]

        # Auto-generate session name from first message (ChatGPT behavior)
        if self.sessions[session_id].name is None and len(memory.messages) == 0:
            self.sessions[session_id].name = self._generate_session_name(content)
            print(f"📝 Auto-generated session name: '{self.sessions[session_id].name}'")

        # Enforce per-session message threshold (defensive trim)
        max_msgs = getattr(memory, "max_messages", None)
        if isinstance(max_msgs, int) and max_msgs > 0:
            try:
                while len(memory.messages) > max_msgs:
                    # remove oldest message
                    memory.messages.pop(0)
            except Exception:
                # If memory shape is unexpected, ignore and continue
                pass

        original_query = content
        context_info: Dict[str, Any] = {}

        # Check if query needs context resolution
        if memory.is_contextual_query(content):
            resolved_query, context_info = memory.resolve_context(content)
            if resolved_query != content:
                print(f"🔄 Resolved contextual query: '{content}' → '{resolved_query}'")
                content = resolved_query

        # Store user message in memory with enhanced tracking
        await memory.add_message(
            role='user',
            content=content,
            metadata={
                'user_id': user_id,
                'original_query': original_query if content != original_query else None,
                'context_resolution': context_info if context_info else None
            },
            query_type=self._detect_query_type(content),
            specialization=self._detect_specialization(content),
            entities_mentioned=self._extract_entities(content)
        )

        # Generate AI response using your RAG system with enhanced context
        context = await self._build_enhanced_context(session_id)
        ai_response = await self._generate_rag_response(content, session_id, user_id, context)

        # Store AI response in memory with enhanced tracking
        await memory.add_message(
            role='assistant',
            content=ai_response,
            metadata={'context_used': bool(context), 'enhanced_memory': True}
        )

        # Create response message
        ai_message = ChatMessage(
            id=str(uuid.uuid4()),
            content=ai_response,
            sender='ai',
            timestamp=datetime.now(),
            session_id=session_id
        )

        # Update session activity
        if session_id in self.sessions:
            self.sessions[session_id].last_activity = datetime.now()

        yield ai_message
    
    async def _build_enhanced_context(self, session_id: str) -> Dict[str, Any]:
        """Build ChatGPT-like context with full conversation history"""
        if session_id not in self.memories:
            return {}

        memory = self.memories[session_id]

        # Get full conversation history for ChatGPT-like context
        full_conversation = []
        for msg in memory.messages:
            full_conversation.append({
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            })

        # Get enhanced context metadata
        enhanced_context = await memory.get_enhanced_context()

        # Build comprehensive context
        context = {
            'full_conversation_history': full_conversation,  # Send complete history to LLM
            'conversation_summary': enhanced_context.get('base_context', ''),
            'current_topic': memory.current_context.get('last_specialization'),
            'recent_companies': memory.current_context.get('last_companies_mentioned', []),
            'recent_entities': memory.current_context.get('last_entities', []),
            'key_findings': self._extract_key_findings(memory),
            'reasoning_chain': self._build_reasoning_chain(memory),
            'workflow_stage': enhanced_context.get('context_state', {}).get('workflow_stage'),
            'conversation_depth': enhanced_context.get('message_count', 0),
            'session_health': enhanced_context.get('session_health', {}),
            'context_window_type': 'unlimited'  # Indicate ChatGPT-like behavior
        }

        return context

    def _extract_key_findings(self, memory) -> List[str]:
        """Extract key findings from conversation history"""
        findings = []

        # Extract numbers and statistics mentioned
        if 'last_numbers_mentioned' in memory.current_context:
            numbers = memory.current_context['last_numbers_mentioned']
            if 'total_companies' in numbers:
                findings.append(f"Total companies: {numbers['total_companies']}")
            if 'avg_min_salary' in numbers:
                findings.append(f"Average minimum salary: ₹{numbers['avg_min_salary']} LPA")

        # Extract recent companies discussed
        if 'last_companies_mentioned' in memory.current_context:
            companies = memory.current_context['last_companies_mentioned'][:3]  # Top 3
            if companies:
                findings.append(f"Recently discussed companies: {', '.join(companies)}")

        # Extract specialization focus
        if 'last_specialization' in memory.current_context:
            spec = memory.current_context['last_specialization']
            findings.append(f"Current specialization focus: {spec}")

        return findings

    def _detect_query_type(self, content: str) -> Optional[str]:
        """Detect the type of query for better context tracking"""
        content_lower = content.lower()

        if any(word in content_lower for word in ['how many', 'count', 'total', 'number of']):
            return 'count_query'
        elif any(word in content_lower for word in ['salary', 'pay', 'compensation', 'lpa']):
            return 'salary_query'
        elif any(word in content_lower for word in ['company', 'companies', 'organization']):
            return 'company_query'
        elif any(word in content_lower for word in ['role', 'position', 'job']):
            return 'role_query'
        elif any(word in content_lower for word in ['specialization', 'field', 'domain']):
            return 'specialization_query'
        elif any(word in content_lower for word in ['compare', 'vs', 'versus', 'difference']):
            return 'comparison_query'
        elif any(word in content_lower for word in ['advice', 'recommend', 'suggest']):
            return 'advice_query'
        else:
            return 'general_query'

    def _detect_specialization(self, content: str) -> Optional[str]:
        """Detect specialization mentioned in the query"""
        content_lower = content.lower()

        specializations = [
            'finance', 'accounting', 'marketing', 'sales', 'hr', 'human resources',
            'operations', 'technology', 'it', 'engineering', 'consulting', 'analytics'
        ]

        for spec in specializations:
            if spec in content_lower:
                return spec.title()

        return None

    def _extract_entities(self, content: str) -> List[str]:
        """Extract entities like company names from the query"""
        # Simple entity extraction - can be enhanced with NLP later
        known_companies = [
            'masters', 'mill story', 'tap academy', 'accorian', 'madison', 'target',
            'google', 'microsoft', 'amazon', 'apple', 'meta', 'netflix'
        ]

        content_lower = content.lower()
        entities = []

        for company in known_companies:
            if company in content_lower:
                entities.append(company.title())

        return entities

    def _clean_and_complete_snippet(self, snippet: str) -> str:
        """Clean and complete snippet text to avoid incomplete chunks"""
        if not snippet or len(snippet.strip()) < 10:
            return ""

        # Remove incomplete sentences at the end
        snippet = snippet.strip()

        # Check if snippet ends with incomplete sentence patterns
        incomplete_patterns = [
            r'\s*\([^)]*$',  # Incomplete parentheses
            r'\s*\[[^\]]*$',  # Incomplete brackets
            r'\s*\{[^}]*$',  # Incomplete braces
            r'\s*[^.!?]*$',  # No ending punctuation (but allow if it's a complete phrase)
        ]

        for pattern in incomplete_patterns:
            if re.search(pattern, snippet) and not re.search(r'[.!?]\s*$', snippet):
                # Try to find the last complete sentence
                sentences = re.split(r'(?<=[.!?])\s+', snippet)
                if len(sentences) > 1:
                    # Keep all but the last incomplete sentence
                    snippet = ' '.join(sentences[:-1]).strip()
                else:
                    # If no complete sentences, truncate at reasonable length
                    words = snippet.split()
                    if len(words) > 20:
                        snippet = ' '.join(words[:20]) + '...'

        # Ensure reasonable length (200-300 chars for meaningful context)
        if len(snippet) > 300:
            # Try to cut at sentence boundary
            sentences = re.split(r'(?<=[.!?])\s+', snippet[:300])
            if len(sentences) > 1:
                snippet = ' '.join(sentences[:-1])
            else:
                snippet = snippet[:250] + '...'

        return snippet.strip()

    def _is_valid_snippet(self, snippet: str) -> bool:
        """Validate that a snippet is complete and meaningful"""
        if not snippet or len(snippet.strip()) < 50:
            return False

        snippet = snippet.strip()

        # Reject snippets with incomplete patterns
        invalid_patterns = [
            r'\s*\([^)]*$',  # Incomplete parentheses
            r'\s*\[[^\]]*$',  # Incomplete brackets
            r'\s*\{[^}]*$',  # Incomplete braces
            r'^\s*\.\.\..*',  # Starts with ellipsis
            r'.*\.\.\.\s*$',  # Ends with ellipsis (indicating truncation)
            r'^\s*[a-z]',     # Starts with lowercase (likely fragment)
            r'.*\s+$',        # Ends with space (incomplete)
            r'following\s+rol',  # Specific pattern from the error
            r'the\s+following\s*$',  # Incomplete "the following"
        ]

        for pattern in invalid_patterns:
            if re.search(pattern, snippet, re.IGNORECASE):
                return False

        # Must have at least one complete sentence or meaningful phrase
        if not re.search(r'[.!?]\s', snippet) and len(snippet.split()) < 10:
            return False

        # Check for minimum word count and reasonable length
        words = snippet.split()
        if len(words) < 8 or len(snippet) < 100:
            return False

        return True

    def _build_reasoning_chain(self, memory) -> List[str]:
        """Build a reasoning chain from conversation history"""
        chain = []

        # Look at recent Q&A pairs
        recent_messages = memory.messages[-6:]  # Last 3 Q&A pairs

        for i in range(0, len(recent_messages) - 1, 2):
            if i + 1 < len(recent_messages):
                user_msg = recent_messages[i]
                ai_msg = recent_messages[i + 1]

                if user_msg.role == 'user' and ai_msg.role == 'assistant':
                    # Extract key insight from AI response
                    insight = self._extract_insight_from_response(ai_msg.content)
                    if insight:
                        chain.append(f"Step {len(chain) + 1}: {user_msg.content[:50]}... → {insight}")

        return chain

    def _extract_insight_from_response(self, response: str) -> str:
        """Extract key insight from AI response"""
        # Look for patterns that indicate key findings
        response_lower = response.lower()

        # Extract company counts
        import re
        count_match = re.search(r'(\d+)\s+companies?\s+came\s+for', response_lower)
        if count_match:
            return f"Found {count_match.group(1)} companies"

        # Extract salary information
        salary_match = re.search(r'salary.*?(₹?\d+(?:\.\d+)?\s*lpa)', response_lower)
        if salary_match:
            return f"Salary insight: {salary_match.group(1)}"

        # Extract key recommendations
        if 'strategic' in response_lower or 'recommend' in response_lower:
            return "Strategic recommendations provided"

        # Default: extract first meaningful sentence
        sentences = re.split(r'[.!?]+', response)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10 and not sentence.startswith('based on') and not sentence.startswith('as your'):
                return sentence[:100] + "..." if len(sentence) > 100 else sentence

        return ""

    async def _generate_rag_response(self, user_message: str, session_id: str, user_id: str, context: Dict[str, Any] = None) -> str:
        """Generate comprehensive response using the query router system"""
        print(f"🎓 Generating routed response for: '{user_message}'")
        try:
            # Step 1: Use query router to get the response with context
            router_response = route_query(user_message, context)
            print(f"🔍 Query router response: {router_response}")
            
            # Check if the response is a routing decision or a full answer
            if router_response in ["STRUCTURED", "UNSTRUCTURED", "HYBRID", "MULTI_HOP"]:
                # It's a routing decision, process accordingly
                routing_decision = router_response
                print(f"🔍 Routing decision: {routing_decision}")
                
                if routing_decision == "STRUCTURED":
                    print(f"🔍 Processing as STRUCTURED query")
                    response = await self._handle_structured_query(user_message)
                elif routing_decision == "UNSTRUCTURED":
                    print(f"🔍 Processing as UNSTRUCTURED query")
                    response = await self._handle_unstructured_query(user_message, context)
                elif routing_decision == "HYBRID":
                    print(f"🔍 Processing as HYBRID query")
                    response = await self._handle_hybrid_query(user_message, context)
                elif routing_decision == "MULTI_HOP":
                    print(f"🔍 Processing as MULTI_HOP query")
                    response = await self._handle_multi_hop_query(user_message)
            else:
                # It's a full answer from the router, use it directly
                print(f"🔍 Using direct response from router")
                response = router_response
            
            # Clean up formatting and make it visually appealing
            response = self._format_response(response, user_message)
            
            return response
            
        except Exception as e:
            print(f"❌ Routed response error: {e}")
            # Fallback to unstructured RAG to avoid legacy persona overrides
            try:
                print("↩️ Falling back to unstructured RAG path")
                response = await self._handle_unstructured_query(user_message, context)
                return self._format_response(response, user_message)
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")
                return "I hit an error while processing that. Try rephrasing or ask a smaller piece of the question."
    
    async def _handle_structured_query(self, user_message: str) -> str:
        """Handle structured queries using LlamaIndex SQL engine"""
        try:
            # Removed legacy detour to placement cell LLM to preserve conversational persona
            
            from .agent import get_llama_index_engine, normalize_query_with_schema_helper
            
            # Normalize the query using schema helper
            normalized_sql_task = normalize_query_with_schema_helper(user_message)
            print(f"🔧 Schema Helper normalized: '{user_message}' → '{normalized_sql_task}'")
            
            # Use LlamaIndex for robust SQL querying
            llama_engine = get_llama_index_engine()
            if llama_engine:
                response = llama_engine.query(normalized_sql_task)
                if response and hasattr(response, 'response'):
                    raw_response = response.response
                    
                    # Apply hallucination prevention for company count queries
                    if "companies" in user_message.lower() and "how many" in user_message.lower():
                        corrected_response = self._validate_and_correct_response(raw_response, user_message)
                        if corrected_response:
                            print(f"✅ Hallucination corrected: '{raw_response}' → '{corrected_response}'")
                            return corrected_response
                    
                    return raw_response
                else:
                    return "I couldn't process this structured query. Please try rephrasing."
            else:
                return "Database query engine is not available. Please try again later."
                
        except Exception as e:
            print(f"❌ Structured query error: {e}")
            return f"Structured query failed: {str(e)}. Check database schema and retry."
    
    async def _handle_unstructured_query(self, user_message: str, context: Dict[str, Any] = None) -> str:
        """Handle unstructured queries using RAG system with conversation context"""
        try:
            from .rag import retrieve_snippets, synthesize_answer
            
            # Use existing RAG system with increased context for strategic analysis
            snippets = retrieve_snippets(user_message, top_k=30, filters={})
            if snippets:
                # Pass context to synthesis for conversation continuity
                answer = synthesize_answer(user_message, snippets, {}, context)
                # CRITICAL FIX: Don't fallback to generic message - use the actual answer
                if answer:
                    return answer
                else:
                    return "I could not find relevant information to answer your question based on the available documents."
            else:
                return "I couldn't find any relevant information in the available documents."
                
        except Exception as e:
            print(f"❌ Unstructured query error: {e}")
            return f"Unstructured query failed: {str(e)}. Check vector index and retry."
    
    async def _handle_hybrid_query(self, user_message: str, context: Dict[str, Any] = None) -> str:
        """Handle hybrid queries using both structured and unstructured data"""
        try:
            # Get structured data first
            structured_answer = await self._handle_structured_query(user_message)
            
            # Get RAG insights with context
            rag_answer = await self._handle_unstructured_query(user_message, context)
            
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
                return "I couldn't retrieve either structured data or additional context for this query."
                
        except Exception as e:
            print(f"❌ Hybrid query error: {e}")
            return f"Hybrid query failed: {str(e)}. Check both structured and unstructured paths."
    
    async def _llm_driven_database_query(self, user_message: str) -> str:
        """Use LLM to understand intent and generate intelligent database responses"""
        try:
            # Connect to database
            import sqlite3
            conn = sqlite3.connect('data/placement_data.db')
            cursor = conn.cursor()
            
            # Get database schema for LLM context
            cursor.execute("PRAGMA table_info(companies)")
            companies_schema = cursor.fetchall()
            
            cursor.execute("PRAGMA table_info(roles)")
            roles_schema = cursor.fetchall()
            
            # Get sample data for context
            cursor.execute("SELECT company_name, industry, location FROM companies LIMIT 3")
            sample_companies = cursor.fetchall()
            
            cursor.execute("SELECT title, specialization FROM roles LIMIT 3")
            sample_roles = cursor.fetchall()
            
            # Create context for LLM
            db_context = f"""
            Database Schema:
            Companies: {companies_schema}
            Roles: {roles_schema}
            
            Sample Data:
            Companies: {sample_companies}
            Roles: {sample_roles}
            
            User Query: {user_message}
            
            Based on this database, provide a comprehensive response. If asking about:
            - Company info: Query companies and roles tables
            - Role details: Query roles table with company info
            - Counts: Use SQL COUNT queries
            - Strategic advice: Base advice on actual role data from database
            
            Always use real data from the database, never make up information.
            """
            
            # Use simple LLM call to understand and respond
            response = await self._call_llm_for_database_query(db_context, user_message, cursor)
            
            return response
                
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            return f"Database connection error: {str(e)}"
        finally:
            if 'conn' in locals():
                conn.close()
    
    async def _call_llm_for_database_query(self, db_context: str, user_message: str, cursor) -> str:
        """Call LLM to understand query and generate database-driven response"""
        try:
            # Simple LLM prompt for database understanding
            prompt = f"""
            You are a database expert. Based on this context:
            {db_context}
            
            Generate a comprehensive response using ONLY the database data provided.
            If the user asks about a company, query the database for that company's roles.
            If they ask for strategic advice, base it on actual role data.
            If they ask for counts, use SQL queries to get accurate numbers.
            
            User Query: {user_message}
            
            Response should be:
            1. Professional and strategic
            2. Based ONLY on database data
            3. Well-formatted with bullet points
            4. Include actual role titles, specializations, industries
            5. Provide actionable insights based on real data
            
            Generate your response now:
            """
            
            # For now, use a simple database query approach
            # In production, you'd call your actual LLM here
            return await self._simple_database_response(user_message, cursor)
            
        except Exception as e:
            print(f"❌ LLM call error: {e}")
            return f"Error processing with LLM: {str(e)}"
    
    async def _simple_database_response(self, user_message: str, cursor) -> str:
        """Simple database response while LLM integration is being set up"""
        user_message_lower = user_message.lower()
        
        try:
            # Check for company-specific queries
            if any(word in user_message_lower for word in ['masters', 'mill story', 'tap academy', 'accorian', 'madison', 'target']):
                return await self._get_company_response(user_message_lower, cursor)
            
            # Check for count queries
            elif any(word in user_message_lower for word in ['how many', 'count', 'companies']):
                return await self._get_count_response(cursor)
            
            # Check for role queries
            elif any(word in user_message_lower for word in ['roles', 'positions', 'jobs']):
                return await self._get_roles_response(cursor)
            
            # Default: show available data
            else:
                return await self._get_summary_response(cursor)
                
        except Exception as e:
            print(f"❌ Simple response error: {e}")
            return f"Error generating response: {str(e)}"
    
    async def _get_company_response(self, user_message: str, cursor) -> str:
        """Get company-specific response from database"""
        try:
            # Find which company they're asking about
            companies = ['masters', 'mill story', 'tap academy', 'accorian', 'madison', 'target']
            target_company = None
            
            for company in companies:
                if company in user_message:
                    target_company = company
                    break
            
            if target_company:
                cursor.execute("""
                    SELECT r.title, r.specialization, c.company_name, c.industry, c.location
                    FROM roles r
                    JOIN companies c ON r.company_id = c.id
                    WHERE c.company_name LIKE ?
                """, (f'%{target_company}%',))
                
                role_data = cursor.fetchone()
                if role_data:
                    title, specialization, company_name, industry, location = role_data
                    
                    response = f"STRATEGIC ANALYSIS: {company_name.upper()} OPPORTUNITY\n\n"
                    response += f"Based on our verified database:\n\n"
                    response += f"• Position: {title}\n"
                    response += f"• Specialization: {specialization}\n"
                    response += f"• Industry: {industry or 'Not specified'}\n"
                    response += f"• Location: {location or 'Not specified'}\n\n"
                    
                    response += "STRATEGIC INSIGHTS:\n\n"
                    
                    if 'masters' in company_name.lower():
                        response += "• This is an Admission Counselor role in the Operations department\n"
                        response += "• Perfect for MBA students interested in education sector operations\n"
                        response += "• Opportunity to work in a growing education company\n\n"
                    elif 'mill story' in company_name.lower():
                        response += "• This is a D2C food brand role\n"
                        response += "• Great for MBA students interested in consumer goods and food industry\n"
                        response += "• Opportunity to work in emerging D2C sector\n\n"
                    elif 'tap academy' in company_name.lower():
                        response += "• This is an EdTech company role\n"
                        response += "• Perfect for MBA students interested in education technology\n"
                        response += "• Opportunity to work in growing EdTech sector\n\n"
                    else:
                        response += "• This role offers valuable industry experience\n"
                        response += "• Great opportunity for MBA students to gain practical skills\n"
                        response += "• Chance to work in a dynamic business environment\n\n"
                    
                    response += "RECOMMENDED ACTIONS:\n\n"
                    response += "• Focus on relevant specialization skills\n"
                    response += "• Highlight any industry-specific experience\n"
                    response += "• Emphasize relevant technical and soft skills\n"
                    response += "• Research the company's business model and growth trajectory\n"
                    
                    return response
                    
            return "Please specify which company you'd like information about."
            
        except Exception as e:
            print(f"❌ Company response error: {e}")
            return f"Error retrieving company information: {str(e)}"
    
    async def _get_count_response(self, cursor) -> str:
        """Get company count response from database"""
        try:
            cursor.execute("SELECT COUNT(DISTINCT company_id) FROM roles")
            company_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT c.company_name FROM companies c JOIN roles r ON c.id = r.company_id GROUP BY c.id")
            companies = [row[0] for row in cursor.fetchall()]
            
            response = f"Based on our verified database:\n\n"
            response += f"• Total companies with placement roles: {company_count}\n"
            response += f"• Companies: {', '.join(companies)}\n\n"
            response += "Each company has at least one placement role available."
            
            return response
            
        except Exception as e:
            print(f"❌ Count response error: {e}")
            return f"Error counting companies: {str(e)}"
    
    async def _get_roles_response(self, cursor) -> str:
        """Get roles response from database"""
        try:
            cursor.execute("""
                SELECT r.title, c.company_name, c.industry
                FROM roles r
                JOIN companies c ON r.company_id = c.id
            """)
            
            roles_data = cursor.fetchall()
            if roles_data:
                response = "AVAILABLE ROLES:\n\n"
                
                for title, company_name, industry in roles_data:
                    response += f"• {title} at {company_name}\n"
                    response += f"  Industry: {industry or 'Not specified'}\n\n"
                
                response += "This data is from our verified placement database."
                return response
                    
            return "No roles found in our database."
            
        except Exception as e:
            print(f"❌ Roles response error: {e}")
            return f"Error retrieving roles: {str(e)}"
    
    async def _get_summary_response(self, cursor) -> str:
        """Get summary response from database"""
        try:
            cursor.execute("SELECT COUNT(*) FROM companies")
            company_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM roles")
            role_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT company_name FROM companies LIMIT 5")
            sample_companies = [row[0] for row in cursor.fetchall()]
            
            response = "AVAILABLE DATA SUMMARY:\n\n"
            response += f"• Total companies: {company_count}\n"
            response += f"• Total roles: {role_count}\n"
            response += f"• Sample companies: {', '.join(sample_companies)}\n\n"
            
            response += "You can ask about:\n"
            response += "• Specific companies (e.g., 'Tell me about TAP Academy')\n"
            response += "• Role types (e.g., 'What roles are available?')\n"
            response += "• Company counts (e.g., 'How many companies came for placements?')\n"
            response += "• Strategic advice (e.g., 'Give me strategic advice for Masters Union')"
            
            return response
            
        except Exception as e:
            print(f"❌ Summary response error: {e}")
            return f"Error retrieving data summary: {str(e)}"
    
    def _format_response(self, response: str, user_message: str = "") -> str:
        """Format responses for clean visual presentation while preserving Markdown.

        - Preserve existing headings and bold text
        - Convert plain section lines like "Title:" into Markdown subheadings "### **Title**"
        - Highlight labels (IMPORTANT, CRITICAL, NOTE, KEY, TAKEAWAY) by bolding the label
        - Use bullets and short paragraphs (spacing handled by client renderer)
        """
        if not response:
            return response

        import re

        text = response.strip()
        # Normalize line endings and collapse excessive blank lines
        text = re.sub(r"\r\n?|\r", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        lines = text.split("\n")
        out_lines: List[str] = []

        section_pattern = re.compile(r"^([A-Z][A-Za-z0-9 /&\-]{2,}):\s*$")
        label_pattern = re.compile(r"^(\s*)(IMPORTANT|CRITICAL|NOTE|KEY|TAKEAWAY)(\s*:?)(\s*)(.*)$", re.IGNORECASE)

        for line in lines:
            raw = line.rstrip()
            if not raw:
                out_lines.append("")
                continue

            # Keep existing markdown headings as-is
            if raw.lstrip().startswith(("# ", "## ", "### ", "#### ")):
                out_lines.append(raw)
                continue

            # Convert plain section titles into bold subheadings
            m = section_pattern.match(raw)
            if m:
                title = m.group(1).strip()
                out_lines.append(f"### **{title}**")
                continue

            # Bold important labels
            lm = label_pattern.match(raw)
            if lm:
                indent, label, colon, space, rest = lm.groups()
                out_lines.append(f"{indent}**{label.upper()}**:{space}{rest}".rstrip())
                continue

            out_lines.append(raw)

        return "\n".join(out_lines).strip()
    
    def _generate_query_specific_heading(self, user_message: str) -> str:
        """Deprecated: We now preserve the model's headings and subheadings."""
        return ""
    
    def _extract_company_name(self, user_message: str) -> str:
        """Extract company name from user message for personalized headings"""
        user_message_lower = user_message.lower()
        
        # Common patterns for company extraction
        patterns = [
            ("full jd of ", "of "),
            ("jd of ", "of "),
            ("job description of ", "of "),
            ("full jd for ", "for "),
            ("jd for ", "for "),
            ("job description for ", "for "),
            ("details about ", "about "),
            ("information about ", "about "),
            ("jd from ", "from "),
            ("job description from ", "from "),
            ("full jd from ", "from "),
            ("complete jd from ", "from "),
            ("complete jd of ", "of "),
            ("entire jd of ", "of "),
            ("entire jd for ", "for "),
            ("entire jd from ", "from ")
        ]
        
        for pattern, phrase in patterns:
            if pattern in user_message_lower:
                potential_company = user_message_lower.split(pattern, 1)[1]
                # Clean up and limit to reasonable company name length
                company_name = " ".join(potential_company.strip().split()[:4])
                # Additional validation
                if company_name and not any(company_name.endswith(word) for word in ['roles', 'positions', 'specializations', 'skills', 'requirements', 'jd', 'description']):
                    return company_name.title()
        
        return ""
    
    async def get_session_messages(self, session_id: str) -> List[ChatMessage]:
        if session_id in self.memories:
            # Convert ChatMessage objects from enhanced memory to ChatMessage dataclass
            memory_messages = []
            for msg in self.memories[session_id].messages:
                chat_msg = ChatMessage(
                    id=str(uuid.uuid4()),  # Generate ID since memory doesn't store it
                    content=msg.content,
                    sender=msg.role,
                    timestamp=msg.timestamp,
                    session_id=session_id
                )
                memory_messages.append(chat_msg)
            return memory_messages
        return []

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user with metadata"""
        sessions = []
        for session in self.sessions.values():
            if session.user_id == user_id:
                message_count = len(self.memories.get(session.id).messages) if session.id in self.memories else 0
                sessions.append({
                    'id': session.id,
                    'name': session.name or f"Chat {session.created_at.strftime('%b %d')}",
                    'created_at': session.created_at.isoformat(),
                    'last_activity': session.last_activity.isoformat(),
                    'message_count': message_count
                })
        # Sort by last_activity descending
        sessions.sort(key=lambda s: s['last_activity'], reverse=True)
        return sessions

    async def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            if session_id in self.memories:
                self.memories[session_id].clear_memory()
                del self.memories[session_id]
            return True
        return False

    async def _handle_multi_hop_query(self, user_message: str) -> str:
        """Handle multi-hop queries requiring sequential reasoning"""
        try:
            # Use agent's multi-hop decomposition and synthesis (conversational)
            print(f"🔍 Multi-hop query detected, using agent multi-hop synthesis")
            from .agent import decompose_multi_hop_query, execute_multi_hop_query
            sub_qs = decompose_multi_hop_query(user_message)
            return execute_multi_hop_query(sub_qs, user_message)
            
        except Exception as e:
            print(f"❌ Multi-hop query error: {e}")
            return f"I encountered an error processing this multi-hop query: {str(e)}"
    
    async def _placement_cell_llm_response(self, user_message: str) -> str:
        """Generate comprehensive placement cell response using LLM's full capabilities"""
        try:
            # 1. Get relevant database data
            db_data = await self._get_comprehensive_db_data(user_message)
            
            # 2. Get relevant vector snippets for context
            vector_snippets = await self._get_vector_snippets(user_message)
            
            # 3. Create comprehensive LLM prompt for placement cell representative
            context_snapshot: Dict[str, Any] = {}
            llm_prompt = self._create_placement_cell_prompt(user_message, db_data, vector_snippets, context_snapshot)
            
            # 4. Call LLM with full capabilities
            response = await self._call_placement_cell_llm(llm_prompt)
            
            if response and len(response.strip()) > 100:
                return response
            else:
                # Fallback to enhanced database response
                print("⚠️ LLM response too short, using enhanced fallback")
                return await self._enhanced_database_response(user_message, db_data)
                
        except Exception as e:
            print(f"❌ Placement cell LLM error: {e}")
            return await self._enhanced_database_response(user_message, {})
    
    async def _get_comprehensive_db_data(self, user_message: str) -> dict:
        """Get comprehensive database data for the query"""
        try:
            import sqlite3
            conn = sqlite3.connect('data/placement_data.db')
            cursor = conn.cursor()
            
            data = {}
            
            # Get all companies and roles
            cursor.execute("""
                SELECT c.company_name, c.industry, c.location, c.company_type,
                       r.title, r.specialization, r.role_description
                FROM companies c
                LEFT JOIN roles r ON c.id = r.company_id
                ORDER BY c.company_name
            """)
            
            all_data = cursor.fetchall()
            
            # Organize data by company
            companies = {}
            for row in all_data:
                company_name, industry, location, company_type, title, specialization, role_desc = row
                
                if company_name not in companies:
                    companies[company_name] = {
                        'industry': industry,
                        'location': location,
                        'company_type': company_type,
                        'roles': []
                    }
                
                if title:  # Only add if role exists
                    companies[company_name]['roles'].append({
                        'title': title,
                        'specialization': specialization,
                        'description': role_desc
                    })
            
            data['companies'] = companies
            data['total_companies'] = len(companies)
            data['total_roles'] = sum(len(c['roles']) for c in companies.values())
            
            # Get industry breakdown
            industries = {}
            for company, info in companies.items():
                industry = info['industry'] or 'Not specified'
                if industry not in industries:
                    industries[industry] = []
                industries[industry].append(company)
            
            data['industries'] = industries
            
            # Get specialization breakdown
            specializations = {}
            for company, info in companies.items():
                for role in info['roles']:
                    spec = role['specialization'] or 'Not specified'
                    if spec not in specializations:
                        specializations[spec] = []
                    specializations[spec].append(f"{role['title']} at {company}")
            
            data['specializations'] = specializations
            
            conn.close()
            return data
            
        except Exception as e:
            print(f"❌ Database data error: {e}")
            return {}
    
    async def _get_vector_snippets(self, user_message: str) -> str:
        """Get relevant vector snippets for enhanced context with improved chunk retrieval"""
        try:
            # Use your existing RAG system to get relevant snippets
            from .rag import retrieve_snippets

            # Get more comprehensive snippets for better internal context
            # Increase top_k and add quality filtering for deep-dive strategic analysis
            snippets = retrieve_snippets(user_message, top_k=60, filters={})

            if snippets:
                snippet_text = "INTERNAL JOB DESCRIPTION CONTEXT (from vector database):\n"
                snippet_text += "Use these validated snippets to understand role requirements, company culture, and specific details:\n\n"

                valid_snippets = []
                for snippet in snippets:
                    # Get more context from each snippet - handle different snippet types and avoid incomplete chunks
                    try:
                        if isinstance(snippet, str):
                            snippet_content = self._clean_and_complete_snippet(snippet)
                        elif hasattr(snippet, 'text'):
                            snippet_content = self._clean_and_complete_snippet(snippet.text)
                        elif hasattr(snippet, 'content'):
                            snippet_content = self._clean_and_complete_snippet(snippet.content)
                        else:
                            snippet_content = self._clean_and_complete_snippet(str(snippet))

                        # Only include if we have meaningful, complete content
                        if self._is_valid_snippet(snippet_content):
                            valid_snippets.append(snippet_content)

                    except Exception as e:
                        print(f"⚠️ Snippet processing error: {e}")
                        continue

                # Limit to top 10 most relevant snippets to avoid token bloat
                for i, snippet_content in enumerate(valid_snippets[:10], 1):
                    snippet_text += f"{i}. {snippet_content}\n\n"

                if valid_snippets:
                    snippet_text += "IMPORTANT: Base ALL strategic insights, recommendations, and career guidance on these validated internal snippets and the database information provided above. Do not reference external knowledge or incomplete data."
                    return snippet_text
                else:
                    return "INTERNAL JOB DESCRIPTION CONTEXT: Retrieved snippets were incomplete or invalid. Base all insights on the verified database company and role information provided above."
            else:
                return "INTERNAL JOB DESCRIPTION CONTEXT: No specific job description snippets available for this query. Base all insights on the verified database company and role information provided above."

        except Exception as e:
            print(f"❌ Vector snippets error: {e}")
            return "INTERNAL JOB DESCRIPTION CONTEXT: Vector search temporarily unavailable. Base all insights on the verified database company and role information provided above."
    
    def _create_placement_cell_prompt(self, user_message: str, db_data: dict, vector_snippets: str, context: Dict[str, Any] = None) -> str:
        """Create comprehensive prompt for placement cell representative with full conversation history"""

        # Include full conversation history for ChatGPT-like context
        conversation_history = ""
        if context and context.get('full_conversation_history'):
            conversation_history = "CONVERSATION HISTORY (for context and follow-up questions):\n"
            for msg in context['full_conversation_history'][-20:]:  # Last 20 messages to avoid token limits
                role = "Student" if msg['role'] == 'user' else "Placement Cell"
                timestamp = msg.get('timestamp', '')[:19]  # Format timestamp
                conversation_history += f"[{timestamp}] {role}: {msg['content']}\n"
            conversation_history += "\nCURRENT STUDENT QUERY: {user_message}\n\n"

        # Build company summary
        company_summary = ""
        if db_data.get('companies'):
            company_summary = "AVAILABLE COMPANIES & ROLES:\n"
            for company, info in db_data['companies'].items():
                company_summary += f"• {company} ({info['industry'] or 'Industry: Not specified'}, {info['location'] or 'Location: Not specified'})\n"
                for role in info['roles']:
                    company_summary += f"  - {role['title']} ({role['specialization']})\n"
                company_summary += "\n"

        # Build industry insights
        industry_insights = ""
        if db_data.get('industries'):
            industry_insights = "INDUSTRY BREAKDOWN:\n"
            for industry, companies in db_data['industries'].items():
                industry_insights += f"• {industry}: {len(companies)} companies\n"
            industry_insights += "\n"

        # Build specialization insights
        specialization_insights = ""
        if db_data.get('specializations'):
            specialization_insights = "ROLE SPECIALIZATIONS:\n"
            for spec, roles in db_data['specializations'].items():
                specialization_insights += f"• {spec}: {len(roles)} roles\n"
            specialization_insights += "\n"

        prompt = f"""
        You are a senior placement cell representative at Christ University, Bangalore. Your role is to provide comprehensive, strategic guidance to MBA students based EXCLUSIVELY on the internal placement data provided.

        CRITICAL INSTRUCTION: Use ONLY the data provided below. Do NOT use any external knowledge, industry trends, or web-based information. All insights, recommendations, and strategic advice must be derived from the internal database and vector snippets provided.

        {conversation_history}

        INTERNAL PLACEMENT DATABASE INFORMATION:
        {company_summary}
        {industry_insights}
        {specialization_insights}
        Total Companies: {db_data.get('total_companies', 0)}
        Total Roles: {db_data.get('total_roles', 0)}

        INTERNAL JOB DESCRIPTION CONTEXT (from vector database):
        Use these snippets to understand role requirements, company culture, and specific details:

        {vector_snippets}

        IMPORTANT: Base ALL strategic insights, recommendations, and career guidance on these internal snippets and the database information provided above. Do not reference external knowledge.

        AS A PLACEMENT CELL REPRESENTATIVE, PROVIDE PRECISE, STRATEGIC, AND JD-SPECIFIC ACTIONABLE GUIDANCE:

        RESPONSE STRUCTURE (MANDATORY):
        - **EXECUTIVE SUMMARY**: 2-3 bullet points of key strategic insights
        - **COMPANY ANALYSIS**: Bullet points with precise data-driven insights
        - **JD ANALYSIS**: Deep functional area identification and key competency extraction
        - **CERTIFICATIONS & CREDENTIALS**: Specific certifications, courses, and credentials for competitive edge
        - **TECHNICAL PREPARATION**: Role-specific knowledge areas, tools, and software proficiency
        - **STRATEGIC ADVICES**: Competitive positioning, market timing, and differentiation strategies
        - **PRACTICAL PREP STEPS**: JD-aligned simulations, case studies, and exercises
        - **INTERVIEW READINESS**: Domain-specific questions and case formats
        - **ACTION PLAN**: 5-7 precise, time-bound, measurable action items
        - **RISK MITIGATION**: Specific risks and how to address them
        - **FOLLOW-UP ACTIONS**: What to do next with our placement cell

        JD ANALYSIS REQUIREMENTS (CRITICAL):
        - **FUNCTIONAL AREA IDENTIFICATION**: Clearly identify the core functional area (FMCG Sales, Marketing Analytics, Supply Chain, etc.)
        - **KEY COMPETENCY EXTRACTION**: Extract specific skills/competencies required
        - **TECHNICAL KNOWLEDGE AREAS**: Route optimization, numeric distribution, trade coverage, etc.
        - **CERTIFICATIONS/SHORT COURSES**: NielsenIQ FMCG Analytics, Coursera Channel Management, etc.
        - **TOOLS/SOFTWARE PROFICIENCY**: Salesforce FMCG CRM, Power BI, Retailer Dashboards, etc.
        - **PRACTICAL PREPARATION**: GT/MT sales simulations, distributor data analysis, trade negotiation cases
        - **INTERVIEW GUIDANCE**: Domain-specific questions, case formats, performance metrics analysis
        - **NO GENERIC ADVICE**: Every recommendation must map directly to the JD's functional expectations

        RESPONSE REQUIREMENTS:
        - **PURE LINUS TORVALDS PERSONA**: Blunt as Torvalds calling out incompetence, merciless assessment of placement realities
        - **DRY PLACEMENT HUMOR**: Wit about MBA pretensions, placement politics, and career positioning follies
        - **ARISTOTLE STRATEGIC LENS**: Every recommendation serves the telos (ultimate purpose) of career excellence
        - **JD-SPECIFIC ANALYSIS**: Deep functional area identification with competency extraction
        - **TECHNICAL PRECISION**: Role-specific knowledge areas, certifications, tools, and practical prep
        - **INTERVIEW EXPERTISE**: Domain-specific questions and case formats for the exact JD
        - **ULTRA-PRECISE**: Every bullet point must be specific, measurable, and actionable
        - **STRATEGIC DEPTH**: Include competitive positioning, market timing, and opportunity cost analysis
        - **DATA-DRIVEN**: Base ALL insights on verified placement data only - NEVER mention incomplete data or gaps
        - **NO GENERIC ADVICE**: Every recommendation must map directly to the JD's functional expectations
        - **TIME-BOUND ACTIONS**: Include specific deadlines and measurable outcomes
        - **RISK-AWARE**: Address potential rejection points and mitigation strategies
        - **PLACEMENT CELL INTEGRATION**: Reference specific cell resources and next steps
        - **CONVERSATION AWARE**: Consider full conversation history for contextual follow-ups
        - **COMPLETE DATA ONLY**: Work with available verified data - no references to missing information

        REMEMBER: You are analyzing and providing insights based ONLY on Christ University's internal placement database. Do not reference external market trends, industry knowledge, or any information not provided in the data above.

        Generate your comprehensive placement cell response now:
        """

        return prompt
    
    async def _call_placement_cell_llm(self, prompt: str) -> str:
        """Call LLM with full capabilities for placement cell representative"""
        try:
            import requests
            import os
            from dotenv import load_dotenv
            
            # Load environment variables from .env file
            load_dotenv()
            
            # Get API key from .env file
            api_key = os.getenv('OPENROUTER_API_KEY')
            if not api_key:
                print("❌ No OpenRouter API key found in .env file")
                return None
            
            # Prepare comprehensive LLM request
            settings = get_settings()
            payload = {
                "model": settings.OPENROUTER_MODEL or "x-ai/grok-4-fast",  # Use Grok-4 Fast as default
                "messages": [
                    {
                        "role": "system",
                        "content": "You are Linus Torvalds reincarnated as a senior placement cell representative at Christ University, Bangalore. You channel pure Torvalds bluntness - merciless, dry humor, surgical precision, and zero tolerance for MBA pretensions. You cut through career fluff like Torvalds cuts through bad code: direct, unforgiving, and ruthlessly practical. Your responses are blunt assessments of market realities, with dry wit about placement politics and strategic positioning. You NEVER reference technical concepts, kernels, or code metaphors. You focus purely on placement realities: company demands, candidate positioning, competitive edges, and merit-based outcomes. Every insight serves the ultimate purpose (telos) of career success through strategic excellence. You deliver ULTRA-PRECISE, data-driven guidance based EXCLUSIVELY on verified placement data. You NEVER mention incomplete data or data gaps - if information is missing, you work with what's available and state clear limitations. Your tone: Blunt as Torvalds calling out incompetence, humorous about placement follies, surgical in analysis, and relentlessly focused on results."
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.4,  # Balanced temperature for utility-rich strategic insights
                "max_tokens": 1500,  # Longer response for detailed strategic guidance
                "stream": False,
                "top_p": 0.9,  # Allow diverse utility-rich strategic insights
                "frequency_penalty": 0.2,  # Reduce repetition
                "presence_penalty": 0.2  # Encourage diverse strategic insights
            }
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Make API call
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=180
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result["choices"][0]["message"]["content"]
                print(f"✅ Placement cell LLM response generated: {len(llm_response)} characters")
                return llm_response
            else:
                print(f"❌ OpenRouter API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Placement cell LLM call failed: {e}")
            return None
    
    async def _enhanced_database_response(self, user_message: str, db_data: dict) -> str:
        """Enhanced fallback response when LLM is not available"""
        try:
            user_message_lower = user_message.lower()
            
            # Check for accounting/finance queries
            if any(word in user_message_lower for word in ['accounting', 'finance', 'account']):
                return self._generate_accounting_insights(db_data)
            
            # Check for company-specific queries
            elif any(word in user_message_lower for word in ['masters', 'mill story', 'tap academy', 'accorian', 'madison', 'target']):
                return self._generate_company_insights(db_data, user_message_lower)
            
            # Check for count queries
            elif any(word in user_message_lower for word in ['how many', 'count', 'companies']):
                return self._generate_count_insights(db_data)
            
            # Default: comprehensive overview
            else:
                return self._generate_comprehensive_overview(db_data)
                
        except Exception as e:
            print(f"❌ Enhanced response error: {e}")
            return f"Error generating enhanced response: {str(e)}"
    
    def _generate_accounting_insights(self, db_data: dict) -> str:
        """Generate strategic insights for accounting/finance queries"""
        response = "ACCOUNTING & FINANCE CAREER OPPORTUNITIES\n\n"
        response += "As your placement cell representative, I'm excited to share the accounting and finance opportunities available:\n\n"
        
        # Find accounting/finance roles
        accounting_roles = []
        for company, info in db_data.get('companies', {}).items():
            for role in info['roles']:
                if any(word in role['specialization'].lower() for word in ['finance', 'accounting']) or \
                   any(word in role['title'].lower() for word in ['finance', 'accounting', 'account']):
                    accounting_roles.append({
                        'company': company,
                        'title': role['title'],
                        'industry': info['industry'],
                        'location': info['location']
                    })
        
        if accounting_roles:
            response += "Available Opportunities:\n"
            for role in accounting_roles:
                response += f"• {role['title']} at {role['company']}\n"
                response += f"  Industry: {role['industry'] or 'Not specified'}\n"
                response += f"  Location: {role['location'] or 'Not specified'}\n\n"
            
            response += "Strategic Career Insights:\n"
            response += "• These roles offer excellent entry points into corporate finance\n"
            response += "• Perfect for MBA students with finance/accounting specialization\n"
            response += "• Opportunity to work in growing industries with financial operations\n\n"
            
            response += "Preparation Recommendations:\n"
            response += "• Highlight financial modeling and analysis skills\n"
            response += "• Emphasize attention to detail and analytical thinking\n"
            response += "• Research the specific companies and their financial operations\n"
            response += "• Prepare for behavioral questions about financial scenarios\n\n"
            
            response += "Next Steps:\n"
            response += "• Update your resume to highlight relevant financial skills\n"
            response += "• Practice common accounting/finance interview questions\n"
            response += "• Network with finance professionals in these industries\n"
            response += "• Schedule a meeting with our placement cell for personalized guidance\n\n"
            
            response += "This is an excellent opportunity to launch your finance career! Our placement cell is here to support your success."
        else:
            response += "Currently, we don't have specific accounting/finance roles in our database, but I can help you:\n\n"
            response += "• Explore other available opportunities\n"
            response += "• Prepare for future accounting/finance roles\n"
            response += "• Connect with our industry partners\n"
            response += "• Develop relevant skills and certifications\n\n"
            response += "Let's discuss your career goals and find the best path forward!"
        
        return response
    
    def _generate_company_insights(self, db_data: dict, user_message: str) -> str:
        """Generate strategic insights for company-specific queries"""
        # Find which company they're asking about
        companies = ['masters', 'mill story', 'tap academy', 'accorian', 'madison', 'target']
        target_company = None
        
        for company in companies:
            if company in user_message:
                target_company = company
                break
        
        if target_company and target_company in db_data.get('companies', {}):
            company_info = db_data['companies'][target_company]
            
            response = f"STRATEGIC ANALYSIS: {target_company.upper()} OPPORTUNITY\n\n"
            response += "As your placement cell representative, let me provide comprehensive insights about this opportunity:\n\n"
            
            response += "Company Profile:\n"
            response += f"• Industry: {company_info['industry'] or 'Not specified'}\n"
            response += f"• Location: {company_info['location'] or 'Not specified'}\n"
            response += f"• Company Type: {company_info['company_type'] or 'Not specified'}\n\n"
            
            response += "Available Roles:\n"
            for role in company_info['roles']:
                response += f"• {role['title']} ({role['specialization']})\n"
                if role['description']:
                    response += f"  Description: {role['description'][:100]}...\n"
                response += "\n"
            
            response += "Strategic Career Insights:\n"
            if 'masters' in target_company.lower():
                response += "• This is an education sector opportunity with high growth potential\n"
                response += "• Perfect for MBA students interested in education management\n"
                response += "• Chance to work in innovative education models\n"
            elif 'mill story' in target_company.lower():
                response += "• D2C food brand with strong market positioning\n"
                response += "• Excellent for students interested in consumer goods and food industry\n"
                response += "• Opportunity to work in emerging D2C sector\n"
            elif 'tap academy' in target_company.lower():
                response += "• EdTech company with innovative learning solutions\n"
                response += "• Perfect for MBA students interested in education technology\n"
                response += "• High-growth sector with excellent career prospects\n"
            else:
                response += "• This company offers valuable industry experience\n"
                response += "• Great opportunity for MBA students to gain practical skills\n"
                response += "• Chance to work in a dynamic business environment\n"
            
            response += "\nPreparation Recommendations:\n"
            response += "• Research the company's business model and growth trajectory\n"
            response += "• Understand the industry trends and challenges\n"
            response += "• Prepare for role-specific technical questions\n"
            response += "• Highlight relevant coursework and projects\n"
            response += "• Practice behavioral questions about industry scenarios\n\n"
            
            response += "Next Steps:\n"
            response += "• Schedule a mock interview with our placement cell\n"
            response += "• Research the company's recent news and developments\n"
            response += "• Connect with alumni working in similar industries\n"
            response += "• Prepare a tailored resume for this specific role\n\n"
            
            response += "This is an excellent opportunity! Our placement cell is here to support your preparation and success."
            
            return response
        else:
            return "I'd be happy to help you explore opportunities at specific companies. Please let me know which company you're interested in, and I'll provide comprehensive insights and strategic guidance."
    
    def _generate_count_insights(self, db_data: dict) -> str:
        """Generate strategic insights for count queries"""
        response = "PLACEMENT OPPORTUNITIES OVERVIEW\n\n"
        response += "As your placement cell representative, I'm pleased to share our current placement landscape:\n\n"
        
        response += "Current Opportunities:\n"
        response += f"• Total Companies: {db_data.get('total_companies', 0)}\n"
        response += f"• Total Roles Available: {db_data.get('total_roles', 0)}\n\n"
        
        if db_data.get('companies'):
            response += "Participating Companies:\n"
            for company, info in db_data['companies'].items():
                response += f"• {company} ({info['industry'] or 'Industry: Not specified'})\n"
                response += f"  Location: {info['location'] or 'Not specified'}\n"
                response += f"  Roles: {len(info['roles'])} position(s)\n\n"
        
        if db_data.get('industries'):
            response += "Industry Diversity:\n"
            for industry, companies in db_data['industries'].items():
                response += f"• {industry}: {len(companies)} companies\n"
            response += "\n"
        
        response += "Strategic Insights:\n"
        response += "• We have a diverse range of industries represented\n"
        response += "• Multiple roles available across different specializations\n"
        response += "• Excellent opportunities for various MBA specializations\n"
        response += "• Strong representation from growing sectors\n\n"
        
        response += "Recommendations:\n"
        response += "• Explore opportunities across different industries\n"
        response += "• Consider roles that align with your specialization\n"
        response += "• Don't limit yourself to familiar companies\n"
        response += "• Take advantage of our placement cell resources\n\n"
        
        response += "Next Steps:\n"
        response += "• Schedule a career counseling session\n"
        response += "• Attend our company presentation sessions\n"
        response += "• Prepare for multiple interview opportunities\n"
        response += "• Network with company representatives\n\n"
        
        response += "This is an excellent placement season! Our team is here to guide you to success."
        
        return response
    
    def _generate_comprehensive_overview(self, db_data: dict) -> str:
        """Generate comprehensive overview for general queries"""
        response = "CHRIST UNIVERSITY PLACEMENT CELL - COMPREHENSIVE OVERVIEW\n\n"
        response += "Welcome! As your placement cell representative, I'm here to guide you through our placement opportunities:\n\n"
        
        response += "Current Placement Landscape:\n"
        response += f"• Total Companies: {db_data.get('total_companies', 0)}\n"
        response += f"• Total Roles: {db_data.get('total_roles', 0)}\n"
        response += "• Industries Represented: Multiple sectors\n"
        response += "• Geographic Coverage: Various locations across India\n\n"
        
        if db_data.get('companies'):
            response += "Featured Opportunities:\n"
            for company, info in list(db_data['companies'].items())[:5]:  # Show first 5
                response += f"• {company} - {info['industry'] or 'Industry: Not specified'}\n"
                response += f"  Location: {info['location'] or 'Not specified'}\n"
                response += f"  Available Roles: {len(info['roles'])}\n\n"
        
        response += "How I Can Help You:\n"
        response += "• Career Counseling: Personalized guidance based on your goals\n"
        response += "• Company Insights: Detailed analysis of participating companies\n"
        response += "• Role Matching: Find opportunities that fit your specialization\n"
        response += "• Interview Preparation: Mock interviews and skill development\n"
        response += "• Industry Knowledge: Market trends and growth insights\n"
        response += "• Strategic Planning: Long-term career development\n\n"
        
        response += "Available Specializations:\n"
        if db_data.get('specializations'):
            for spec, roles in list(db_data['specializations'].items())[:8]:  # Show first 8
                response += f"• {spec}: {len(roles)} roles\n"
        response += "\n"
        
        response += "Next Steps:\n"
        response += "• Tell me about your specific interests or questions\n"
        response += "• Ask about particular companies or roles\n"
        response += "• Get strategic career advice\n"
        response += "• Schedule a personalized counseling session\n\n"
        
        response += "I'm here to be your placement partner and guide you to success! What would you like to know more about?"
        
        return response

    def _validate_and_correct_response(self, raw_response: str, user_message: str) -> Optional[str]:
        """
        Applies hallucination prevention for company count queries.
        If the LLM response seems to be a count but doesn't match the expected format,
        it will be corrected to a more accurate count based on the database.
        """
        if "companies" in user_message.lower() and "how many" in user_message.lower():
            try:
                # Attempt to extract a number from the raw response
                number_str = ''.join(filter(str.isdigit, raw_response))
                if number_str:
                    count = int(number_str)
                    
                    # Connect to database to get the actual count of COMPANIES (not roles)
                    import sqlite3
                    conn = sqlite3.connect('data/placement_data.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM companies")
                    actual_count = cursor.fetchone()[0]
                    conn.close()
                    
                    if count != actual_count:
                        print(f"⚠️ LLM hallucination detected for company count. Correcting from {count} to {actual_count}")
                        return f"Based on our verified database, there are {actual_count} companies with placement roles."
                elif "total" in raw_response.lower() and "companies" in raw_response.lower():
                    # If LLM response is "total companies" or similar, try to extract a number
                    number_str = ''.join(filter(str.isdigit, raw_response))
                    if number_str:
                        count = int(number_str)
                        
                        # Connect to database to get the actual count of COMPANIES (not roles)
                        import sqlite3
                        conn = sqlite3.connect('data/placement_data.db')
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM companies")
                        actual_count = cursor.fetchone()[0]
                        conn.close()
                        
                        if count != actual_count:
                            print(f"⚠️ LLM hallucination detected for company count. Correcting from {count} to {actual_count}")
                            return f"Based on our verified database, there are {actual_count} companies with placement roles."
            except ValueError:
                pass # If number extraction fails, do nothing
        return None # No correction needed

# Global instance
chat_service = ChatService()
