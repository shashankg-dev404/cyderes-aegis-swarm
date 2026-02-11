# Day 2: Analyst Agent (Code Interpreter)

## 🎯 Objective
Build an AI agent that writes and executes Python/Pandas code to analyze the 50k security logs we generated on Day 1.

---

## 🧠 What is a Code Interpreter Agent?

**Traditional AI:**
- User: "How many brute force attacks from 89.248.172.16?"
- AI: "I don't have access to your data, I can only guess..."

**Code Interpreter Agent:**
- User: "How many brute force attacks from 89.248.172.16?"
- AI: *Writes Python code* → `df[df['source_ip'] == '89.248.172.16'].shape[0]`
- AI: *Executes code* → Result: 1,667 attempts
- AI: "There were 1,667 brute force attempts from that IP"

**Why this matters for SecOps:**
- Security analysts ask complex questions: "Find all IPs that scanned more than 50 ports in under 10 minutes"
- Writing SQL/Python for every query is slow
- The AI becomes a **data analyst partner** that writes queries for you

---

## 🏗️ Architecture Overview

```
User Query: "Find suspicious IPs with 500+ requests"
         ↓
    Analyst Agent
         ↓
   [Generate Python Code]
         ↓
   pandas_executor.py (Safe Sandbox)
         ↓
   Execute: df[df.groupby('source_ip').size() > 500]
         ↓
   Return Results to Agent
         ↓
   Agent Formats Final Answer
```

### Key Components We'll Build:

1. **`src/agents/analyst_agent.py`** - The AI brain that generates code
2. **`src/utils/code_executor.py`** - Secure sandbox that runs the code
3. **`src/models/analyst_models.py`** - Pydantic schemas for requests/responses
4. **`src/services/analyst_service.py`** - Orchestration layer
5. **`src/routers/analyst_router.py`** - API endpoint
6. **Test script** - Validate with real queries

---

## 🔒 Security Concerns (Critical!)

**The Problem:**
If we let AI write ANY Python code, a malicious user could ask:
- "Delete all files on the server"
- "Send my AWS keys to attacker.com"

**Our Solution: Restricted Execution Environment**

```python
ALLOWED_IMPORTS = ['pandas', 'numpy', 'datetime']
FORBIDDEN_PATTERNS = ['os.', 'subprocess', 'eval(', 'exec(', '__import__']

def execute_code(code: str):
    # 1. Check for forbidden patterns
    # 2. Only allow pandas operations on the CSV
    # 3. Set 5-second timeout
    # 4. Capture output and return
```

---

## 📊 Example Queries the Analyst Agent Will Handle

| Query | Expected Code | Purpose |
|-------|---------------|---------|
| "How many total attacks?" | `df[df['alert_type'] != 'benign'].shape[0]` | Simple count |
| "Top 5 attacking IPs" | `df['source_ip'].value_counts().head(5)` | Aggregation |
| "Brute force attempts from 89.248.172.16" | `df[(df['alert_type']=='brute_force') & (df['source_ip']=='89.248.172.16')]` | Filtering |
| "Average bytes sent in data exfil" | `df[df['alert_type']=='data_exfiltration']['bytes_sent'].mean()` | Statistics |
| "Port scan timeline" | `df[df['alert_type']=='port_scan'][['timestamp','source_ip','dest_port']]` | Temporal analysis |

---

## 🛠️ Implementation Steps

### Step 1: Create Pydantic Models
Define the data shapes for input/output.

**File:** `src/models/analyst_models.py`

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional

class AnalystRequest(BaseModel):
    """User's question about the security logs"""
    query: str = Field(..., description="Natural language question")
    csv_path: str = Field(default="data/raw/firewall_logs.csv")

class CodeExecutionResult(BaseModel):
    """Result of executing generated code"""
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: float

class AnalystResponse(BaseModel):
    """Final answer from the Analyst Agent"""
    query: str
    generated_code: str
    execution_result: CodeExecutionResult
    natural_language_answer: str
    confidence: Literal["high", "medium", "low"]
