"""
Workflow API endpoints for durable workflow features
Provides REST API access to the new LlamaIndex durable workflow capabilities.
"""

from fastapi import APIRouter, HTTPException, Body, Query
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from .durable_workflow import durable_workflow_manager
from .enhanced_chat_memory import enhanced_memory_manager

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.post("/sessions/{session_id}/create")
async def create_workflow_session(
    session_id: str,
    user_id: str = Query(default="anonymous"),
    metadata: Dict[str, Any] = Body(default={})
):
    """Create a new durable workflow for a chat session"""
    try:
        instance = await durable_workflow_manager.create_workflow(
            session_id=session_id,
            user_id=user_id,
            metadata=metadata
        )
        
        return {
            "success": True,
            "workflow_instance": instance.to_dict(),
            "message": f"Workflow created for session {session_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating workflow: {str(e)}")


@router.get("/sessions/{session_id}/status")
async def get_workflow_status(session_id: str):
    """Get comprehensive workflow status for a session"""
    try:
        status = await durable_workflow_manager.get_workflow_status(session_id)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"No workflow found for session {session_id}")
        
        return {
            "success": True,
            "workflow_status": status
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting workflow status: {str(e)}")


@router.post("/sessions/{session_id}/pause")
async def pause_workflow(
    session_id: str,
    reason: str = Body(default="user_requested", embed=True)
):
    """Pause a workflow session"""
    try:
        await durable_workflow_manager.pause_workflow(session_id, reason)
        
        return {
            "success": True,
            "message": f"Workflow {session_id} paused: {reason}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error pausing workflow: {str(e)}")


@router.post("/sessions/{session_id}/resume")
async def resume_workflow(session_id: str):
    """Resume a paused workflow session"""
    try:
        success = await durable_workflow_manager.resume_workflow(session_id)
        
        if success:
            return {
                "success": True,
                "message": f"Workflow {session_id} resumed successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Workflow {session_id} is not paused or does not exist")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resuming workflow: {str(e)}")


@router.post("/sessions/{session_id}/checkpoint")
async def create_checkpoint(
    session_id: str,
    checkpoint_data: Dict[str, Any] = Body(...),
    checkpoint_type: str = Query(default="manual")
):
    """Create a manual checkpoint for a session"""
    try:
        checkpoint_id = await durable_workflow_manager.checkpointer.create_checkpoint(
            session_id=session_id,
            checkpoint_data=checkpoint_data,
            checkpoint_type=checkpoint_type
        )
        
        return {
            "success": True,
            "checkpoint_id": checkpoint_id,
            "message": f"Checkpoint created for session {session_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating checkpoint: {str(e)}")


@router.get("/sessions/{session_id}/checkpoints")
async def list_checkpoints(session_id: str):
    """List all checkpoints for a session"""
    try:
        checkpoints = await durable_workflow_manager.checkpointer.list_checkpoints(session_id)
        
        return {
            "success": True,
            "checkpoints": checkpoints,
            "count": len(checkpoints)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing checkpoints: {str(e)}")


@router.get("/checkpoints/{checkpoint_id}")
async def get_checkpoint(checkpoint_id: str):
    """Get a specific checkpoint by ID"""
    try:
        checkpoint = await durable_workflow_manager.checkpointer.restore_checkpoint(checkpoint_id)
        
        if not checkpoint:
            raise HTTPException(status_code=404, detail=f"Checkpoint {checkpoint_id} not found")
        
        return {
            "success": True,
            "checkpoint": checkpoint
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting checkpoint: {str(e)}")


@router.get("/users/{user_id}/sessions")
async def get_user_workflow_sessions(
    user_id: str,
    status: Optional[str] = Query(default=None)
):
    """Get all workflow sessions for a user"""
    try:
        instances = await durable_workflow_manager.instance_storage.list_user_instances(user_id, status)
        
        return {
            "success": True,
            "sessions": [instance.to_dict() for instance in instances],
            "count": len(instances)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user sessions: {str(e)}")


@router.get("/sessions/{session_id}/context")
async def get_context_state(session_id: str):
    """Get context state for a session"""
    try:
        context = await durable_workflow_manager.context_store.get_context(session_id)
        
        return {
            "success": True,
            "context_state": {
                "session_id": context.session_id,
                "current_topic": context.current_topic,
                "conversation_summary": context.conversation_summary,
                "entities_tracked": context.entities_tracked,
                "query_patterns": context.query_patterns,
                "user_preferences": context.user_preferences,
                "last_activity": context.last_activity.isoformat() if context.last_activity else None,
                "workflow_stage": context.workflow_stage
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting context state: {str(e)}")


@router.post("/sessions/{session_id}/context")
async def update_context_state(
    session_id: str,
    updates: Dict[str, Any] = Body(...)
):
    """Update context state for a session"""
    try:
        await durable_workflow_manager.update_workflow_state(session_id, **updates)
        
        return {
            "success": True,
            "message": f"Context state updated for session {session_id}",
            "updates": updates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating context state: {str(e)}")


@router.post("/sessions/{session_id}/entities")
async def add_entity(
    session_id: str,
    entity_type: str = Body(embed=True),
    entity: str = Body(embed=True)
):
    """Add an entity to context tracking"""
    try:
        await durable_workflow_manager.context_store.add_entity(session_id, entity_type, entity)
        
        return {
            "success": True,
            "message": f"Entity '{entity}' added to {entity_type} for session {session_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding entity: {str(e)}")


@router.get("/sessions/{session_id}/entities")
async def get_entities(
    session_id: str,
    entity_type: Optional[str] = Query(default=None)
):
    """Get tracked entities for a session"""
    try:
        entities = await durable_workflow_manager.context_store.get_entities(session_id, entity_type)
        
        return {
            "success": True,
            "entities": entities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting entities: {str(e)}")


@router.get("/sessions/{session_id}/insights")
async def get_workflow_insights(session_id: str):
    """Get comprehensive workflow insights for a session"""
    try:
        insights = await enhanced_memory_manager.get_workflow_insights(session_id)
        
        return {
            "success": True,
            "insights": insights
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting workflow insights: {str(e)}")


@router.post("/sessions/{session_id}/stage")
async def update_workflow_stage(
    session_id: str,
    stage: str = Body(embed=True)
):
    """Update workflow stage for a session"""
    try:
        await durable_workflow_manager.context_store.update_workflow_stage(session_id, stage)
        
        return {
            "success": True,
            "message": f"Workflow stage updated to '{stage}' for session {session_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating workflow stage: {str(e)}")


@router.post("/cleanup")
async def cleanup_old_workflows(
    days_to_keep: int = Body(default=30, embed=True)
):
    """Clean up old workflows and checkpoints"""
    try:
        await durable_workflow_manager.cleanup_old_workflows(days_to_keep)
        await enhanced_memory_manager.cleanup_old_sessions(days_to_keep)
        
        return {
            "success": True,
            "message": f"Cleaned up workflows and sessions older than {days_to_keep} days"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up workflows: {str(e)}")


@router.get("/health")
async def workflow_health_check():
    """Health check for workflow system"""
    try:
        # Test basic functionality
        test_session_id = "health_check_test"
        
        # Create a test workflow
        instance = await durable_workflow_manager.create_workflow(
            session_id=test_session_id,
            user_id="health_check",
            metadata={"test": True}
        )
        
        # Get status
        status = await durable_workflow_manager.get_workflow_status(test_session_id)
        
        # Clean up test workflow
        await durable_workflow_manager.instance_storage.update_instance_status(instance.id, "completed")
        
        return {
            "success": True,
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "workflow_storage": "operational",
                "context_store": "operational",
                "checkpointer": "operational"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def include_workflow_router(app):
    """Include the workflow router in the FastAPI app"""
    app.include_router(router)
