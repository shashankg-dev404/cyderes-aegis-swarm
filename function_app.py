"""
Cyderes Aegis Swarm - Azure Functions Entry Point
Multi-Agent Security Operations Center
"""

import azure.functions as func
import logging
from src.routers.analyst_router import handle_analyze_logs
from src.routers.investigation_router import handle_investigate # <--- NEW IMPORT

# Create Function App
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    logging.info("Health check called")
    return func.HttpResponse(
        body='{"status": "healthy", "service": "Cyderes Aegis Swarm", "day": "3"}', # Updated Day
        status_code=200,
        mimetype="application/json"
    )

@app.route(route="analyze-logs", methods=["POST"])
async def analyze_logs(req: func.HttpRequest) -> func.HttpResponse:
    """Analyst Agent endpoint"""
    return await handle_analyze_logs(req)

# --- NEW ENDPOINT ---
@app.route(route="investigate", methods=["POST"])
async def investigate(req: func.HttpRequest) -> func.HttpResponse:
    """
    Manager Agent endpoint - Full Investigation Orchestration
    """
    return await handle_investigate(req)