```

---

### Step 2: Build the Code Executor
Safely run AI-generated Python in a sandbox.

**File:** `src/utils/code_executor.py`

**Key Features:**
1. Imports whitelist (only pandas, numpy, datetime allowed)
2. Pattern blacklist (blocks os, subprocess, eval, exec)
3. Timeout protection (kills code after 5 seconds)
4. Exception handling (captures errors without crashing)

---

### Step 3: Build the Analyst Agent
The AI that generates pandas code from natural language.

**File:** `src/agents/analyst_agent.py`

**System Prompt:**
```
You are a cybersecurity data analyst. Given a question about firewall logs, 
write Python pandas code to answer it.

Dataset schema:
- timestamp: ISO datetime
- source_ip, dest_ip: IPv4 addresses
- source_port, dest_port: integers
- protocol: TCP/UDP
- action: ALLOW/BLOCK
- bytes_sent, bytes_received: integers
- alert_type: benign, sql_injection, brute_force, port_scan, data_exfiltration, dos_attack

RULES:
1. DataFrame is already loaded as 'df'
2. Only use pandas, numpy, datetime
3. Return a printable result (use print() or return a value)
4. Keep code under 10 lines
```

---

### Step 4: Service Layer
Orchestrates: User Query → Agent → Executor → Response

**File:** `src/services/analyst_service.py`

**Flow:**
1. Load CSV into pandas DataFrame
2. Send user query + schema to GPT-4o
3. AI generates code
4. Validate code (security checks)
5. Execute code with DataFrame
6. If error: retry with error message (self-correction)
7. Format final answer

---

### Step 5: API Router
Expose the analyst via HTTP endpoint.

**File:** `src/routers/analyst_router.py`

Endpoint: `POST /api/analyze-logs`

---

### Step 6: Integration
Wire everything into `function_app.py`

---

## 🧪 Test Scenarios

After implementation, we'll test with:

1. **Simple Count**: "How many SQL injection attempts?"
2. **Aggregation**: "Which IP has the most brute force attempts?"
3. **Time-based**: "How many attacks happened in the last 24 hours of logs?"
4. **Complex Filter**: "Find IPs that did both port scanning AND data exfiltration"
5. **Statistical**: "What's the average data transfer size for benign traffic vs data exfiltration?"

---

## 📈 Success Criteria

By end of Day 2, you should be able to:

✅ Send a natural language query via API  
✅ Receive AI-generated pandas code  
✅ Get execution results with actual data  
✅ See a human-readable answer  
✅ Handle errors gracefully (invalid code, timeouts)  

---

## 🎓 Interview Talking Points

**Q: Why build a code interpreter instead of just asking GPT-4o directly?**

**A:** "GPT-4o doesn't have access to our live data. It can't run queries. A code interpreter agent:
1. **Grounds answers in real data** (no hallucinations about numbers)
2. **Handles complex queries** that need aggregation, filtering, joins
3. **Is deterministic** - same query always returns same result
4. **Is auditable** - we can review the generated code before execution"

**Q: How do you prevent the AI from executing malicious code?**

**A:** "I implemented a three-layer security model:
1. **Whitelist imports** - only pandas, numpy, datetime allowed
2. **Blacklist patterns** - regex blocks os, subprocess, eval, exec
3. **Sandboxed execution** - code runs in restricted namespace with 5-second timeout
4. **No file system access** - DataFrame is passed in-memory, code can't read/write files"

**Q: What if the generated code has a bug?**

**A:** "I implemented a self-correction loop:
1. Execute code
2. If error, send error message back to GPT-4o
3. Ask it to fix the code
4. Retry (max 2 attempts)
This pattern is called 'ReAct' (Reasoning + Acting) and is standard in agentic systems."

---

## 🚀 Day 3 Preview

Tomorrow we'll build the **Manager Agent** that:
- Takes high-level alerts like "Suspicious activity from 89.248.172.16"
- Breaks it into sub-tasks: "Check IP reputation" + "Analyze traffic patterns"
- Decides which agent to call (Analyst vs Intel)
- Combines results into final verdict

---

## 📚 Key Concepts Learned

1. **Code Interpreter Pattern**: AI writes code → Execute safely → Return results
2. **Sandboxed Execution**: Restrict what code can do (imports, patterns, timeout)
3. **Self-Correction Loop**: If code fails, AI debugs itself
4. **Structured Outputs**: Force AI to return valid JSON (Pydantic models)
5. **Service Layer Pattern**: Keep API endpoints thin, logic in services

---

**Estimated Time:** 3-4 hours  
**Lines of Code:** ~400 lines  
**Dependencies:** openai, pandas, pydantic  

Let's start building! 🔨
