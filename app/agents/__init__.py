"""
Multi-agent system for JD-Copilot.

Agent Pipeline:
1. Intent Classifier - Extracts intent, companies, sources needed
2. Planning Agent - Creates execution plan with fallbacks
3. Route Decider - Determines agent pipeline and strategies
4. Conversation Agent - Resolves context and conversation history
5. Retrieval Agent - Multi-source, company-isolated retrieval
6. Data Quality Agent - Validates retrieval results
7. Synthesis Agent - Generates response with tone + template
"""

from .intent_classifier import IntentClassifier, QueryIntent, intent_classifier
from .planning_agent import PlanningAgent, ExecutionPlan, planning_agent
from .route_decider import RouteDecider, RoutingDecision, route_decider
from .data_quality_agent import DataQualityAgent, QualityReport, data_quality_agent
from .orchestrator import AgentOrchestrator, agent_orchestrator

__all__ = [
    'IntentClassifier',
    'QueryIntent',
    'intent_classifier',
    'PlanningAgent',
    'ExecutionPlan',
    'planning_agent',
    'RouteDecider',
    'RoutingDecision',
    'route_decider',
    'DataQualityAgent',
    'QualityReport',
    'data_quality_agent',
    'AgentOrchestrator',
    'agent_orchestrator',
]
