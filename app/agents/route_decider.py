"""
Route Decider Agent - Determines agent pipeline and strategies.
"""

from typing import Dict, List
from dataclasses import dataclass
from .intent_classifier import QueryIntent
from .planning_agent import ExecutionPlan


@dataclass
class RoutingDecision:
    """Routing decision for agent orchestration."""
    agent_pipeline: List[str]
    retrieval_strategy: str
    synthesis_mode: str
    should_validate: bool
    fallback_strategy: str


class RouteDecider:
    """Decides how to orchestrate agents based on intent and plan."""
    
    def decide(self, intent: QueryIntent, plan: ExecutionPlan) -> RoutingDecision:
        """
        Decide routing strategy based on intent and execution plan.
        """
        
        # Determine agent pipeline
        agent_pipeline = self._determine_pipeline(intent, plan)
        
        # Determine retrieval strategy
        retrieval_strategy = plan.primary_strategy
        
        # Determine synthesis mode
        synthesis_mode = self._determine_synthesis_mode(intent)
        
        # Decide if validation needed
        should_validate = intent.complexity in ['medium', 'high']
        
        # Fallback strategy
        fallback_strategy = plan.fallback_strategies[0] if plan.fallback_strategies else 'none'
        
        decision = RoutingDecision(
            agent_pipeline=agent_pipeline,
            retrieval_strategy=retrieval_strategy,
            synthesis_mode=synthesis_mode,
            should_validate=should_validate,
            fallback_strategy=fallback_strategy
        )
        
        print(f"🚦 Routing Decision:")
        print(f"   Pipeline: {' → '.join(decision.agent_pipeline)}")
        print(f"   Synthesis: {decision.synthesis_mode}")
        
        return decision
    
    def _determine_pipeline(self, intent: QueryIntent, plan: ExecutionPlan) -> List[str]:
        """Determine which agents to invoke."""
        
        # Simple count queries skip conversation agent
        if intent.primary_intent == 'count_query' and intent.complexity == 'low':
            return ['retrieval', 'quality', 'synthesis']
        
        # Full pipeline for complex queries
        return ['conversation', 'retrieval', 'quality', 'synthesis']
    
    def _determine_synthesis_mode(self, intent: QueryIntent) -> str:
        """Determine synthesis template/mode."""
        
        mode_map = {
            'interview_prep_guide': 'structured_interview_prep',
            'topic_list': 'simple_list',
            'experience_summary': 'narrative_synthesis',
            'structured_info': 'fact_extraction',
            'comparison_table': 'comparative_analysis',
            'simple_count': 'direct_count'
        }
        
        return mode_map.get(intent.response_format, 'general_synthesis')


# Global instance
route_decider = RouteDecider()
