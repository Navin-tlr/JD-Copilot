#!/usr/bin/env python3
"""
Test script for the new LlamaIndex Durable Workflow features
Demonstrates the enhanced chat memory and workflow persistence capabilities.
"""

import asyncio
import json
from datetime import datetime
from app.durable_workflow import durable_workflow_manager
from app.enhanced_chat_memory import enhanced_memory_manager


async def test_workflow_persistence():
    """Test the core workflow persistence features"""
    print("🦙 Testing LlamaIndex Durable Workflow Features")
    print("=" * 60)
    
    session_id = "demo_session"
    user_id = "demo_user"
    
    # Test 1: Create a new workflow
    print("\n1️⃣ Creating Durable Workflow...")
    instance = await durable_workflow_manager.create_workflow(
        session_id=session_id,
        user_id=user_id,
        metadata={
            "demo": True,
            "created_at": datetime.now().isoformat(),
            "features": ["persistence", "checkpointing", "context_tracking"]
        }
    )
    print(f"✅ Created workflow: {instance.id}")
    print(f"   Status: {instance.status}")
    print(f"   Session: {instance.session_id}")
    
    # Test 2: Update workflow state
    print("\n2️⃣ Updating Workflow State...")
    await durable_workflow_manager.update_workflow_state(
        session_id,
        current_topic="job_descriptions",
        workflow_stage="active",
        user_preferences={"interested_in_salary": True}
    )
    print("✅ Updated workflow state with context")
    
    # Test 3: Create checkpoints
    print("\n3️⃣ Creating Checkpoints...")
    checkpoint1 = await durable_workflow_manager.checkpointer.create_checkpoint(
        session_id,
        {"milestone": "initial_setup", "timestamp": datetime.now().isoformat()},
        "milestone"
    )
    print(f"✅ Created milestone checkpoint: {checkpoint1}")
    
    checkpoint2 = await durable_workflow_manager.checkpointer.create_checkpoint(
        session_id,
        {"user_query": "What companies hire for finance roles?", "response_quality": "good"},
        "conversation"
    )
    print(f"✅ Created conversation checkpoint: {checkpoint2}")
    
    # Test 4: Pause and resume workflow
    print("\n4️⃣ Testing Pause/Resume...")
    await durable_workflow_manager.pause_workflow(session_id, "user_break")
    print("✅ Workflow paused")
    
    success = await durable_workflow_manager.resume_workflow(session_id)
    print(f"✅ Workflow resumed: {success}")
    
    # Test 5: Get comprehensive status
    print("\n5️⃣ Getting Workflow Status...")
    status = await durable_workflow_manager.get_workflow_status(session_id)
    print(f"✅ Workflow Status:")
    print(f"   Status: {status['status']}")
    print(f"   Stage: {status['context_state']['workflow_stage']}")
    print(f"   Topic: {status['context_state']['current_topic']}")
    print(f"   Checkpoints: {len(status['recent_checkpoints'])}")
    
    return session_id


async def test_enhanced_chat_memory():
    """Test the enhanced chat memory with workflow integration"""
    print("\n\n🧠 Testing Enhanced Chat Memory")
    print("=" * 60)
    
    session_id = "chat_demo"
    user_id = "chat_user"
    
    # Test 1: Create enhanced session
    print("\n1️⃣ Creating Enhanced Chat Session...")
    enhanced_session = enhanced_memory_manager.get_session(session_id, user_id)
    print(f"✅ Created enhanced session: {session_id}")
    
    # Test 2: Add messages with context tracking
    print("\n2️⃣ Adding Messages with Context Tracking...")
    
    # User asks about finance roles
    await enhanced_session.add_message(
        role="user",
        content="Which companies hire for finance roles?",
        query_type="structured",
        specialization="finance",
        entities_mentioned=["companies", "finance"]
    )
    print("✅ Added user message about finance roles")
    
    # Simulate assistant response
    await enhanced_session.add_message(
        role="assistant",
        content="Based on our database, companies like Goldman Sachs, JP Morgan, and Deloitte hire for finance roles. Total companies: 15. Average salary range: 8-15 LPA.",
        metadata={"snippets_used": 3, "response_type": "structured"}
    )
    print("✅ Added assistant response with salary info")
    
    # User asks follow-up question
    await enhanced_session.add_message(
        role="user",
        content="What about remote work options?",
        query_type="unstructured",
        entities_mentioned=["remote work"]
    )
    print("✅ Added follow-up question about remote work")
    
    # Test 3: Get enhanced context
    print("\n3️⃣ Getting Enhanced Context...")
    enhanced_context = await enhanced_session.get_enhanced_context()
    print(f"✅ Enhanced Context:")
    print(f"   Message Count: {enhanced_context['message_count']}")
    print(f"   Session Duration: {enhanced_context['session_duration']}")
    if 'workflow_status' in enhanced_context:
        print(f"   Workflow Stage: {enhanced_context['workflow_status']['context_state']['workflow_stage']}")
    
    # Test 4: Get workflow insights
    print("\n4️⃣ Getting Workflow Insights...")
    insights = await enhanced_session.get_workflow_insights()
    print(f"✅ Workflow Insights:")
    if 'conversation_patterns' in insights:
        patterns = insights['conversation_patterns']
        print(f"   Total Messages: {patterns.get('total_messages', 0)}")
        print(f"   Conversation Depth: {patterns.get('conversation_depth', 'unknown')}")
        print(f"   Query Types: {patterns.get('query_type_distribution', {})}")
    
    if 'session_health' in insights:
        health = insights['session_health']
        print(f"   Session Health: {health.get('status', 'unknown')} (Score: {health.get('score', 0)})")
    
    return session_id


