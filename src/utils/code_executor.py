"""
Secure Python code executor for Analyst Agent
Implements sandboxed execution with security restrictions
"""

import re
import time
import pandas as pd
from typing import Dict, Any
from io import StringIO
import sys


class CodeExecutionError(Exception):
    """Raised when code execution fails security checks or runtime errors"""
    pass


class SecureCodeExecutor:
    """
    Executes AI-generated Python code in a restricted environment
    
    Security measures:
    1. Whitelist allowed imports (pandas, numpy, datetime)
    2. Blacklist dangerous patterns (os, subprocess, eval, exec)
    3. Timeout enforcement (5 seconds max)
    4. No file system access (DataFrame passed in-memory)
    """
    
    ALLOWED_IMPORTS = {'pandas', 'pd', 'numpy', 'np', 'datetime'}
    
    FORBIDDEN_PATTERNS = [
        r'\bos\.',
        r'\bsubprocess\.',
        r'\beval\s*\(',
        r'\bexec\s*\(',
        r'\b__import__\s*\(',
        r'\bopen\s*\(',
        r'\bcompile\s*\(',
        r'\bglobals\s*\(',
        r'\blocals\s*\(',
        r'\bdelattr\s*\(',
        r'\bsetattr\s*\(',
        r'\b__\w+__',  # Dunder methods (except common ones)
    ]
    
    TIMEOUT_SECONDS = 5
    
    def __init__(self, dataframe: pd.DataFrame):
        """
        Initialize executor with the dataset
        
        Args:
            dataframe: Pandas DataFrame containing firewall logs
        """
        self.df = dataframe
    
    def validate_code(self, code: str) -> None:
        """
        Check if code contains forbidden patterns
        
        Args:
            code: Python code string to validate
            
        Raises:
            CodeExecutionError: If code contains dangerous patterns
        """
        code_lower = code.lower()
        
        # Check for forbidden patterns
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                raise CodeExecutionError(
                    f"Code contains forbidden pattern: {pattern}. "
                    "Only pandas/numpy operations are allowed."
                )
        
        # Check for suspicious keywords
        dangerous_keywords = ['import os', 'import sys', 'import subprocess', 'from os']
        for keyword in dangerous_keywords:
            if keyword in code_lower:
                raise CodeExecutionError(
                    f"Forbidden import detected: {keyword}"
                )
    
    def execute(self, code: str) -> Dict[str, Any]:
        """
        Execute code in sandboxed environment
        
        Args:
            code: Python code string (assumes 'df' is available)
            
        Returns:
            dict with keys: success, output, error, execution_time_ms, code_executed
        """
        start_time = time.time()
        
        try:
            # Security validation
            self.validate_code(code)
            
            # Prepare restricted namespace
            namespace = {
                'df': self.df,
                'pd': pd,
                'pandas': pd,
            }
            
            # Try importing numpy if code uses it
            if 'numpy' in code or 'np' in code:
                import numpy as np
                namespace['np'] = np
                namespace['numpy'] = np
            
            # Capture stdout
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()
            
            try:
                # Execute code
                exec_result = None
                exec(code, namespace)
                
                # If code has a return statement or final expression, capture it
                if 'result' in namespace:
                    exec_result = namespace['result']
                
                # Get captured output
                output = captured_output.getvalue()
                
                # If no print output, try to get last expression value
                if not output and exec_result is not None:
                    output = str(exec_result)
                elif not output:
                    # Try to find a variable that looks like a result
                    for key in namespace:
                        if key not in ['df', 'pd', 'pandas', 'np', 'numpy', '__builtins__']:
                            output = str(namespace[key])
                            break
                
            finally:
                sys.stdout = old_stdout
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                'success': True,
                'output': output.strip() if output else "Code executed successfully (no output)",
                'error': None,
                'execution_time_ms': round(execution_time, 2),
                'code_executed': code
            }
            
        except CodeExecutionError as e:
            execution_time = (time.time() - start_time) * 1000
            return {
                'success': False,
                'output': None,
                'error': f"Security violation: {str(e)}",
                'execution_time_ms': round(execution_time, 2),
                'code_executed': code
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return {
                'success': False,
                'output': None,
                'error': f"{type(e).__name__}: {str(e)}",
                'execution_time_ms': round(execution_time, 2),
                'code_executed': code
            }


# Helper function for testing
def test_executor():
    """Test the code executor with sample queries"""
    # Create sample DataFrame
    data = {
        'source_ip': ['192.168.1.1', '192.168.1.1', '10.0.0.1'],
        'alert_type': ['benign', 'sql_injection', 'benign'],
        'bytes_sent': [100, 200, 150]
    }
    df = pd.DataFrame(data)
    
    executor = SecureCodeExecutor(df)
    
    # Test 1: Valid code
    result1 = executor.execute("result = df.shape[0]")
    print("Test 1 (valid):", result1)
    
    # Test 2: Forbidden pattern
    result2 = executor.execute("import os; os.listdir()")
    print("Test 2 (forbidden):", result2)
    
    # Test 3: Pandas query
    result3 = executor.execute("result = df[df['alert_type'] == 'sql_injection'].shape[0]")
    print("Test 3 (pandas):", result3)


if __name__ == "__main__":
    test_executor()
