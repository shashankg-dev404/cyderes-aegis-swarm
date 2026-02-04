"""
Analyst Agent - Code Interpreter for Security Log Analysis
Generates and executes Python/Pandas code to answer natural language queries
"""

import os
import json
from typing import Dict, Any
from openai import AzureOpenAI

class AnalystAgent:
    """
    AI agent that writes Python code to analyze security logs
    
    Workflow:
    1. Receive natural language query
    2. Generate pandas code using GPT-4o
    3. Return code for execution by SecureCodeExecutor
    """
    
    SYSTEM_PROMPT = """You are an expert cybersecurity data analyst specializing in network security logs.

Your job is to write Python pandas code to answer questions about firewall logs.

**Dataset Schema:**
The DataFrame 'df' contains these columns:
- timestamp (str): ISO datetime format
- source_ip (str): Source IPv4 address
- dest_ip (str): Destination IPv4 address  
- source_port (int): Source port number
- dest_port (int): Destination port number
- protocol (str): TCP or UDP
- action (str): ALLOW or BLOCK
- bytes_sent (int): Bytes sent by source
- bytes_received (int): Bytes received by source
- user_agent (str): HTTP user agent (or N/A)
- request_path (str): HTTP path (or N/A)
- http_status (int): HTTP status code (or 0)
- session_id (str): Session identifier
- alert_type (str): benign, sql_injection, brute_force, port_scan, data_exfiltration, dos_attack

**CRITICAL RULES:**
1. The DataFrame is already loaded as 'df' - do NOT add import statements
2. Store your final result in a variable called 'result'
3. Use ONLY pandas, numpy, and datetime operations
4. Keep code under 10 lines
5. Handle edge cases (empty results, division by zero)
6. Return ONLY the Python code, no explanations

**Example Queries:**

Query: "How many total attacks?"
Code:

result = df[df['alert_type'] != 'benign'].shape[0]


Query: "Which IP has the most brute force attempts?"
Code:

brute_force_df = df[df['alert_type'] == 'brute_force']
if len(brute_force_df) > 0:
    result = brute_force_df['source_ip'].value_counts().head(1)
else:
    result = "No brute force attempts found"


Query: "Average bytes sent in SQL injection attacks"
Code:

sql_inj = df[df['alert_type'] == 'sql_injection']
result = sql_inj['bytes_sent'].mean() if len(sql_inj) > 0 else 0


Now generate code for the following query. Return ONLY executable Python code, nothing else.
"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment = os.getenv("ANALYST_MODEL", "gpt-4o")
    
    def generate_code(self, query: str, retry_context: str = None) -> str:
        """
        Generate Python code to answer the query
        
        Args:
            query: Natural language question
            retry_context: If previous attempt failed, include error for self-correction
            
        Returns:
            Python code as string
        """
        user_message = f"Query: {query}"
        
        if retry_context:
            user_message += f"\n\nPrevious attempt failed with error:\n{retry_context}\n\nPlease fix the code."
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,  # Low temperature for deterministic code
                max_tokens=500
            )
            
            code = response.choices[0].message.content.strip()
            
            # Clean up code (remove markdown formatting if present)
            if code.startswith("```python"):
                code = code.replace("```python", "").replace("```", "").strip()
            elif code.startswith("```"):
                code = code.replace("```", "").strip()
            
            return code
            
        except Exception as e:
            raise Exception(f"Failed to generate code: {str(e)}")
    
    def interpret_result(self, query: str, code: str, execution_output: str) -> Dict[str, Any]:
        """
        Convert code execution result into natural language answer
        
        Args:
            query: Original user question
            code: The code that was executed
            execution_output: Result from code execution
            
        Returns:
            dict with 'answer' and 'confidence' keys
        """
        interpretation_prompt = f"""Given this security log analysis:

        User Question: {query}
        Code Executed: {code}
        Result: {execution_output}

        Provide a clear, concise answer to the user's question in 1-2 sentences.
        If the result is a number, include context. If it's a list, summarize key findings.
        Be direct and professional.

        Also rate your confidence: high, medium, or low.

        Return your response as JSON:
        {{"answer": "your answer here", "confidence": "high/medium/low"}}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "user", "content": interpretation_prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            # Fixed access pattern here: choices[0]
            content = response.choices[0].message.content.strip()
            
            # Clean markdown if present
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            
            result = json.loads(content)
            return result
            
        except Exception as e:
            # Fallback if interpretation fails
            return {
                "answer": f"Analysis complete. Result: {execution_output}",
                "confidence": "medium"
            }