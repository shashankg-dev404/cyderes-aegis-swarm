"""
Manager Agent - The Orchestrator

Responsibility: Planning, Delegation, and Synthesis
Now with Recursive Decision Making (ReAct Loop)
"""

import os
import json
import logging
from typing import List, Dict, Any
from openai import AzureOpenAI
from pydantic import BaseModel
from src.models.manager_models import InvestigationPlan, ThreatVerdict, AgentTask
from src.models.state_models import InvestigationState

class NextStepDecision(BaseModel):
    """
    The Manager's decision on what to do next.
    """
    decision: str  # "continue" or "stop"
    reasoning: str
    tasks: List[AgentTask] = []

class ManagerAgent:
    """
    Orchestrates the investigation by decomposing alerts into agent tasks
    and synthesizing results into a final verdict.
    
    Now supports iterative reasoning via the ReAct loop.
    """

    SYSTEM_PROMPT_PLANNER = """You are a Senior SOC Manager. Your goal is to investigate security alerts by delegating tasks to specialized agents.

**Available Agents:**
1. **Intel Agent**:
   - Action: `lookup_ip`
   - Params: `{"ip_address": "8.8.8.8"}`
   - Use for: IP reputation, threat intelligence.

2. **Analyst Agent**:
   - Action: `analyze_logs`
   - Params: `{"query": "Count login attempts from 1.2.3.4"}`
   - Use for: Querying firewall logs, counting events.

**Goal:**
Given an alert, create a JSON plan of tasks.

**Output Format:**
Return ONLY valid JSON matching this schema:
{
  "thought_process": "Brief explanation...",
  "tasks": [
    {
      "agent": "intel",
      "action": "lookup_ip",
      "params": {"ip_address": "8.8.8.8"},
      "reasoning": "Check if IP is known malicious"
    },
    {
      "agent": "analyst",
      "action": "analyze_logs",
      "params": {"query": "..."},
      "reasoning": "Check for successful attacks"
    }
  ]
}
"""

    SYSTEM_PROMPT_NEXT_STEP = """You are a Senior SOC Manager conducting an iterative investigation.

**Available Agents:**
1. **Intel Agent**: IP reputation lookups
2. **Analyst Agent**: Log analysis queries

**Your Task:**
Review the investigation so far and decide the next step.

**Options:**
1. **Continue**: More investigation needed. Provide new tasks.
2. **Stop**: We have enough evidence. No more tasks needed.

**Output Format:**
Return ONLY valid JSON:
{
  "decision": "continue" or "stop",
  "reasoning": "Why are we continuing/stopping?",
  "tasks": [
    {
      "agent": "intel",
      "action": "lookup_ip",
      "params": {"ip_address": "..."},
      "reasoning": "..."
    }
  ]
}

If decision is "stop", tasks should be an empty array [].
"""

    SYSTEM_PROMPT_VERDICT = """You are a Senior SOC Manager. Synthesize the following investigation data into a final threat verdict.

**Input Data:**
1. Original Alert
2. Intel Findings (IP reputation)
3. Analyst Findings (Log analysis)

**Goal:**
Determine the severity and provide a summary.

- **Critical**: Confirmed malicious IP + Successful attacks or Data Exfiltration.
- **High**: Confirmed malicious IP + High volume of failed attacks (Brute Force).
- **Medium**: Suspicious IP + Low volume / Scanning.
- **Low/Info**: Benign IP or standard noise.

**Output Format:**
Return ONLY valid JSON matching the ThreatVerdict schema:
{
  "severity": "critical|high|medium|low|info",
  "confidence": 0.95,
  "threat_summary": "Executive summary...",
  "evidence": ["Evidence 1", "Evidence 2"],
  "recommended_actions": ["Action 1", "Action 2"],
  "affected_assets": ["1.2.3.4", "UserX"]
}
"""

    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment = os.getenv("MANAGER_MODEL", "gpt-4o")
        self.logger = logging.getLogger(__name__)

    async def plan_investigation(self, alert_text: str) -> InvestigationPlan:
        """
        Phase 1: Initial Planning
        Ask LLM to decompose the alert into a list of tasks.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT_PLANNER},
                    {"role": "user", "content": f"Alert: {alert_text}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )

            content = response.choices[0].message.content
            plan_dict = json.loads(content)
            return InvestigationPlan(**plan_dict)

        except Exception as e:
            self.logger.error(f"Planning failed: {str(e)}")
            return InvestigationPlan(
                thought_process="Planning failed, executing fallback.",
                tasks=[]
            )

    async def plan_next_step(self, state: InvestigationState) -> NextStepDecision:
        """
        NEW: ReAct Loop Decision
        Given the current investigation state, decide what to do next.
        """
        # Build context from state
        context = f"**Original Alert:** {state.alert_text}\n\n"
        context += f"**Investigation ID:** {state.id}\n"
        context += f"**Current Status:** {state.status}\n\n"
        
        if state.tasks_history:
            context += "**Tasks Completed So Far:**\n"
            for idx, task in enumerate(state.tasks_history, 1):
                context += f"{idx}. Agent: {task['agent']}, Action: {task['action']}\n"
                context += f"   Result: {json.dumps(task['output'], indent=2)}\n\n"
        else:
            context += "**No tasks executed yet.**\n\n"

        context += "**What should we do next?**"

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT_NEXT_STEP},
                    {"role": "user", "content": context}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )

            content = response.choices[0].message.content
            decision_dict = json.loads(content)
            
            self.logger.info(f"Manager Decision: {decision_dict.get('decision')} - {decision_dict.get('reasoning')}")
            
            return NextStepDecision(**decision_dict)

        except Exception as e:
            self.logger.error(f"Next step planning failed: {str(e)}")
            # Fallback: Stop the loop if we can't plan
            return NextStepDecision(
                decision="stop",
                reasoning=f"Planning error: {str(e)}",
                tasks=[]
            )

    async def synthesize_verdict(self, alert_text: str, task_results: List[Dict[str, Any]]) -> ThreatVerdict:
        """
        Phase 3: Synthesis
        Ask LLM to review all agent outputs and form a final opinion.
        """
        context = f"Original Alert: {alert_text}\n\nTask Results:\n"
        for res in task_results:
            context += f"- Agent: {res.get('agent')}\n"
            context += f"  Action: {res.get('action')}\n"
            context += f"  Output: {json.dumps(res.get('output'))}\n\n"

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT_VERDICT},
                    {"role": "user", "content": context}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )

            content = response.choices[0].message.content
            verdict_dict = json.loads(content)
            return ThreatVerdict(**verdict_dict)

        except Exception as e:
            self.logger.error(f"Synthesis failed: {str(e)}")
            return ThreatVerdict(
                severity="medium",
                confidence=0.0,
                threat_summary=f"Automated synthesis failed. Error: {str(e)}",
                evidence=[],
                recommended_actions=["Manual Review Required"],
                affected_assets=[]
            )
