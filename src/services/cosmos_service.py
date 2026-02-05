"""
Cosmos Service - The Database Driver

Handles all Read/Write operations to Azure Cosmos DB.
"""

import os
import logging
from typing import Optional, List
from azure.cosmos import CosmosClient, PartitionKey
from src.models.state_models import InvestigationState

class CosmosService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Load credentials from environment variables
        self.url = os.getenv("COSMOS_ENDPOINT")
        self.key = os.getenv("COSMOS_KEY")
        self.db_name = os.getenv("COSMOS_DATABASE_NAME", "aegis-swarm")
        self.container_name = os.getenv("COSMOS_CONTAINER_NAME", "investigation-state")

        if not self.url or not self.key:
            raise ValueError("Missing COSMOS_ENDPOINT or COSMOS_KEY in environment variables")
        
        # Initialize the Azure Client
        self.client = CosmosClient(self.url, credential=self.key)
        self.database = self.client.get_database_client(self.db_name)
        self.container = self.database.get_container_client(self.container_name)

    def create_investigation(self, alert_text: str) -> InvestigationState:
        """
        Start a new investigation document.
        Equivalent to: INSERT INTO c VALUES (...)
        """
        # Create the Python object
        state = InvestigationState(alert_text=alert_text)

        # Save to DB (convert to JSON dict first)
        self.container.create_item(body=state.model_dump(mode="json"))

        self.logger.info(f"Created new investigation: {state.id}")
        return state
        
    def get_investigation(self, investigation_id: str) -> Optional[InvestigationState]:
        """
        Retrieve state by ID.
        Equivalent to: SELECT * FROM c WHERE c.id = '...'
        """
        try:
            # We must provide the partition key (id) for fast lookup
            item = self.container.read_item(
                item=investigation_id,
                partition_key=investigation_id
            )
            # Convert JSON back to Pydantic object
            return InvestigationState(**item)
        except Exception as e:
            self.logger.warning(f"Investigation {investigation_id} not found: {str(e)}")
            return None
        
    def update_investigation(self, state: InvestigationState) -> InvestigationState:
        """
        Save changes to an existing investigation.
        Equivalent to: UPDATE c SET ... WHERE c.id = ...
        """
        # upsert_item = "Update if exists, Insert if new"
        self.container.upsert_item(body=state.model_dump(mode="json"))
        self.logger.info(f"Updated investigation: {state.id}")
        return state
    
    def list_recent_investigations(self, limit: int = 10) -> List[InvestigationState]:
        """
        Get the last N investigations.
        Uses a SQL query.
        """
        query = f"SELECT * FROM c ORDER BY c.created_at DESC OFFSET 0 LIMIT {limit}"
        items = self.container.query_items(
            query=query,
            enable_cross_partition_query=True
        )
        return [InvestigationState(**item) for item in items]
    
# Singleton Instance
_cosmos_instance = None

def get_cosmos_service() -> CosmosService:
    global _cosmos_instance
    if _cosmos_instance is None:
        _cosmos_instance = CosmosService()
    return _cosmos_instance