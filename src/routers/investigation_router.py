"""
Investigation Router - API Endpoint
Handles HTTP requests for /api/investigate
"""

import azure.functions as func
import logging
import json
from src.models.manager_models import InvestigationRequest
from src.services.investigation_service import get_investigation_service

async def handle_investigate(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/investigate
    
    Trigger a multi-agent investigation.
    
    Request Body:
    {
        "alert": "Suspicious login attempts from 89.248.172.16",
        "priority": "high"
    }
    """
    logging.info("Investigation endpoint called")

    try:
        # 1. Parse Request
        # Get JSON body safely
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                body=json.dumps({"error": "Invalid JSON body"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Validate with Pydantic
        # This ensures 'alert' exists and 'priority' is valid
        try:
            investigation_req = InvestigationRequest(**req_body)
        except Exception as e:
            return func.HttpResponse(
                body=json.dumps({"error": f"Schema validation failed: {str(e)}"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # 2. Call Service
        # Pass the validated object to the business logic
        service = get_investigation_service()
        response = await service.run_investigation(investigation_req)

        # 3. Return Response
        # Convert the full report to JSON
        return func.HttpResponse(
            body=response.model_dump_json(indent=2),
            status_code=200,
            mimetype='application/json'
        )
    
    except Exception as e:
        # Catch-all for unexpected crashes
        logging.error(f"Investigation failed: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"error": "Internal Server Error", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )