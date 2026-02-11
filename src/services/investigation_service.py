"""
Investigation Service - The Workflow Coordinator
Connects the Manager, Intel, and Analyst components with ReAct loop
"""

import logging
import os
from typing import Dict, Any

from src.agents.manager_agent import ManagerAgent
from src.agents.intel_agent import IntelAgent
from src.services.analyst_service import get_analyst_service
from src.services.cosmos_service import get_cosmos_service

from src.models.manager_models import InvestigationRequest, AgentTask
from src.models.analyst_models import AnalystRequest
from src.models.state_models import InvestigationState

class InvestigationService:
    """
    Coordinates the multi-agent investigation workflow.
    Implements the ReAct Loop (Reasoning + Acting).
    """

    def __init__(self):
        self.manager_agent = ManagerAgent()
        self.intel_agent = IntelAgent()
        self.analyst_service = get_analyst_service()
        self.cosmos_service = get_cosmos_service()
        self.logger = logging.getLogger(__name__)
        
        # Safety: Maximum iterations before forcing a stop
        self.max_loops = int(os.getenv("MAX_INVESTIGATION_LOOPS", "10"))

    async def run_investigation(self, request: InvestigationRequest) -> InvestigationState:
        """
        Main entry point.
        Implements the ReAct Loop:
        1. Create State
        2. Loop: Ask Manager -> Execute -> Save
        3. Final Verdict
        """
        # 1. CREATE STATE
        state = self.cosmos_service.create_investigation(request.alert)
        self.logger.info(f"Started Investigation ID: {state.id}")

        try:
            # 2. THE REACT LOOP
            loop_count = 0
            
            while loop_count < self.max_loops:
                loop_count += 1
                self.logger.info(f"--- ReAct Loop Iteration {loop_count}/{self.max_loops} ---")
                
                # Ask Manager: "What should we do next?"
                decision = await self.manager_agent.plan_next_step(state)
                
                self.logger.info(f"Manager says: {decision.decision} - {decision.reasoning}")
                
                # STOP CONDITION
                if decision.decision == "stop" or not decision.tasks:
                    self.logger.info("Manager decided to stop. Moving to verdict.")
                    break
                
                # EXECUTE THE NEW TASKS
                for task in decision.tasks:
                    result = await self._execute_task(task)
                    
                    # Update state and save to DB after every task
                    state.add_task_result(task, result)
                    self.cosmos_service.update_investigation(state)
                
                self.logger.info(f"Completed {len(decision.tasks)} tasks. Saved to DB.")
            
            # Check if we hit the loop limit
            if loop_count >= self.max_loops:
                self.logger.warning("Hit maximum loop limit. Forcing stop.")
            
            # 3. FINAL SYNTHESIS
            self.logger.info("Phase: Final Synthesis")
            
            task_results = state.tasks_history
            verdict = await self.manager_agent.synthesize_verdict(
                request.alert,
                task_results
            )
            
            # Final Save
            state.set_verdict(verdict)
            self.cosmos_service.update_investigation(state)
            
            self.logger.info(f"Investigation complete. Verdict: {verdict.severity}")
            return state

        except Exception as e:
            self.logger.error(f"Investigation failed: {str(e)}")
            state.status = "failed"
            state.tasks_history.append({"error": str(e)})
            self.cosmos_service.update_investigation(state)
            raise e

    async def _execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Helper to route a task to the correct agent.
        """
        self.logger.info(f"Executing task: {task.agent} -> {task.action}")
        
        try:
            output = None

            if task.agent == 'intel':
                if task.action == 'lookup_ip':
                    ip = task.params.get('ip_address')
                    if ip:
                        response = await self.intel_agent.lookup_ip(ip)
                        output = response.model_dump(mode='json')
                    else:
                        output = {"error": "Missing 'ip_address' parameter"}

            elif task.agent == 'analyst':
                if task.action == 'analyze_logs':
                    query = task.params.get("query")
                    if query:
                        analyst_req = AnalystRequest(query=query)
                        response = self.analyst_service.analyze(analyst_req)
                        output = response.model_dump(mode='json')
                    else:
                        output = {"error": "Missing 'query' parameter"}
            else:
                output = {"error": f"Unknown agent: {task.agent}"}

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

# Singleton Pattern
_service_instance = None

def get_investigation_service() -> InvestigationService:
    global _service_instance
    if _service_instance is None:
        _service_instance = InvestigationService()
    return _service_instance
