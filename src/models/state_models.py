"""
State Models - The Schema for our Database

This defines exactly what an 'Investigation' looks like when stored in Cosmos DB.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field

from src.models.manager_models import InvestigationPlan, ThreatVerdict, AgentTask

class InvestigationState(BaseModel):
    """
    The Master Document stored in Cosmos DB.
    Represents the full lifecycle of a security incident.
    """
    # Unique ID for the investigation (Partition Key)
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # The original alert that started it all
    alert_text: str
    
    # Metadata
    status: str = "running"  # running, completed, failed
    
    # We store these as ISO strings directly to match Cosmos DB format
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # ---------------------------------------------------------
    # The Brain (Manager)
    # ---------------------------------------------------------
    plan: Optional[InvestigationPlan] = None
    verdict: Optional[ThreatVerdict] = None
    
    # ---------------------------------------------------------
    # The Evidence (accumulated from agents)
    # ---------------------------------------------------------
    tasks_history: List[Dict[str, Any]] = []

    # ---------------------------------------------------------
    # Helper Methods
    # ---------------------------------------------------------
    def add_task_result(self, task: AgentTask, result: Dict[str, Any]):
        """Append a completed task to history"""
        self.tasks_history.append({
            "agent": task.agent,
            "action": task.action,
            "params": task.params,
            "output": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def set_plan(self, plan: InvestigationPlan):
        """Update the plan"""
        self.plan = plan
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def set_verdict(self, verdict: ThreatVerdict):
        """Complete the investigation"""
        self.verdict = verdict
        self.status = "completed"
        self.updated_at = datetime.now(timezone.utc).isoformat()
