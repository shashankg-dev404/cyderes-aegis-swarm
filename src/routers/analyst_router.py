"""
API Router for Analyst Agent
Exposes HTTP endpoints for log analysis
"""

import azure.functions as func
import logging
import json
from src.models.analyst_models import AnalystRequest
from src.services.analyst_service import get_analyst_service


async def handle_analyze_logs(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/analyze-logs
    
    Request body:
    {
        "query": "How many SQL injection attempts?",
        "csv_path": "data/raw/firewall_logs.csv"  // optional
    }
    
    Response:
    {
        "query": "...",
        "generated_code": "...",
        "execution_result": {...},
        "natural_language_answer": "...",
        "confidence": "high"
    }
    """
    logging.info("Analyst endpoint called")
    
    try:
        # Parse request
        req_body = req.get_json()
        analyst_request = AnalystRequest(**req_body)
        
        # Process via service layer
        service = get_analyst_service()
        response = service.analyze(analyst_request)
        
        # Return JSON response
        return func.HttpResponse(
            body=response.model_dump_json(indent=2),
            status_code=200,
            mimetype="application/json"
        )
        
    except ValueError as e:
        return func.HttpResponse(
            body=json.dumps({"error": f"Invalid request: {str(e)}"}),
            status_code=400,
            mimetype="application/json"
        )
    
    except FileNotFoundError as e:
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            status_code=404,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Analysis failed: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"error": f"Internal error: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )
