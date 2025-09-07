"""
Enhanced Chat Memory System with Durable Workflow Integration
Integrates the new LlamaIndex durable workflow features with existing chat memory.
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from .chat_memory import ChatMessage, ConversationMemory, ChatMemoryManager
from .durable_workflow import (
    DurableWorkflowManager, 
    ContextStateStore, 
    WorkflowInstanceStorage,
    ExternalCheckpointer,
    durable_workflow_manager
)


class EnhancedConversationMemory(ConversationMemory):
    """Enhanced conversation memory with durable workflow integration"""
    
    def __init__(self, session_id: str = "default", max_messages: int = 100, user_id: str = "anonymous"):
        super().__init__(session_id, max_messages)
        self.user_id = user_id
        self.workflow_manager = durable_workflow_manager
        self.workflow_instance = None
        # Note: _initialize_workflow() will be called when first message is added
    
    async def _initialize_workflow(self):
        """Initialize durable workflow for this conversation"""
        try:
            # Check if workflow already exists
            existing_instance = await self.workflow_manager.instance_storage.get_instance_by_session(self.session_id)
            
            if existing_instance:
                self.workflow_instance = existing_instance
                print(f"✅ Restored existing workflow for session {self.session_id}")
            else:
                # Create new workflow
                self.workflow_instance = await self.workflow_manager.create_workflow(
                    self.session_id, 
                    self.user_id,
                    {
                        "max_messages": self.max_messages,
                        "created_from": "enhanced_chat_memory"
                    }
                )
                print(f"✅ Created new durable workflow for session {self.session_id}")
        except Exception as e:
            print(f"⚠️ Could not initialize workflow for session {self.session_id}: {e}")
    
    async def add_message(
        self, 
        role: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None,
        query_type: Optional[str] = None,
        specialization: Optional[str] = None,
        entities_mentioned: Optional[List[str]] = None
    ):
        """Enhanced add_message with workflow integration"""
        # Initialize workflow if not already done
        if self.workflow_instance is None:
            await self._initialize_workflow()
        
        # Call parent method
        super().add_message(role, content, metadata, query_type, specialization, entities_mentioned)
        
        # Update workflow state
        await self._update_workflow_state(role, content, metadata, query_type, specialization, entities_mentioned)
    
    async def _update_workflow_state(
        self, 
        role: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None,
        query_type: Optional[str] = None,
        specialization: Optional[str] = None,
        entities_mentioned: Optional[List[str]] = None
    ):
        """Update workflow state based on new message"""
        if not self.workflow_instance:
            return
        
        try:
            # Update context state
            context_updates = {}
            
            if role == 'user':
                # Analyze user query for context updates
                context_updates.update(await self._analyze_user_query(content, query_type, specialization))
                
                # Track entities
                if entities_mentioned:
                    for entity in entities_mentioned:
                        await self.workflow_manager.context_store.add_entity(
                            self.session_id, 
                            "mentioned_entities", 
                            entity
                        )
                
                # Update workflow stage based on conversation depth
                await self._update_workflow_stage(content)
            
            elif role == 'assistant':
                # Analyze assistant response
                context_updates.update(await self._analyze_assistant_response(content))
            
            # Apply context updates
            if context_updates:
                await self.workflow_manager.update_workflow_state(self.session_id, **context_updates)
            
            # Create message checkpoint for important interactions
            if self._should_checkpoint(role, content):
                await self._create_message_checkpoint(role, content, metadata)
        
        except Exception as e:
            print(f"⚠️ Error updating workflow state: {e}")
    
    async def _analyze_user_query(self, content: str, query_type: str = None, specialization: str = None) -> Dict[str, Any]:
        """Analyze user query for context updates"""
        updates = {}
        content_lower = content.lower()
        
        # Track current topic/specialization
        if specialization:
            updates['current_topic'] = specialization
            await self.workflow_manager.context_store.add_entity(
                self.session_id, 
                "specializations", 
                specialization
            )
        
        # Track query patterns
        if query_type:
            updates['last_query_type'] = query_type
        
        # Analyze conversation patterns
        if any(phrase in content_lower for phrase in ['how many', 'total', 'count']):
            updates['query_patterns'] = self._add_query_pattern("counting_queries")
        
        if any(phrase in content_lower for phrase in ['compare', 'versus', 'vs', 'difference']):
            updates['query_patterns'] = self._add_query_pattern("comparison_queries")
        
        if any(phrase in content_lower for phrase in ['details', 'more info', 'explain']):
            updates['query_patterns'] = self._add_query_pattern("detail_requests")
        
        # Track user preferences
        if 'salary' in content_lower:
            updates['user_preferences'] = self._update_user_preferences("interested_in_salary", True)
        
        if any(word in content_lower for word in ['remote', 'work from home', 'hybrid']):
            updates['user_preferences'] = self._update_user_preferences("interested_in_remote_work", True)
        
        return updates
    
    async def _analyze_assistant_response(self, content: str) -> Dict[str, Any]:
        """Analyze assistant response for context updates"""
        updates = {}
        
        # Extract and track companies mentioned
        companies = self._extract_companies_from_response(content)
        if companies:
            for company in companies:
                await self.workflow_manager.context_store.add_entity(
                    self.session_id, 
                    "companies_discussed", 
                    company
                )
        
        # Extract numerical data
        numbers = self._extract_numbers_from_response(content)
        if numbers:
            updates['last_numbers_mentioned'] = numbers
        
        # Update conversation summary
        if len(self.messages) > 5:  # Only update summary for longer conversations
            updates['conversation_summary'] = await self._generate_conversation_summary()
        
        return updates
    
    def _add_query_pattern(self, pattern: str) -> List[str]:
        """Add a query pattern to the tracked patterns"""
        context = self.workflow_manager.context_store._active_contexts.get(self.session_id)
        if context:
            if pattern not in context.query_patterns:
                context.query_patterns.append(pattern)
            return context.query_patterns
        return [pattern]
    
    def _update_user_preferences(self, preference: str, value: Any) -> Dict[str, Any]:
        """Update user preferences"""
        context = self.workflow_manager.context_store._active_contexts.get(self.session_id)
        if context:
            context.user_preferences[preference] = value
            return context.user_preferences
        return {preference: value}
    
    async def _update_workflow_stage(self, content: str):
        """Update workflow stage based on conversation depth and content"""
        message_count = len(self.messages)
        content_lower = content.lower()
        
        if message_count <= 2:
            stage = "initial"
        elif message_count <= 10:
            stage = "active"
        elif any(word in content_lower for word in ['deep dive', 'detailed analysis', 'comprehensive']):
            stage = "deep_dive"
        elif any(word in content_lower for word in ['summary', 'overview', 'conclusion']):
            stage = "summary"
        else:
            stage = "active"
        
        await self.workflow_manager.context_store.update_workflow_stage(self.session_id, stage)
    
    def _should_checkpoint(self, role: str, content: str) -> bool:
        """Determine if this message should trigger a checkpoint"""
        # Checkpoint for important user queries
        if role == 'user':
            important_patterns = [
                r'how many companies',
                r'compare.*companies',
                r'salary.*range',
                r'which companies.*hire',
                r'details.*about'
            ]
            return any(re.search(pattern, content.lower()) for pattern in important_patterns)
        
        # Checkpoint for long assistant responses
        if role == 'assistant' and len(content) > 500:
            return True
        
        return False
    
    async def _create_message_checkpoint(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Create a checkpoint for an important message"""
        try:
            checkpoint_data = {
                "message_role": role,
                "message_content": content[:200] + "..." if len(content) > 200 else content,
                "message_count": len(self.messages),
                "workflow_stage": await self._get_current_workflow_stage(),
                "metadata": metadata or {}
            }
            
            await self.workflow_manager.checkpointer.create_checkpoint(
                self.session_id,
                checkpoint_data,
                "important_message"
            )
        except Exception as e:
            print(f"⚠️ Error creating message checkpoint: {e}")
    
    async def _get_current_workflow_stage(self) -> str:
        """Get current workflow stage"""
        try:
            context = await self.workflow_manager.context_store.get_context(self.session_id)
            return context.workflow_stage
        except:
            return "unknown"
    
    async def _generate_conversation_summary(self) -> str:
        """Generate a summary of the conversation for context"""
        if len(self.messages) < 3:
            return ""
        
        # Get recent messages
        recent_messages = self.messages[-5:]
        
        # Extract key topics and entities
        topics = set()
        entities = set()
        
        for msg in recent_messages:
            if msg.role == 'user':
                # Extract topics from user queries
                if msg.specialization:
                    topics.add(msg.specialization)
                if msg.query_type:
                    topics.add(msg.query_type)
        
        # Get tracked entities from context
        try:
            tracked_entities = await self.workflow_manager.context_store.get_entities(self.session_id)
            for entity_type, entity_list in tracked_entities.items():
                entities.update(entity_list[:3])  # Limit to top 3 per type
        except:
            pass
        
        # Generate summary
        summary_parts = []
        if topics:
            summary_parts.append(f"Topics discussed: {', '.join(list(topics)[:3])}")
        if entities:
            summary_parts.append(f"Key entities: {', '.join(list(entities)[:5])}")
        
        return "; ".join(summary_parts)
    
    async def get_enhanced_context(self) -> Dict[str, Any]:
        """Get enhanced context including workflow state"""
        base_context = self.get_conversation_summary()
        
        try:
            # Get workflow status
            workflow_status = await self.workflow_manager.get_workflow_status(self.session_id)
            
            # Get context state
            context_state = await self.workflow_manager.context_store.get_context(self.session_id)
            
            return {
                "base_context": base_context,
                "workflow_status": workflow_status,
                "context_state": asdict(context_state),
                "message_count": len(self.messages),
                "session_duration": self._calculate_session_duration()
            }
        except Exception as e:
            print(f"⚠️ Error getting enhanced context: {e}")
            return {
                "base_context": base_context,
                "message_count": len(self.messages),
                "error": str(e)
            }
    
    def _calculate_session_duration(self) -> str:
        """Calculate session duration"""
        if not self.messages:
            return "0 minutes"
        
        first_message = self.messages[0].timestamp
        last_message = self.messages[-1].timestamp
        duration = last_message - first_message
        
        if duration.total_seconds() < 60:
            return f"{int(duration.total_seconds())} seconds"
        elif duration.total_seconds() < 3600:
            return f"{int(duration.total_seconds() / 60)} minutes"
        else:
            return f"{int(duration.total_seconds() / 3600)} hours"
    
    async def pause_conversation(self, reason: str = "user_requested"):
        """Pause the conversation workflow"""
        try:
            await self.workflow_manager.pause_workflow(self.session_id, reason)
            print(f"✅ Conversation {self.session_id} paused: {reason}")
        except Exception as e:
            print(f"⚠️ Error pausing conversation: {e}")
    
    async def resume_conversation(self) -> bool:
        """Resume the conversation workflow"""
        try:
            success = await self.workflow_manager.resume_workflow(self.session_id)
            if success:
                print(f"✅ Conversation {self.session_id} resumed")
            return success
        except Exception as e:
            print(f"⚠️ Error resuming conversation: {e}")
            return False
    
    async def get_workflow_insights(self) -> Dict[str, Any]:
        """Get insights about the conversation workflow"""
        try:
            workflow_status = await self.workflow_manager.get_workflow_status(self.session_id)
            if not workflow_status:
                return {"error": "No workflow found"}
            
            # Get checkpoints
            checkpoints = await self.workflow_manager.checkpointer.list_checkpoints(self.session_id)
            
            # Analyze conversation patterns
            patterns = self._analyze_conversation_patterns()
            
            return {
                "workflow_status": workflow_status,
                "checkpoint_count": len(checkpoints),
                "conversation_patterns": patterns,
                "session_health": self._assess_session_health()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _analyze_conversation_patterns(self) -> Dict[str, Any]:
        """Analyze conversation patterns"""
        if len(self.messages) < 2:
            return {"status": "insufficient_data"}
        
        user_messages = [msg for msg in self.messages if msg.role == 'user']
        assistant_messages = [msg for msg in self.messages if msg.role == 'assistant']
        
        # Calculate average message lengths
        avg_user_length = sum(len(msg.content) for msg in user_messages) / len(user_messages) if user_messages else 0
        avg_assistant_length = sum(len(msg.content) for msg in assistant_messages) / len(assistant_messages) if assistant_messages else 0
        
        # Count query types
        query_types = {}
        for msg in user_messages:
            if msg.query_type:
                query_types[msg.query_type] = query_types.get(msg.query_type, 0) + 1
        
        return {
            "total_messages": len(self.messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "avg_user_message_length": round(avg_user_length, 1),
            "avg_assistant_message_length": round(avg_assistant_length, 1),
            "query_type_distribution": query_types,
            "conversation_depth": "shallow" if len(self.messages) < 5 else "moderate" if len(self.messages) < 15 else "deep"
        }
    
    def _assess_session_health(self) -> Dict[str, Any]:
        """Assess the health of the conversation session"""
        if not self.messages:
            return {"status": "empty", "score": 0}
        
        score = 0
        issues = []
        
        # Check message balance
        user_count = len([msg for msg in self.messages if msg.role == 'user'])
        assistant_count = len([msg for msg in self.messages if msg.role == 'assistant'])
        
        if user_count == 0:
            issues.append("No user messages")
            score -= 20
        elif assistant_count == 0:
            issues.append("No assistant responses")
            score -= 20
        else:
            score += 20
        
        # Check for context continuity
        if len(self.messages) > 3:
            recent_context = self.get_recent_context(3)
            if len(recent_context) > 100:  # Has substantial context
                score += 20
            else:
                issues.append("Limited context")
        
        # Check for workflow integration
        if self.workflow_instance:
            score += 20
        else:
            issues.append("No workflow integration")
        
        # Determine health status
        if score >= 60:
            status = "healthy"
        elif score >= 40:
            status = "moderate"
        else:
            status = "needs_attention"
        
        return {
            "status": status,
            "score": score,
            "issues": issues,
            "recommendations": self._get_health_recommendations(issues)
        }
    
    def _get_health_recommendations(self, issues: List[str]) -> List[str]:
        """Get recommendations based on health issues"""
        recommendations = []
        
        if "No user messages" in issues:
            recommendations.append("Encourage user interaction")
        if "No assistant responses" in issues:
            recommendations.append("Check response generation")
        if "Limited context" in issues:
            recommendations.append("Provide more detailed responses")
        if "No workflow integration" in issues:
            recommendations.append("Initialize workflow system")
        
        return recommendations


class EnhancedChatMemoryManager(ChatMemoryManager):
    """Enhanced chat memory manager with durable workflow integration"""
    
    def __init__(self):
        super().__init__()
        self.workflow_manager = durable_workflow_manager
    
    def get_session(self, session_id: str = "default", user_id: str = "anonymous") -> EnhancedConversationMemory:
        """Get or create an enhanced conversation session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = EnhancedConversationMemory(session_id, user_id=user_id)
        return self.sessions[session_id]
    
    async def get_workflow_insights(self, session_id: str = "default") -> Dict[str, Any]:
        """Get workflow insights for a session"""
        session = self.get_session(session_id)
        return await session.get_workflow_insights()
    
    async def pause_session(self, session_id: str = "default", reason: str = "user_requested"):
        """Pause a session workflow"""
        session = self.get_session(session_id)
        await session.pause_conversation(reason)
    
    async def resume_session(self, session_id: str = "default") -> bool:
        """Resume a session workflow"""
        session = self.get_session(session_id)
        return await session.resume_conversation()
    
    async def cleanup_old_sessions(self, days_to_keep: int = 30):
        """Clean up old sessions and workflows"""
        await self.workflow_manager.cleanup_old_workflows(days_to_keep)
        
        # Also clean up old session files
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        sessions_dir = Path("data/chat_sessions")
        
        if sessions_dir.exists():
            for session_file in sessions_dir.glob("*.json"):
                try:
                    with open(session_file, 'r') as f:
                        data = json.load(f)
                    
                    last_updated = datetime.fromisoformat(data.get('last_updated', ''))
                    if last_updated < cutoff_date:
                        session_file.unlink()
                        print(f"Cleaned up old session: {session_file.name}")
                except Exception as e:
                    print(f"Error cleaning up session {session_file}: {e}")


# Global enhanced memory manager instance
enhanced_memory_manager = EnhancedChatMemoryManager()
