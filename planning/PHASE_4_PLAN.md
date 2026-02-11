# PHASE-4: The ReAct Loop (Recursive Reasoning)

## 🎯 Objective
Transform the linear "Plan → Execute" script into a true **Autonomous Agent** that uses a recursive loop to think, act, observe, and adapt.

---

## 🧠 The Concept: Linear vs. Recursive

### 1. The Old Way (Linear Script)
Like a construction worker following a blueprint:
1.  **Manager:** "Here is a list of 3 tasks."
2.  **Worker:** Executes Task 1, 2, 3.
3.  **End:** Returns results.
*   **Flaw:** If Task 1 reveals a Critical Threat that requires *new* actions (like blocking a port), the linear script cannot adapt. It just finishes the pre-planned list.

### 2. The New Way (ReAct Loop)
Like a Detective solving a case:
1.  **Manager:** "Based on what we know *so far*, what is the next step?"
2.  **Action:** "Check IP reputation."
3.  **Observation:** "IP is malicious."
4.  **Loop:** Manager sees the new info. "Okay, *now* check if that IP logged in successfully."
5.  **Action:** "Query logs."
6.  **Observation:** "No successful logins."
7.  **Loop:** Manager sees new info. "Okay, we are done. Final Verdict: High Severity."

---

## 🏗️ Architecture Changes

### 1. Manager Agent (`src/agents/manager_agent.py`)
We added a new "Brain" function: `plan_next_step(state)`.
-   **Input:** The full history of the investigation (Alert + Completed Tasks).
-   **Output:** A decision (`continue` or `stop`) and a list of *new* tasks.
-   **Prompt Engineering:** We use a `SYSTEM_PROMPT_NEXT_STEP` that forces the LLM to review the `tasks_history` before deciding.

### 2. Investigation Service (`src/services/investigation_service.py`)
We replaced the linear execution flow with a `while` loop.
-   **Max Loops:** Safety limit (e.g., 10 iterations) to prevent infinite loops / cost spikes.
-   **Persistence:** We save the state to Cosmos DB after *every* single task. If the server crashes on Loop 3, we have a permanent record of everything up to that point.

---

## 🔄 The New Workflow

```mermaid
graph TD
    Start[New Alert] --> Create[Create DB Record]
    Create --> LoopStart{Loop Limit Reached?}
    LoopStart -->|No| AskManager[Manager: plan_next_step(State)]

    AskManager --> Decision{Decision?}
    Decision -->|Stop| Synthesis[Synthesize Verdict]
    Decision -->|Continue| Execute[Execute New Tasks]

    Execute --> UpdateDB[Update Cosmos DB]
    UpdateDB --> LoopStart

    LoopStart -->|Yes| Synthesis
    Synthesis --> End[Save Final Verdict]
```

---

## 🧪 Implementation Details

### A. The Decision Model
The Manager now returns this JSON structure for every loop iteration:

```json
{
  "decision": "continue",
  "reasoning": "The IP is confirmed malicious. Now I need to check for successful logins to determine impact.",
  "tasks": [
    {
      "agent": "analyst",
      "action": "analyze_logs",
      "params": { "query": "..." }
    }
  ]
}
```

### B. State Persistence (Cosmos DB)
We use the `InvestigationState` model (from Day 4) as our "Redux Store".
-   **Before Loop:** Create generic record.
-   **Inside Loop:** Append new results to `tasks_history`.
-   **After Loop:** Update `verdict` and mark `status="completed"`.

---

## 🚀 How to Test

1.  **Start the App:** `func start`
2.  **Send a Request:**
    ```bash
    curl -X POST http://localhost:7071/api/investigate \
    -H "Content-Type: application/json" \
    -d '{"alert": "Suspicious login attempts from 89.248.172.16"}'
    ```
3.  **Watch the Logs:** You will see the "Thinking Process":
    -   `--- ReAct Loop Iteration 1/10 ---`
    -   `Manager says: continue - Check IP reputation`
    -   `--- ReAct Loop Iteration 2/10 ---`
    -   `Manager says: continue - IP is bad. Check logs.`
    -   `--- ReAct Loop Iteration 3/10 ---`
    -   `Manager says: stop - Done.`

## ⏭️ Next Steps (PHASE 5)
-   **Evaluation:** How do we know it's working *well*? We will build a test suite with 10 different attack scenarios.
-   **PromptOps:** Tuning the prompts to handle edge cases (e.g., when the Analyst agent fails).