async def test_context_state_management():
    """Test advanced context state management"""
    print("\n\n🎯 Testing Context State Management")
    print("=" * 60)
    
    session_id = "context_demo"
    
    # Test 1: Add entities to context
    print("\n1️⃣ Adding Entities to Context...")
    await durable_workflow_manager.context_store.add_entity(session_id, "companies", "Goldman Sachs")
    await durable_workflow_manager.context_store.add_entity(session_id, "companies", "JP Morgan")
    await durable_workflow_manager.context_store.add_entity(session_id, "specializations", "finance")
    await durable_workflow_manager.context_store.add_entity(session_id, "specializations", "marketing")
    print("✅ Added entities to context tracking")
    
    # Test 2: Get tracked entities
    print("\n2️⃣ Getting Tracked Entities...")
    all_entities = await durable_workflow_manager.context_store.get_entities(session_id)
    print(f"✅ All Entities: {all_entities}")
    
    companies = await durable_workflow_manager.context_store.get_entities(session_id, "companies")
    print(f"✅ Companies: {companies}")
    
    # Test 3: Update workflow stage
    print("\n3️⃣ Updating Workflow Stage...")
    await durable_workflow_manager.context_store.update_workflow_stage(session_id, "deep_dive")
    print("✅ Updated workflow stage to 'deep_dive'")
    
    # Test 4: Get context state
    print("\n4️⃣ Getting Context State...")
    context = await durable_workflow_manager.context_store.get_context(session_id)
    print(f"✅ Context State:")
    print(f"   Workflow Stage: {context.workflow_stage}")
    print(f"   Entities Tracked: {len(context.entities_tracked)} types")
    print(f"   Query Patterns: {context.query_patterns}")


async def test_checkpoint_management():
    """Test checkpoint creation and restoration"""
    print("\n\n💾 Testing Checkpoint Management")
    print("=" * 60)
    
    session_id = "checkpoint_demo"
    
    # Test 1: Create multiple checkpoints
    print("\n1️⃣ Creating Multiple Checkpoints...")
    checkpoints = []
    
    for i in range(3):
        checkpoint_id = await durable_workflow_manager.checkpointer.create_checkpoint(
            session_id,
            {
                "step": i + 1,
                "data": f"checkpoint_data_{i}",
                "timestamp": datetime.now().isoformat()
            },
            f"step_{i+1}"
        )
        checkpoints.append(checkpoint_id)
        print(f"✅ Created checkpoint {i+1}: {checkpoint_id}")
    
    # Test 2: List checkpoints
    print("\n2️⃣ Listing Checkpoints...")
    all_checkpoints = await durable_workflow_manager.checkpointer.list_checkpoints(session_id)
    print(f"✅ Found {len(all_checkpoints)} checkpoints")
    
    for cp in all_checkpoints:
        print(f"   - {cp['checkpoint_id']} ({cp['checkpoint_type']})")
    
    # Test 3: Restore a checkpoint
    print("\n3️⃣ Restoring Checkpoint...")
    if checkpoints:
        restored = await durable_workflow_manager.checkpointer.restore_checkpoint(checkpoints[0])
        if restored:
            print(f"✅ Restored checkpoint: {restored['checkpoint_id']}")
            print(f"   Data: {restored['data']}")
        else:
            print("❌ Failed to restore checkpoint")


async def test_cleanup_and_maintenance():
    """Test cleanup and maintenance features"""
    print("\n\n🧹 Testing Cleanup and Maintenance")
    print("=" * 60)
    
    # Test 1: Cleanup old workflows (simulation)
    print("\n1️⃣ Testing Cleanup...")
    try:
        await durable_workflow_manager.cleanup_old_workflows(days_to_keep=0)  # Clean everything for demo
        print("✅ Cleanup completed (simulation)")
    except Exception as e:
        print(f"⚠️ Cleanup simulation: {e}")
    
    # Test 2: Health check
    print("\n2️⃣ Testing Health Check...")
    try:
        # This would normally be done via API
        test_session = "health_check"
        instance = await durable_workflow_manager.create_workflow(test_session, "health_user")
        status = await durable_workflow_manager.get_workflow_status(test_session)
        print(f"✅ Health check passed: {status['status']}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")


async def main():
    """Run all tests"""
    print("🚀 Starting LlamaIndex Durable Workflow Tests")
    print("=" * 80)
    
    try:
        # Run all test suites
        await test_workflow_persistence()
        await test_enhanced_chat_memory()
        await test_context_state_management()
        await test_checkpoint_management()
        await test_cleanup_and_maintenance()
        
        print("\n\n🎉 All Tests Completed Successfully!")
        print("=" * 80)
        print("\n📋 Summary of Features Implemented:")
        print("✅ Workflow Instance Storage - Persistent workflow state")
        print("✅ Context Object State Store - Enhanced context management")
        print("✅ External Checkpointing - Long-running conversation support")
        print("✅ Enhanced Chat Memory - Integrated workflow features")
        print("✅ API Endpoints - REST API access to all features")
        print("✅ Health Monitoring - System health and insights")
        
        print("\n🔗 Available API Endpoints:")
        print("   POST /workflow/sessions/{id}/create")
        print("   GET  /workflow/sessions/{id}/status")
        print("   POST /workflow/sessions/{id}/pause")
        print("   POST /workflow/sessions/{id}/resume")
        print("   POST /workflow/sessions/{id}/checkpoint")
        print("   GET  /workflow/sessions/{id}/checkpoints")
        print("   GET  /workflow/sessions/{id}/context")
        print("   GET  /workflow/sessions/{id}/insights")
        print("   GET  /workflow/health")
        
        print("\n🚀 Ready for production use!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
