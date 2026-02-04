"""
Manager Agent - The Orchestrator
Responsibility: Planning, Delegation, and Synthesis
"""

import os
import json
import logging
from typing import List, Dict, Any
from openai import AzureOpenAI
from src.models.manager_models import InvestigationPlan, ThreatVerdict, AgentTask

class ManagerAgent:
    """
    Orchestrates the investigation by decomposing alerts into agent tasks
    and synthesizing results into a final verdict.
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
        "reasoning": "Check if IP is known malicious"  <-- CRITICAL ADDITION
        },
        {
        "agent": "analyst",
        "action": "analyze_logs",
        "params": {"query": "..."},
        "reasoning": "Check for successful attacks"    <-- CRITICAL ADDITION
        }
    ]
    }
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
        Phase 1: Planning
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
                temperature=0.1 # Low temp for strict planning
            )

            content = response.choices[0].message.content
            plan_dict = json.loads(content)

            # Validate with Pydantic
            return InvestigationPlan(**plan_dict)
        
        except Exception as e:
            self.logger.error(f"Planning failed: {str(e)}")
            # Fallback plan if LLM fails
            return InvestigationPlan(
                thought_process="Planning failed, executing fallback.",
                tasks=[]
            )

    async def synthesize_verdict(self, alert_text: str, task_results: List[Dict[str, Any]]) -> ThreatVerdict:
        """
        Phase 3: Synthesis
        Ask LLM to review all agent outputs and form a final opinion.
        """

        # Format results for the LLM
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
        
