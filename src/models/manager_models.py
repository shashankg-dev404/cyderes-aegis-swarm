"""
Manager Models - Schemas for Orchestration & Decision Making
"""

from pydantic import BaseModel, Field
from typing import Literal, List, Dict, Any

class InvestigationRequest(BaseModel):
    """Initial alert triggering the investigation"""
    alert: str = Field(..., description="High-level description of the security event")
    source: str = Field("manual", description="Source of the alert (e.g., splunk, sentinel, manual)")
    priority: Literal["critical", "high", "medium", "low"] = "medium"

class AgentTask(BaseModel):
    """A single unit of work delegated to a sub-agent"""
    agent: Literal["intel", "analyst"] = Field(..., description="Which agent to call")
    action: str = Field(..., description="The function/capability to invoke")
    params: Dict[str, Any] = Field(..., description="Arguments for the action")
    reasoning: str = Field(..., description="Why this task is necessary")

class InvestigationPlan(BaseModel):
    """The manager's strategy for investigating the alert"""
    tasks: List[AgentTask] = Field(..., description="Ordered list of tasks to execute")
    thought_process: str = Field(..., description="Explanation of the strategy")

class ThreatVerdict(BaseModel):
    """Final conclusion of the investigation"""
    severity: Literal["critical", "high", "medium", "low", "info"]
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the verdict (0-1)")
    threat_summary: str = Field(..., description="Executive summary of findings")
    evidence: List[str] = Field(..., description="Key data points supporting the verdict")
    recommended_actions: List[str] = Field(..., description="Next steps for remediation")
    affected_assets: List[str] = Field(default_factory=list, description="IPs, Users, or Hosts involved")
    investigation_duration_ms: float = Field(0.0, description="Total time taken")

class InvestigationResponse(BaseModel):
    """Full report returned to the user"""
    request: InvestigationRequest
    plan: InvestigationPlan
    tasks_executed: List[Dict[str, Any]] = Field(..., description="Results from each agent")
    verdict: ThreatVerdict
