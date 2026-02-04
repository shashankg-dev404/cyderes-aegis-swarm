"""
Investigation Service - The Workflow Coordinator
Connects the Manager, Intel, and Analyst components.
"""

import logging
import time
from typing import Dict, Any, List

# Import our Agents and Services
from src.agents.manager_agent import ManagerAgent
from src.agents.intel_agent import IntelAgent
from src.services.analyst_service import get_analyst_service
from src.models.manager_models import (
    InvestigationRequest, 
    InvestigationResponse, 
    InvestigationPlan,
    AgentTask
)
from src.models.analyst_models import AnalystRequest

class InvestigationService:
    """
    Coordinates the multi-agent investigation workflow.
    """

    def __init__(self):
        # We initialize all agents here.
        # In a larger app, we might use Dependency Injection.
        self.manager_agent = ManagerAgent()
        self.intel_agent = IntelAgent()
        self.analyst_service = get_analyst_service() # Reuse the existing singleton
        self.logger = logging.getLogger(__name__)

    async def run_investigation(self, request: InvestigationRequest) -> InvestigationResponse:
        """
        Main entry point for an investigation.
        """
        start_time = time.time()
        self.logger.info(f"Starting investigation for alert: {request.alert}")

        # ---------------------------------------------------------
        # Phase 1: Planning
        # Ask the Manager what to do.
        # ---------------------------------------------------------
        self.logger.info("Phase 1: Planning")
        plan: InvestigationPlan = await self.manager_agent.plan_investigation(request.alert)
        self.logger.info(f"Manager generated {len(plan.tasks)} tasks.")

        # ---------------------------------------------------------
        # Phase 2: Execution
        # Run the tasks the Manager requested.
        # ---------------------------------------------------------
        self.logger.info("Phase 2: Execution")
        task_results = []

        for task in plan.tasks:
            result = await self._execute_task(task)
            task_results.append(result)
        
        # ---------------------------------------------------------
        # Phase 3: Synthesis
        # Give all raw data to Manager for a final verdict.
        # ---------------------------------------------------------
        self.logger.info("Phase 3: Synthesis")
        verdict = await self.manager_agent.synthesize_verdict(request.alert, task_results)

        # Calculate total duration
        duration = (time.time() - start_time) * 1000
        verdict.investigation_duration_ms = duration

        self.logger.info(f"Investigation complete. Verdict: {verdict.severity}")

        # Return the comprehensive report
        return InvestigationResponse(
            request=request,
            plan=plan,
            tasks_executed=task_results,
            verdict=verdict
        )
    
    async def _execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Helper to route a task to the correct agent.
        """
        self.logger.info(f"Executing task: {task.agent} -> {task.action}")

        try:
            output = None

            # ROUTING LOGIC
            if task.agent == 'intel':
                if task.action == 'lookup_ip':
                    ip = task.params.get('ip_address')
                    if ip:
                        # Call Intel Agent
                        # Note: This returns a Pydantic model, so we .model_dump() it to JSON
                        response = await self.intel_agent.lookup_ip(ip)
                        output = response.model_dump(mode='json')
                    else:
                        output = {"error": "Missing 'ip_address' parameter"}
            
            elif task.agent == 'analyst':
                if task.action == 'analyze_logs':
                    query = task.params.get("query")
                    if query:
                        # Call Analyst Service
                        # We must wrap the string in a Request object
                        analyst_req = AnalystRequest(query=query)
                        response = self.analyst_service.analyze(analyst_req)
                        output = response.model_dump()
                    else:
                        output = {"error": "Missing 'query' parameter"}
            
            else:
                output = {"error": f"Unknown agent: {task.agent}"}

            # Return a standardized result block
            return {
                "agent": task.agent,
                "action": task.action,
                "status": "success",
                "output": output
            }
        
        except Exception as e:
            self.logger.error(f"Task failed: {str(e)}")
            return {
                "agent": task.agent,
                "action": task.action,
                "status": "error",
                "error": str(e)
            }

# Singleton pattern again - standard for stateless services
_service_instance = None

def get_investigation_service() -> InvestigationService:
    global _service_instance
    if _service_instance is None:
        _service_instance = InvestigationService()
    return _service_instance