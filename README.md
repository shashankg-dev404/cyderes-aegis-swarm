# Cyderes Aegis Swarm

Multi-Agent AI system for autonomous security threat investigation and remediation.

## Architecture

- **Manager Agent**: Orchestrates investigation, breaks down tasks
- **Analyst Agent**: Executes Python/Pandas code on log data
- **Intel Agent**: Performs IP reputation and threat intelligence lookups

## Tech Stack

- Azure Functions (Serverless)
- Azure OpenAI (GPT-4o)
- Azure CosmosDB (State Management)
- Azure Blob Storage (Data Lake)
- Python 3.11+

## Project Status

- [x] Day 1: Data Lake Generation
- [ ] Day 2: Analyst Agent (Code Interpreter)
- [ ] Day 3: Manager Agent (Orchestrator)
- [ ] Day 4: State Management (CosmosDB)
- [ ] Day 5: The Agentic Loop
- [ ] Day 6: Evaluation Framework
- [ ] Day 7: Cloud Deployment

## Setup

```bash
# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Generate security logs
python scripts/generate_logs.py