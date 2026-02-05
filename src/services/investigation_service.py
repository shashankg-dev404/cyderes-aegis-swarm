"""
Investigation Service - The Workflow Coordinator
Connects the Manager, Intel, and Analyst components.
"""

import logging
import time
from typing import Dict, Any, List

# Agents and Services
from src.agents.manager_agent import ManagerAgent
from src.agents.intel_agent import IntelAgent
from src.services.analyst_service import get_analyst_service
from src.services.cosmos_service import get_cosmos_service

# Models
from src.models.manager_models import InvestigationRequest, AgentTask
from src.models.analyst_models import AnalystRequest
from src.models.state_models import InvestigationState

class InvestigationService:
    """
    Coordinates the multi-agent investigation workflow.
    Manages state persistence via Cosmos DB.
    """

    def __init__(self):
        # Initialize Agents
        self.manager_agent = ManagerAgent()
        self.intel_agent = IntelAgent()
        self.analyst_service = get_analyst_service()
        
        # Initialize Database Access
        self.cosmos_service = get_cosmos_service()
        
        self.logger = logging.getLogger(__name__)

    async def run_investigation(self, request: InvestigationRequest) -> InvestigationState:
        """
        Main entry point.
        1. Create DB Record
        2. Plan
        3. Execute
        4. Synthesize
        5. Save & Return
        """
        # 1. CREATE STATE -----------------------------------------
        # We start by creating a permanent record in the database.
        state = self.cosmos_service.create_investigation(request.alert)
        self.logger.info(f"Started Investigation ID: {state.id}")

        try:
            # 2. PLANNING PHASE ---------------------------------------
            self.logger.info("Phase 1: Planning")
            plan = await self.manager_agent.plan_investigation(request.alert)
            
            # Save the plan to DB
            state.set_plan(plan)
            self.cosmos_service.update_investigation(state)
            
            self.logger.info(f"Manager generated {len(plan.tasks)} tasks.")

            # 3. EXECUTION PHASE --------------------------------------
            self.logger.info("Phase 2: Execution")
            
            for task in plan.tasks:
                # Execute the single task
                result = await self._execute_task(task)
                
                # IMMEDIATE SAVE: We save after *every* task.
                # If the system crashes, we won't lose this progress.
                state.add_task_result(task, result)
                self.cosmos_service.update_investigation(state)

            # 4. SYNTHESIS PHASE --------------------------------------
            self.logger.info("Phase 3: Synthesis")
            
            # We send the *accumulated history* from our state object
            # This ensures the Manager sees exactly what is in the DB
            task_results = [t['output'] for t in state.tasks_history]
            
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
            # Emergency Save: If anything crashes, mark state as 'failed'
            self.logger.error(f"Investigation failed: {str(e)}")
            state.status = "failed"
            state.tasks_history.append({"error": str(e)}) # Log the crash
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
                        # Intel Agent returns a Pydantic model
                        response = await self.intel_agent.lookup_ip(ip)
                        output = response.model_dump(mode='json')
                    else:
                        output = {"error": "Missing 'ip_address' parameter"}

            elif task.agent == 'analyst':
                if task.action == 'analyze_logs':
                    query = task.params.get("query")
                    if query:
                        # Analyst Service returns a Pydantic model
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