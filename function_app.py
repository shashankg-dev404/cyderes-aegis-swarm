"""
Cyderes Aegis Swarm - Azure Functions Entry Point
Multi-Agent Security Operations Center
"""

import azure.functions as func
import logging

from src.routers.investigation_router import investigation_bp
from src.routers.analyst_router import analyst_bp

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

app.register_functions(investigation_bp)
app.register_functions(analyst_bp)

@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Health check called")
    return func.HttpResponse(
        body='{"status": "healthy", "service": "Cyderes Aegis Swarm"}',
        status_code=200,
        mimetype="application/json"
    )
