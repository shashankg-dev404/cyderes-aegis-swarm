"""
Analyst Service - Orchestrates the code interpreter workflow
Coordinates between Agent, Executor, and Data Layer
"""

import pandas as pd
from pathlib import Path
from src.agents.analyst_agent import AnalystAgent
from src.utils.code_executor import SecureCodeExecutor, CodeExecutionError
from src.models.analyst_models import (
    AnalystRequest, 
    AnalystResponse, 
    CodeExecutionResult
)

class AnalystService:
    """
    Service layer for Analyst Agent operations
    
    Workflow:
    1. Load dataset
    2. Generate code via AnalystAgent
    3. Execute code via SecureCodeExecutor
    4. Self-correct if execution fails (retry once)
    5. Interpret results into natural language
    """

    MAX_RETRIES = 1

    def __init__(self):
        self.agent = AnalystAgent()
        self.dataframe_cache = {}  # Cache loaded CSVs

    def load_dataset(self, csv_path: str) -> pd.DataFrame:
        """
        Load CSV into pandas DataFrame (with caching)
        
        Args:
            csv_path: Path to firewall logs CSV
            
        Returns:
            Pandas DataFrame
        """
        if csv_path in self.dataframe_cache:
            return self.dataframe_cache[csv_path]
        
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {csv_path}")
        
        df = pd.read_csv(csv_path)
        self.dataframe_cache[csv_path] = df

        return df
    
    def analyze(self, request: AnalystRequest) -> AnalystResponse:
        """
        Main analysis workflow
        
        Args:
            request: AnalystRequest with query and csv_path
            
        Returns:
            AnalystResponse with code, results, and natural language answer
        """
        # Step 1: Load dataset
        df = self.load_dataset(request.csv_path)

        # Step 2: Generate initial code
        generated_code = self.agent.generate_code(request.query)
        
        # Step 3: Execute code
        executor = SecureCodeExecutor(df)
        exec_result = executor.execute(generated_code)

        # Step 4: Self-correction loop (if execution failed)
        retry_count = 0
        while not exec_result['success'] and retry_count < self.MAX_RETRIES:
            retry_count += 1

            # Ask agent to fix the code
            generated_code = self.agent.generate_code(
                request.query,
                retry_context=exec_result['error']
            )

            exec_result = executor.execute(generated_code)
        
        # Step 5: Interpret results
        if exec_result['success']:
            interpretation = self.agent.interpret_result(
                request.query,
                generated_code,
                exec_result['output']
            )
            natural_answer = interpretation['answer']
            confidence = interpretation['confidence']
        else:
            # Failed even after retry
            natural_answer = f"Unable to analyze: {exec_result['error']}"
            confidence = "low"
        
        # Step 6: Build response
        return AnalystResponse(
            query=request.query,
            generated_code=generated_code,
            execution_result=CodeExecutionResult(**exec_result),
            natural_language_answer=natural_answer,
            confidence=confidence,
            data_summary={
                "total_records": len(df),
                "dataset_path": request.csv_path
            }
        )


# Singleton instance
_service_instance = None

def get_analyst_service() -> AnalystService:
    """Get or create AnalystService singleton"""
    global _service_instance
    if _service_instance is None:
        _service_instance = AnalystService()
    return _service_instance
