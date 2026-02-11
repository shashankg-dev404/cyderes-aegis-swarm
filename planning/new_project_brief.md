# Project Brief: Auto-SOC (Multi-Agent Threat Hunter)

**Role Context**: Full-Stack AI Engineer (Python, Azure, Agentic Systems)
**Objective**: Build a production-grade "Swarm" of AI Agents that autonomously investigate and remediate security incidents. This project is designed to demonstrate advanced skills required for the Cyderes JD (Multi-agent orchestration, State management, Data Analysis).

## 1. Architecture Overview
Instead of a single bot, we are building a team:
1.  **Manager Agent (Orchestrator)**: Breaks down high-level alerts into tasks. Maintains the "State" of the investigation.
2.  **Analyst Agent (Code Interpreter)**: Writes and executes Python/Pandas code to analyze raw CSV logs (simulating Splunk/KQL).
3.  **Intel Agent (Researcher)**: Uses external tools to check IP reputation and threat intelligence.

## 2. Tech Stack
*   **Language**: Python 3.11+
*   **Core Framework**: Azure Functions (Serverless)
*   **AI Logic**: Azure OpenAI (GPT-4o) + Instructor (Structured Outputs)
*   **Orchestration**: Custom State Machine (or LangGraph concept)
*   **Memory/State**: Azure CosmosDB (NoSQL)
*   **Data Storage**: Azure Blob Storage (Log Lake)
*   **Infrastructure**: Azure Bicep / CLI

## 3. The 7-Day Sprint Plan

| Phase | Focus Area | Deliverable |
| :--- | :--- | :--- |
| **Phase 1** | **The Data Lake** | Python script using `Faker` to generate 50k rows of realistic security logs (SQL Injection, Brute Force). Upload to Azure Blob. |
| **Phase 2** | **Analyst Agent** | Build a "Code Interpreter" tool. The AI writes Python code to query the CSVs (e.g., "Find all IPs with 500+ requests"). |
| **Phase 3** | **Manager Agent** | Implement the "Planner" logic. The Manager takes a vague alert and decides *which* agent to call next. |
| **Phase 4** | **State Management** | Connect **Azure CosmosDB**. Ensure the agents remember the investigation context across multiple API calls. |
| **Phase 5** | **The Loop** | Implement the recursive "Plan $\rightarrow$ Execute $\rightarrow$ Observe" loop. The swarm runs until the threat is neutralized. |
| **Phase 6** | **Evaluation** | Run the swarm against 10 different attack scenarios. Measure success rate and tokens used (PromptOps). |
| **Phase 7** | **Cloud Deploy** | Deploy the entire multi-agent system to Azure Functions with a CI/CD pipeline. |

