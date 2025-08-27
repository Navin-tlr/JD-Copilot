"""
Chat Memory System for Context-Aware Conversations
Provides comprehensive conversation tracking and context resolution
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class ChatMessage:
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    query_type: Optional[str] = None
    specialization: Optional[str] = None
    entities_mentioned: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class ConversationMemory:
    """Manages conversation history with context-aware capabilities"""
    
    def __init__(self, session_id: str = "default", max_messages: int = 100):
        self.session_id = session_id
        self.max_messages = max_messages
        self.messages: List[ChatMessage] = []
        self.current_context: Dict[str, Any] = {}
        self.storage_path = Path(f"data/chat_sessions/{session_id}.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.load_from_storage()

    def add_message(
        self, 
        role: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None,
        query_type: Optional[str] = None,
        specialization: Optional[str] = None,
        entities_mentioned: Optional[List[str]] = None
    ):
        """Add a new message to conversation memory"""
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {},
            query_type=query_type,
            specialization=specialization,
            entities_mentioned=entities_mentioned or []
        )
        
        self.messages.append(message)
        
        # Update current context
        if role == 'user':
            self._update_context_from_user_query(message)
        elif role == 'assistant':
            self._update_context_from_assistant_response(message)
        
        # Maintain memory limit
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
        
        self.save_to_storage()

    def _update_context_from_user_query(self, message: ChatMessage):
        """Extract and update context from user query"""
        content_lower = message.content.lower()
        
        # Track current topic/specialization
        if message.specialization:
            self.current_context['last_specialization'] = message.specialization
            self.current_context['specialization_timestamp'] = message.timestamp
        
        # Track query type
        if message.query_type:
            self.current_context['last_query_type'] = message.query_type
        
        # Track entities mentioned
        if message.entities_mentioned:
            self.current_context['last_entities'] = message.entities_mentioned
            self.current_context['entities_timestamp'] = message.timestamp

        # Track specific question patterns
        if any(phrase in content_lower for phrase in ['how many companies', 'total companies', 'companies came']):
            self.current_context['last_company_query'] = message.content
            self.current_context['company_query_timestamp'] = message.timestamp
        
        if 'salary' in content_lower:
            self.current_context['last_salary_query'] = message.content
            self.current_context['salary_query_timestamp'] = message.timestamp

    def _update_context_from_assistant_response(self, message: ChatMessage):
        """Extract context from assistant responses"""
        content_lower = message.content.lower()
        
        # Extract companies mentioned in response
        companies = self._extract_companies_from_response(message.content)
        if companies:
            self.current_context['last_companies_mentioned'] = companies
            self.current_context['companies_mentioned_timestamp'] = message.timestamp
        
        # Extract numbers/statistics
        numbers = self._extract_numbers_from_response(message.content)
        if numbers:
            self.current_context['last_numbers_mentioned'] = numbers

    def _extract_companies_from_response(self, content: str) -> List[str]:
        """Extract company names from assistant response"""
        # Look for patterns like "Companies: Madison PR, Tap Academy, Target"
        company_pattern = r'(?:Companies:|Company:)\s*([^*\n]+)'
        matches = re.findall(company_pattern, content, re.IGNORECASE)
        
        companies = []
        for match in matches:
            # Split by commas and clean up
            company_list = [c.strip() for c in match.split(',') if c.strip()]
            companies.extend(company_list)
        
        return companies

    def _extract_numbers_from_response(self, content: str) -> Dict[str, str]:
        """Extract numerical information from response"""
        numbers = {}
        
        # Extract total companies count
        total_pattern = r'Total Companies:\*\*\s*(\d+)'
        match = re.search(total_pattern, content)
        if match:
            numbers['total_companies'] = match.group(1)
        
        # Extract salary information
        salary_patterns = [
            (r'Average Min Salary:\*\*\s*([^*\n]+)', 'avg_min_salary'),
            (r'Average Max Salary:\*\*\s*([^*\n]+)', 'avg_max_salary'),
            (r'Salary Range:\*\*\s*([^*\n]+)', 'salary_range')
        ]
        
        for pattern, key in salary_patterns:
            match = re.search(pattern, content)
            if match:
                numbers[key] = match.group(1).strip()
        
        return numbers

    def is_contextual_query(self, query: str) -> bool:
        """Determine if query requires context from previous conversation"""
        query_lower = query.lower().strip()
        
        # Contextual patterns
        contextual_patterns = [
            # Direct references
            r'\bthat\b', r'\bthis\b', r'\bit\b', r'\bthey\b', r'\bthem\b', r'\bthose\b', r'\bthese\b',
            # Implicit references
            r'^(give|show|tell)\s+(me\s+)?(more\s+)?details',
            r'^(what|which)\s+(about|are)',
            r'^(can\s+you\s+)?(tell|show|give)\s+(me\s+)?(more|about)',
            r'^(expand\s+on|elaborate\s+on)',
            r'^(more\s+)?(info|information|details)',
            r'^explain\s+(that|this|it)',
            r'^(break\s+down|breakdown)',
            r'^(list|name)\s+(them|those)',
            # Follow-up questions
            r'^(and\s+)?(what|which|who|how|when|where)',
            r'^(also|additionally)',
            r'^(so\s+)?which\s+companies',
            r'^(any|other)\s+',
            # Comparative questions
            r'^(compare|vs|versus)',
            r'^(how\s+does\s+)?(that|this|it)\s+compare',
            # Clarification requests
            r'^(what\s+do\s+you\s+mean|clarify|explain)',
            r'^(i\s+don\'t\s+understand|confused)',
        ]
        
        return any(re.search(pattern, query_lower) for pattern in contextual_patterns)

    def resolve_context(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """Resolve contextual references in the query"""
        if not self.is_contextual_query(query):
            return query, {}
        
        resolved_query = query
        context_info = {}
        
        # Get recent conversation context
        recent_context = self.get_recent_context(max_messages=10)
        
        # Resolve based on query patterns
        query_lower = query.lower().strip()
        
        # Handle direct references to previous topics
        if any(word in query_lower for word in ['that', 'this', 'it', 'them', 'those']):
            resolved_query, context_info = self._resolve_direct_references(query, recent_context)
        
        # Handle detail requests
        elif re.search(r'^(give|show|tell).*(details|more|info)', query_lower):
            resolved_query, context_info = self._resolve_detail_requests(query, recent_context)
        
        # Handle follow-up questions
        elif re.search(r'^(which|what|who|how).*companies', query_lower):
            resolved_query, context_info = self._resolve_company_questions(query, recent_context)
        
        # Handle comparative questions
        elif re.search(r'(compare|vs|versus)', query_lower):
            resolved_query, context_info = self._resolve_comparative_questions(query, recent_context)
        
        return resolved_query, context_info

    def _resolve_direct_references(self, query: str, context: str) -> Tuple[str, Dict[str, Any]]:
        """Resolve direct references like 'that', 'this', 'it'"""
        context_info = {}
        
        # Find the most recent topic/specialization
        if 'last_specialization' in self.current_context:
            specialization = self.current_context['last_specialization']
            context_info['specialization'] = specialization
            
            # Replace contextual words with specific references
            resolved = query
            replacements = {
                r'\bthat\b': f'the {specialization} information',
                r'\bthis\b': f'the {specialization} data',
                r'\bit\b': f'the {specialization} results',
                r'\bthey\b': f'the {specialization} companies',
                r'\bthem\b': f'the {specialization} companies',
                r'\bthose\b': f'those {specialization} companies',
                r'\bthese\b': f'these {specialization} companies'
            }
            
            for pattern, replacement in replacements.items():
                resolved = re.sub(pattern, replacement, resolved, flags=re.IGNORECASE)
            
            # Add context from last query
            if 'last_company_query' in self.current_context:
                context_info['previous_query'] = self.current_context['last_company_query']
                resolved = f"Based on the previous query about {specialization}: {resolved}"
        
        return resolved, context_info

    def _resolve_detail_requests(self, query: str, context: str) -> Tuple[str, Dict[str, Any]]:
        """Resolve requests for more details"""
        context_info = {}
        
        if 'last_specialization' in self.current_context:
            specialization = self.current_context['last_specialization']
            context_info['specialization'] = specialization
            
            # If companies were mentioned, ask for details about them
            if 'last_companies_mentioned' in self.current_context:
                companies = self.current_context['last_companies_mentioned']
                resolved = f"Which companies recruited for {specialization} roles? Give details about: {', '.join(companies)}"
                context_info['companies'] = companies
            else:
                resolved = f"Which companies recruited for {specialization} roles?"
            
            context_info['request_type'] = 'details'
            context_info['entity'] = 'companies'
            return resolved, context_info
        
        return query, context_info

    def _resolve_company_questions(self, query: str, context: str) -> Tuple[str, Dict[str, Any]]:
        """Resolve questions about companies"""
        context_info = {}
        
        if 'last_specialization' in self.current_context:
            specialization = self.current_context['last_specialization']
            context_info['specialization'] = specialization
            
            # Replace general company questions with specific ones
            if re.search(r'which companies', query.lower()):
                resolved = re.sub(
                    r'which companies', 
                    f'which companies have {specialization} roles', 
                    query, 
                    flags=re.IGNORECASE
                )
            else:
                resolved = f"{query} for {specialization} roles"
            
            return resolved, context_info
        
        return query, context_info

    def _resolve_comparative_questions(self, query: str, context: str) -> Tuple[str, Dict[str, Any]]:
        """Resolve comparative questions"""
        context_info = {}
        
        if 'last_specialization' in self.current_context:
            specialization = self.current_context['last_specialization']
            context_info['specialization'] = specialization
            context_info['request_type'] = 'comparison'
            
            resolved = f"Compare {specialization} roles: {query}"
            return resolved, context_info
        
        return query, context_info

    def get_recent_context(self, max_messages: int = 5) -> str:
        """Get recent conversation context as formatted string"""
        if not self.messages:
            return ""
        
        recent_messages = self.messages[-max_messages:]
        context_lines = []
        
        for msg in recent_messages:
            role_prefix = "User" if msg.role == "user" else "Assistant"
            context_lines.append(f"{role_prefix}: {msg.content}")
        
        return "\n".join(context_lines)

    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation for LLM context"""
        if not self.messages:
            return ""
        
        summary_parts = []
        
        # Add current context
        if self.current_context:
            if 'last_specialization' in self.current_context:
                summary_parts.append(f"Current topic: {self.current_context['last_specialization']}")
            
            if 'last_companies_mentioned' in self.current_context:
                companies = ', '.join(self.current_context['last_companies_mentioned'][:3])
                summary_parts.append(f"Recently discussed companies: {companies}")
            
            if 'last_numbers_mentioned' in self.current_context:
                numbers = self.current_context['last_numbers_mentioned']
                if 'total_companies' in numbers:
                    summary_parts.append(f"Last company count: {numbers['total_companies']}")
        
        # Add recent context
        recent_context = self.get_recent_context(3)
        if recent_context:
            summary_parts.append(f"Recent conversation:\n{recent_context}")
        
        return "\n".join(summary_parts)

    def save_to_storage(self):
        """Save conversation to persistent storage"""
        try:
            data = {
                'session_id': self.session_id,
                'messages': [msg.to_dict() for msg in self.messages],
                'current_context': self.current_context,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving conversation: {e}")

    def load_from_storage(self):
        """Load conversation from persistent storage"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                self.messages = [ChatMessage.from_dict(msg) for msg in data.get('messages', [])]
                self.current_context = data.get('current_context', {})
                
                # Clean old context (older than 1 hour)
                self._clean_old_context()
        except Exception as e:
            print(f"Error loading conversation: {e}")
            self.messages = []
            self.current_context = {}

    def _clean_old_context(self):
        """Clean context items older than 1 hour"""
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        timestamp_keys = [
            'specialization_timestamp', 'entities_timestamp', 
            'company_query_timestamp', 'salary_query_timestamp',
            'companies_mentioned_timestamp'
        ]
        
        for key in timestamp_keys:
            if key in self.current_context:
                try:
                    timestamp = datetime.fromisoformat(self.current_context[key])
                    if timestamp < cutoff_time:
                        # Remove related context
                        related_key = key.replace('_timestamp', '')
                        if related_key in self.current_context:
                            del self.current_context[related_key]
                        del self.current_context[key]
                except:
                    del self.current_context[key]

    def clear_memory(self):
        """Clear all conversation memory"""
        self.messages = []
        self.current_context = {}
        if self.storage_path.exists():
            self.storage_path.unlink()


class ChatMemoryManager:
    """Manages multiple conversation sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, ConversationMemory] = {}
    
    def get_session(self, session_id: str = "default") -> ConversationMemory:
        """Get or create a conversation session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationMemory(session_id)
        return self.sessions[session_id]
    
    def clear_session(self, session_id: str = "default"):
        """Clear a specific session"""
        if session_id in self.sessions:
            self.sessions[session_id].clear_memory()
            del self.sessions[session_id]


# Global memory manager instance
memory_manager = ChatMemoryManager()
