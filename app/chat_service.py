import asyncio
import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional, Any
from dataclasses import dataclass

# Import your existing RAG components
from .agent import route_query
from .rag import retrieve_snippets, synthesize_answer
from .database import PlacementDatabase
from .config import get_settings

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

class ChatService:
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
        self.messages: Dict[str, List[ChatMessage]] = {}
        
        # Initialize your existing RAG components
        self.db = PlacementDatabase()
    
    async def create_session(self, user_id: str) -> str:
        session_id = str(uuid.uuid4())
        session = ChatSession(
            id=session_id,
            user_id=user_id,
            created_at=datetime.now(),
            last_activity=datetime.now()
        )
        self.sessions[session_id] = session
        self.messages[session_id] = []
        return session_id
    
    async def send_message(self, session_id: str, content: str, user_id: str) -> AsyncGenerator[ChatMessage, None]:
        print(f"🔍 Backend received query: '{content}' from user {user_id}")
        
        # Create session if it doesn't exist
        if session_id not in self.sessions:
            new_session_id = await self.create_session(user_id)
            # Use the new session ID if one was created
            if new_session_id != session_id:
                session_id = new_session_id
        
        # Store user message
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            content=content,
            sender='user',
            timestamp=datetime.now(),
            session_id=session_id
        )
        self.messages[session_id].append(user_message)
        
        # Generate AI response using your RAG system with context
        context = self._build_context(session_id)
        ai_response = await self._generate_rag_response(content, session_id, user_id, context)
        ai_message = ChatMessage(
            id=str(uuid.uuid4()),
            content=ai_response,
            sender='ai',
            timestamp=datetime.now(),
            session_id=session_id
        )
        self.messages[session_id].append(ai_message)
        
        # Update session activity
        if session_id in self.sessions:
            self.sessions[session_id].last_activity = datetime.now()
        
        yield ai_message
    
    def _build_context(self, session_id: str) -> Dict[str, Any]:
        """Build context from conversation history"""
        context = {
            'previous_companies': [],
            'previous_roles': [],
            'previous_specializations': []
        }
        
        if session_id in self.messages:
            # Look at recent messages to extract entities
            recent_messages = self.messages[session_id][-10:]  # Last 10 messages
            
            for message in recent_messages:
                content = message.content.lower()
                
                # Extract company names (simple pattern matching)
                companies = ['acuity', 'mill story', 'madison pr', 'masters union', 'target', 'tap academy', 'withum', 'accorian', 'wns', 'turtle shell']
                for company in companies:
                    if company in content and company not in context['previous_companies']:
                        context['previous_companies'].append(company.title())
                
                # Extract roles (simple pattern matching)
                roles = ['analyst', 'intern', 'associate', 'counselor', 'executive', 'assistant', 'trainee']
                for role in roles:
                    if role in content and role not in context['previous_roles']:
                        context['previous_roles'].append(role.title())
        
        return context
    
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
                    response = await self._handle_unstructured_query(user_message)
                elif routing_decision == "HYBRID":
                    print(f"🔍 Processing as HYBRID query")
                    response = await self._handle_hybrid_query(user_message)
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
            # Fallback to placement cell LLM if routing fails
            try:
                response = await self._placement_cell_llm_response(user_message)
                return self._format_response(response, user_message)
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")
                return f"I'm sorry, I encountered an error while processing your query. Please try rephrasing your question."
    
    async def _handle_structured_query(self, user_message: str) -> str:
        """Handle structured queries using LlamaIndex SQL engine"""
        try:
            # Check if this is a query that needs comprehensive reporting (like HR roles)
            if any(keyword in user_message.lower() for keyword in ["hr role", "hr position", "human resources", "people operations"]):
                print(f"🔍 HR role query detected, using placement cell LLM for comprehensive report")
                return await self._placement_cell_llm_response(user_message)
            
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
            return f"I encountered an error processing this structured query: {str(e)}"
    
    async def _handle_unstructured_query(self, user_message: str) -> str:
        """Handle unstructured queries using RAG system"""
        try:
            from .rag import retrieve_snippets, synthesize_answer
            
            # Use existing RAG system
            snippets = retrieve_snippets(user_message, top_k=15, filters={})
            if snippets:
                answer = synthesize_answer(user_message, snippets, {})
                # CRITICAL FIX: Don't fallback to generic message - use the actual answer
                if answer:
                    return answer
                else:
                    return "I could not find relevant information to answer your question based on the available documents."
            else:
                return "I couldn't find any relevant information in the available documents."
                
        except Exception as e:
            print(f"❌ Unstructured query error: {e}")
            return f"I encountered an error processing this unstructured query: {str(e)}"
    
    async def _handle_hybrid_query(self, user_message: str) -> str:
        """Handle hybrid queries using both structured and unstructured data"""
        try:
            # Get structured data first
            structured_answer = await self._handle_structured_query(user_message)
            
            # Get RAG insights
            rag_answer = await self._handle_unstructured_query(user_message)
            
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
            return f"I encountered an error processing this hybrid query: {str(e)}"
    
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
        """Format responses into structured, visually appealing layout matching Notion document style"""
        if not response:
            return response
        
        # Remove markdown formatting
        response = response.replace('**', '').replace('###', '').replace('##', '').replace('#', '')
        
        # Clean up extra whitespace but preserve line breaks
        lines = response.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)
        
        # Join with proper spacing
        formatted_response = '\n\n'.join(cleaned_lines)
        
        # Generate dynamic, query-specific heading based on user message
        heading = self._generate_query_specific_heading(user_message)
        
        # Add structured formatting with dynamic heading
        return f"""{heading}

{formatted_response}

---
For more detailed information or specific questions, please ask follow-up questions."""
    
    def _generate_query_specific_heading(self, user_message: str) -> str:
        """Generate dynamic, query-specific heading based on user message"""
        if not user_message:
            return "CHRIST UNIVERSITY PLACEMENT CELL RESPONSE"
        
        user_message_lower = user_message.lower()
        
        # Full JD requests
        if any(phrase in user_message_lower for phrase in [
            "full jd", "complete jd", "entire jd", "full job description", 
            "complete job description", "entire job description", "show me jd", "give jd"
        ]):
            # Extract company name for personalized heading
            company_name = self._extract_company_name(user_message)
            if company_name:
                return f"CHRIST UNIVERSITY PLACEMENT CELL - FULL JOB DESCRIPTION: {company_name.upper()}"
            else:
                return "CHRIST UNIVERSITY PLACEMENT CELL - COMPLETE JOB DESCRIPTION"
        
        # Company-specific queries
        elif any(word in user_message_lower for word in ["company", "role", "position", "job"]):
            company_name = self._extract_company_name(user_message)
            if company_name:
                return f"CHRIST UNIVERSITY PLACEMENT CELL - COMPANY ANALYSIS: {company_name.upper()}"
            else:
                return "CHRIST UNIVERSITY PLACEMENT CELL - COMPANY INSIGHTS"
        
        # Skills queries
        elif any(word in user_message_lower for word in ["skills", "requirements", "qualifications"]):
            return "CHRIST UNIVERSITY PLACEMENT CELL - SKILLS & REQUIREMENTS ANALYSIS"
        
        # Salary/compensation queries
        elif any(word in user_message_lower for word in ["salary", "compensation", "pay", "lpa"]):
            return "CHRIST UNIVERSITY PLACEMENT CELL - COMPENSATION INSIGHTS"
        
        # Count/overview queries
        elif any(word in user_message_lower for word in ["how many", "count", "list", "overview"]):
            return "CHRIST UNIVERSITY PLACEMENT CELL - PLACEMENT OVERVIEW"
        
        # Strategic advice queries
        elif any(word in user_message_lower for word in ["advice", "strategy", "recommendations", "insights"]):
            return "CHRIST UNIVERSITY PLACEMENT CELL - STRATEGIC INSIGHTS"
        
        # Default heading
        else:
            return "CHRIST UNIVERSITY PLACEMENT CELL RESPONSE"
    
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
        return self.messages.get(session_id, [])
    
    async def get_user_sessions(self, user_id: str) -> List[ChatSession]:
        return [session for session in self.sessions.values() if session.user_id == user_id]
    
    async def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            del self.messages[session_id]
            return True
        return False

    async def _handle_multi_hop_query(self, user_message: str) -> str:
        """Handle multi-hop queries requiring sequential reasoning"""
        try:
            # For multi-hop queries, use the placement cell LLM as it can handle complex reasoning
            print(f"🔍 Multi-hop query detected, using placement cell LLM for complex reasoning")
            return await self._placement_cell_llm_response(user_message)
            
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
            llm_prompt = self._create_placement_cell_prompt(user_message, db_data, vector_snippets)
            
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
        """Get relevant vector snippets for enhanced context"""
        try:
            # Use your existing RAG system to get relevant snippets
            from .rag import retrieve_snippets
            
            # Get more comprehensive snippets for better internal context
            snippets = retrieve_snippets(user_message, top_k=15, filters={})
            
            if snippets:
                snippet_text = "INTERNAL JOB DESCRIPTION CONTEXT (from vector database):\n"
                snippet_text += "Use these snippets to understand role requirements, company culture, and specific details:\n\n"
                
                for i, snippet in enumerate(snippets, 1):
                    # Get more context from each snippet - handle different snippet types
                    try:
                        if isinstance(snippet, str):
                            snippet_content = snippet[:300] if len(snippet) > 300 else snippet
                        elif hasattr(snippet, 'text'):
                            snippet_content = snippet.text[:300] if len(snippet.text) > 300 else snippet.text
                        elif hasattr(snippet, 'content'):
                            snippet_content = snippet.content[:300] if len(snippet.content) > 300 else snippet.content
                        else:
                            snippet_content = str(snippet)[:300]
                        
                        snippet_text += f"{i}. {snippet_content}...\n\n"
                    except Exception as e:
                        print(f"⚠️ Snippet processing error: {e}")
                        snippet_text += f"{i}. {str(snippet)[:200]}...\n\n"
                
                snippet_text += "IMPORTANT: Base ALL strategic insights, recommendations, and career guidance on these internal snippets and the database information provided above. Do not reference external knowledge."
                return snippet_text
            else:
                return "INTERNAL JOB DESCRIPTION CONTEXT: No specific job description snippets available for this query. Base all insights on the database company and role information provided above."
                
        except Exception as e:
            print(f"❌ Vector snippets error: {e}")
            return "INTERNAL JOB DESCRIPTION CONTEXT: Vector search not available for this query. Base all insights on the database company and role information provided above."
    
    def _create_placement_cell_prompt(self, user_message: str, db_data: dict, vector_snippets: str) -> str:
        """Create comprehensive prompt for placement cell representative"""
        
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

        STUDENT QUERY: {user_message}

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

        AS A PLACEMENT CELL REPRESENTATIVE, PROVIDE:

        1. **QUERY ANALYSIS**: Understand what the student is really asking for
        2. **STRATEGIC INSIGHTS**: Based ONLY on the internal company and role data provided
        3. **SPECIFIC RECOMMENDATIONS**: Derived from actual available roles and companies in our database
        4. **CAREER GUIDANCE**: How to approach these specific opportunities strategically
        5. **PREPARATION TIPS**: Based on the actual role requirements and company information provided
        6. **COMPANY INSIGHTS**: Analysis based ONLY on the internal company data (industry, location, company type)
        7. **NEXT STEPS**: Actionable advice specific to the opportunities in our database

        RESPONSE REQUIREMENTS:
        - Professional, warm, and encouraging tone as Christ University placement cell
        - Clear sections with bullet points
        - ALL insights must be based on the internal data provided
        - NO generic industry knowledge or web-based information
        - Specific company and role recommendations from our database
        - Strategic insights derived from the actual company and role data
        - Actionable next steps

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
                "model": settings.OPENROUTER_MODEL or "moonshotai/kimi-k2:free",  # High-capability model
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are a senior placement cell representative at Christ University, Bangalore. You provide comprehensive, strategic guidance to MBA students based EXCLUSIVELY on internal placement data. You do NOT use external knowledge, industry trends, or web-based information. All insights, recommendations, and strategic advice must be derived from the internal database and vector snippets provided. You are an expert at analyzing internal data and providing actionable career guidance based on real opportunities available in Christ University's placement database."
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.4,  # Balanced creativity and accuracy
                "max_tokens": 1200,  # Longer response for comprehensive guidance
                "stream": False,
                "top_p": 0.9,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.1
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
                timeout=45
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
