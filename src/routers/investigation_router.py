import azure.functions as func
import logging
import json
from pydantic import ValidationError
from src.models.manager_models import InvestigationRequest
from src.services.investigation_service import get_investigation_service
from src.services.cosmos_service import get_cosmos_service

# Create a Blueprint (Group of routes)
investigation_bp = func.Blueprint()

@investigation_bp.route(route="investigate", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
async def investigate(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/investigate
    Starts a new investigation.
    """
    logging.info('Python HTTP trigger function processed a request.')

    try:
        # 1. Parse Input
        req_body = req.get_json()
        
        # Validate with Pydantic
        # If 'priority' is missing, it defaults to 'medium' per the model
        request_model = InvestigationRequest(**req_body)

        # 2. Call Service
        service = get_investigation_service()
        state = await service.run_investigation(request_model)

        # 3. Return Result
        # We use .model_dump_json() to automatically handle all nested objects
        return func.HttpResponse(
            state.model_dump_json(),
            mimetype="application/json",
            status_code=200
        )

    except ValidationError as e:
        return func.HttpResponse(
            json.dumps({"error": "Invalid input", "details": e.errors()}),
            status_code=400,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal Server Error", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@investigation_bp.route(route="investigation/{id}", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
async def get_investigation_status(req: func.HttpRequest) -> func.HttpResponse:
    """
    GET /api/investigation/{id}
    Retrieves the current state of an investigation from Cosmos DB.
    """
    inv_id = req.route_params.get('id')
    
    try:
        # Direct DB Access (CQRS Pattern: Read side doesn't need domain logic)
        cosmos = get_cosmos_service()
        state = cosmos.get_investigation(inv_id)
        
        if not state:
            return func.HttpResponse(
                json.dumps({"error": "Investigation not found"}),
                status_code=404,
                mimetype="application/json"
            )

        return func.HttpResponse(
            state.model_dump_json(),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logging.error(f"Error retrieving investigation: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to retrieve investigation", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
