"""
Durable Workflow System for Chat Sessions
Implements LlamaIndex's new workflow persistence features for enhanced chat memory management.
"""

import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
from contextlib import asynccontextmanager

from .config import get_settings


@dataclass
class WorkflowInstance:
    """Represents a durable workflow instance for chat sessions"""
    id: str
    session_id: str
    user_id: str
    status: str  # 'active', 'paused', 'completed', 'failed'
    created_at: datetime
    last_updated: datetime
    metadata: Dict[str, Any]
    context_state: Dict[str, Any]
    checkpoint_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['created_at'] = self.created_at.isoformat()
        result['last_updated'] = self.last_updated.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowInstance':
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return cls(**data)


@dataclass
class ContextState:
    """Enhanced context state for workflow persistence"""
    session_id: str
    current_topic: Optional[str] = None
    conversation_summary: Optional[str] = None
    entities_tracked: Dict[str, List[str]] = None  # entity_type -> list of entities
    query_patterns: List[str] = None
    user_preferences: Dict[str, Any] = None
    last_activity: Optional[datetime] = None
    workflow_stage: str = "initial"  # initial, active, deep_dive, summary
    
    def __post_init__(self):
        if self.entities_tracked is None:
            self.entities_tracked = {}
        if self.query_patterns is None:
            self.query_patterns = []
        if self.user_preferences is None:
            self.user_preferences = {}


class WorkflowInstanceStorage:
    """Persistent storage for workflow instances using SQLite"""
    
    def __init__(self, db_path: str = "data/workflow_instances.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize the workflow instances database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_instances (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    context_state TEXT NOT NULL,
                    checkpoint_data TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_id ON workflow_instances(session_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_id ON workflow_instances(user_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON workflow_instances(status)
            """)
    
    async def create_instance(self, session_id: str, user_id: str, metadata: Dict[str, Any] = None) -> WorkflowInstance:
        """Create a new workflow instance"""
        instance = WorkflowInstance(
            id=str(uuid.uuid4()),
            session_id=session_id,
            user_id=user_id,
            status='active',
            created_at=datetime.now(),
            last_updated=datetime.now(),
            metadata=metadata or {},
            context_state={}
        )
        
        await self.save_instance(instance)
        return instance
    
    async def save_instance(self, instance: WorkflowInstance):
        """Save a workflow instance to storage"""
        instance.last_updated = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO workflow_instances 
                (id, session_id, user_id, status, created_at, last_updated, metadata, context_state, checkpoint_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                instance.id,
                instance.session_id,
                instance.user_id,
                instance.status,
                instance.created_at.isoformat(),
                instance.last_updated.isoformat(),
                json.dumps(instance.metadata),
                json.dumps(instance.context_state),
                json.dumps(instance.checkpoint_data) if instance.checkpoint_data else None
            ))
    
    async def get_instance(self, instance_id: str) -> Optional[WorkflowInstance]:
        """Get a workflow instance by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM workflow_instances WHERE id = ?
            """, (instance_id,))
            
            row = cursor.fetchone()
            if row:
                return WorkflowInstance(
                    id=row[0],
                    session_id=row[1],
                    user_id=row[2],
                    status=row[3],
                    created_at=datetime.fromisoformat(row[4]),
                    last_updated=datetime.fromisoformat(row[5]),
                    metadata=json.loads(row[6]),
                    context_state=json.loads(row[7]),
                    checkpoint_data=json.loads(row[8]) if row[8] else None
                )
        return None
    
    async def get_instance_by_session(self, session_id: str) -> Optional[WorkflowInstance]:
        """Get a workflow instance by session ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM workflow_instances WHERE session_id = ? ORDER BY last_updated DESC LIMIT 1
            """, (session_id,))
            
            row = cursor.fetchone()
            if row:
                return WorkflowInstance(
                    id=row[0],
                    session_id=row[1],
                    user_id=row[2],
                    status=row[3],
                    created_at=datetime.fromisoformat(row[4]),
                    last_updated=datetime.fromisoformat(row[5]),
                    metadata=json.loads(row[6]),
                    context_state=json.loads(row[7]),
                    checkpoint_data=json.loads(row[8]) if row[8] else None
                )
        return None
    
    async def update_instance_status(self, instance_id: str, status: str):
        """Update the status of a workflow instance"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE workflow_instances 
                SET status = ?, last_updated = ?
                WHERE id = ?
            """, (status, datetime.now().isoformat(), instance_id))
    
    async def list_user_instances(self, user_id: str, status: str = None) -> List[WorkflowInstance]:
        """List workflow instances for a user"""
        query = "SELECT * FROM workflow_instances WHERE user_id = ?"
        params = [user_id]
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY last_updated DESC"
        
        instances = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            for row in cursor.fetchall():
                instances.append(WorkflowInstance(
                    id=row[0],
                    session_id=row[1],
                    user_id=row[2],
                    status=row[3],
                    created_at=datetime.fromisoformat(row[4]),
                    last_updated=datetime.fromisoformat(row[5]),
                    metadata=json.loads(row[6]),
                    context_state=json.loads(row[7]),
                    checkpoint_data=json.loads(row[8]) if row[8] else None
                ))
        
        return instances


class ContextStateStore:
    """Enhanced context state management for workflows"""
    
    def __init__(self, storage_path: str = "data/context_states"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._active_contexts: Dict[str, ContextState] = {}
    
    async def get_context(self, session_id: str) -> ContextState:
        """Get or create context state for a session"""
        if session_id not in self._active_contexts:
            await self._load_context(session_id)
        
        return self._active_contexts[session_id]
    
    async def update_context(self, session_id: str, **updates):
        """Update context state for a session"""
        context = await self.get_context(session_id)
        
        for key, value in updates.items():
            if hasattr(context, key):
                setattr(context, key, value)
        
        context.last_activity = datetime.now()
        await self._save_context(context)
    
    async def add_entity(self, session_id: str, entity_type: str, entity: str):
        """Add an entity to the context tracking"""
        context = await self.get_context(session_id)
        
        if entity_type not in context.entities_tracked:
            context.entities_tracked[entity_type] = []
        
        if entity not in context.entities_tracked[entity_type]:
            context.entities_tracked[entity_type].append(entity)
        
        await self._save_context(context)
    
    async def get_entities(self, session_id: str, entity_type: str = None) -> Dict[str, List[str]]:
        """Get tracked entities for a session"""
        context = await self.get_context(session_id)
        
        if entity_type:
            return {entity_type: context.entities_tracked.get(entity_type, [])}
        
        return context.entities_tracked
    
    async def update_workflow_stage(self, session_id: str, stage: str):
        """Update the workflow stage for a session"""
        await self.update_context(session_id, workflow_stage=stage)
    
    async def _load_context(self, session_id: str):
        """Load context state from storage"""
        context_file = self.storage_path / f"{session_id}.json"
        
        if context_file.exists():
            try:
                with open(context_file, 'r') as f:
                    data = json.load(f)
                
                # Convert datetime strings back to datetime objects
                if data.get('last_activity'):
                    data['last_activity'] = datetime.fromisoformat(data['last_activity'])
                
                self._active_contexts[session_id] = ContextState(**data)
            except Exception as e:
                print(f"Error loading context for {session_id}: {e}")
                self._active_contexts[session_id] = ContextState(session_id=session_id)
        else:
            self._active_contexts[session_id] = ContextState(session_id=session_id)
    
    async def _save_context(self, context: ContextState):
        """Save context state to storage"""
        context_file = self.storage_path / f"{context.session_id}.json"
        
        try:
            data = asdict(context)
            # Convert datetime to string for JSON serialization
            if data.get('last_activity'):
                data['last_activity'] = data['last_activity'].isoformat()
            
            with open(context_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving context for {context.session_id}: {e}")


class ExternalCheckpointer:
    """External checkpointing system for long-running conversations"""
    
    def __init__(self, checkpoint_dir: str = "data/checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_checkpoint(self, session_id: str, checkpoint_data: Dict[str, Any], checkpoint_type: str = "conversation") -> str:
        """Create a checkpoint for a session"""
        checkpoint_id = f"{session_id}_{checkpoint_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        
        checkpoint_info = {
            "checkpoint_id": checkpoint_id,
            "session_id": session_id,
            "checkpoint_type": checkpoint_type,
            "created_at": datetime.now().isoformat(),
            "data": checkpoint_data
        }
        
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_info, f, indent=2)
        
        return checkpoint_id
    
    async def restore_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Restore a checkpoint by ID"""
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        
        if checkpoint_file.exists():
            try:
                with open(checkpoint_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error restoring checkpoint {checkpoint_id}: {e}")
        
        return None
    
    async def list_checkpoints(self, session_id: str = None) -> List[Dict[str, Any]]:
        """List available checkpoints"""
        checkpoints = []
        
        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            try:
                with open(checkpoint_file, 'r') as f:
                    checkpoint_info = json.load(f)
                
                if session_id is None or checkpoint_info.get('session_id') == session_id:
                    checkpoints.append(checkpoint_info)
            except Exception as e:
                print(f"Error reading checkpoint {checkpoint_file}: {e}")
        
        # Sort by creation time (newest first)
        checkpoints.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return checkpoints
    
    async def cleanup_old_checkpoints(self, days_to_keep: int = 30):
        """Clean up checkpoints older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            try:
                with open(checkpoint_file, 'r') as f:
                    checkpoint_info = json.load(f)
                
                created_at = datetime.fromisoformat(checkpoint_info.get('created_at', ''))
                if created_at < cutoff_date:
                    checkpoint_file.unlink()
                    print(f"Cleaned up old checkpoint: {checkpoint_file.name}")
            except Exception as e:
                print(f"Error cleaning up checkpoint {checkpoint_file}: {e}")


class DurableWorkflowManager:
    """Main manager for durable workflow features"""
    
    def __init__(self):
        self.instance_storage = WorkflowInstanceStorage()
        self.context_store = ContextStateStore()
        self.checkpointer = ExternalCheckpointer()
    
    async def create_workflow(self, session_id: str, user_id: str, metadata: Dict[str, Any] = None) -> WorkflowInstance:
        """Create a new durable workflow for a chat session"""
        # Create workflow instance
        instance = await self.instance_storage.create_instance(session_id, user_id, metadata)
        
        # Initialize context state
        await self.context_store.update_context(
            session_id,
            workflow_stage="initial",
            last_activity=datetime.now()
        )
        
        # Create initial checkpoint
        await self.checkpointer.create_checkpoint(
            session_id,
            {
                "workflow_instance_id": instance.id,
                "status": "initialized",
                "metadata": metadata or {}
            },
            "initialization"
        )
        
        return instance
    
    async def update_workflow_state(self, session_id: str, **updates):
        """Update workflow state and create checkpoint"""
        # Update context state
        await self.context_store.update_context(session_id, **updates)
        
        # Get current workflow instance
        instance = await self.instance_storage.get_instance_by_session(session_id)
        if instance:
            # Update instance context state
            instance.context_state.update(updates)
            await self.instance_storage.save_instance(instance)
            
            # Create checkpoint
            await self.checkpointer.create_checkpoint(
                session_id,
                {
                    "workflow_instance_id": instance.id,
                    "context_updates": updates,
                    "timestamp": datetime.now().isoformat()
                },
                "state_update"
            )
    
    async def pause_workflow(self, session_id: str, reason: str = "user_requested"):
        """Pause a workflow and create checkpoint"""
        instance = await self.instance_storage.get_instance_by_session(session_id)
        if instance:
            await self.instance_storage.update_instance_status(instance.id, "paused")
            
            # Create pause checkpoint
            await self.checkpointer.create_checkpoint(
                session_id,
                {
                    "workflow_instance_id": instance.id,
                    "pause_reason": reason,
                    "context_state": instance.context_state,
                    "timestamp": datetime.now().isoformat()
                },
                "pause"
            )
    
    async def resume_workflow(self, session_id: str) -> bool:
        """Resume a paused workflow"""
        instance = await self.instance_storage.get_instance_by_session(session_id)
        if instance and instance.status == "paused":
            await self.instance_storage.update_instance_status(instance.id, "active")
            
            # Create resume checkpoint
            await self.checkpointer.create_checkpoint(
                session_id,
                {
                    "workflow_instance_id": instance.id,
                    "resume_timestamp": datetime.now().isoformat()
                },
                "resume"
            )
            return True
        return False
    
    async def get_workflow_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive workflow status for a session"""
        instance = await self.instance_storage.get_instance_by_session(session_id)
        if not instance:
            return None
        
        context = await self.context_store.get_context(session_id)
        checkpoints = await self.checkpointer.list_checkpoints(session_id)
        
        return {
            "workflow_instance": instance.to_dict(),
            "context_state": asdict(context),
            "recent_checkpoints": checkpoints[:5],  # Last 5 checkpoints
            "status": instance.status
        }
    
    async def cleanup_old_workflows(self, days_to_keep: int = 30):
        """Clean up old workflows and checkpoints"""
        await self.checkpointer.cleanup_old_checkpoints(days_to_keep)
        
        # Also clean up old context states
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        for context_file in self.context_store.storage_path.glob("*.json"):
            try:
                with open(context_file, 'r') as f:
                    data = json.load(f)
                
                last_activity = datetime.fromisoformat(data.get('last_activity', ''))
                if last_activity < cutoff_date:
                    context_file.unlink()
                    print(f"Cleaned up old context: {context_file.name}")
            except Exception as e:
                print(f"Error cleaning up context {context_file}: {e}")


# Global durable workflow manager instance
durable_workflow_manager = DurableWorkflowManager()
