"""
Intel Agent - Threat Intelligence & IP Reputation
Provides context about IPs, domains, and other security indicators
"""

import os
import logging
import httpx
from datetime import datetime
from typing import Dict, Any, Optional
from src.models.intel_models import IPReputationResponse

class IntelAgent:
    """
    Agent responsible for gathering threat intelligence.
    Capabilities:
    1. IP Reputation Lookup (AbuseIPDB + Mock)
    2. Threat Context Enrichment
    """

    # Internal Mock DB for testing/fallback
    MOCK_DB = {
        "89.248.172.16": {
            "reputation": "malicious",
            "category": "brute_force_attacker",
            "threat_score": 95,
            "details": "Known SSH/RDP brute force scanner reported by multiple sources.",
            "geolocation": {"country": "NL", "isp": "BadHosting Corp"}
        },
        "185.220.101.17": {
            "reputation": "malicious", 
            "category": "tor_exit_node",
            "threat_score": 85,
            "details": "Active TOR network exit node. Traffic is anonymized.",
            "geolocation": {"country": "DE", "isp": "Tor Exit Service"}
        },
        "8.8.8.8": {
            "reputation": "benign",
            "category": "dns_server",
            "threat_score": 0,
            "details": "Google Public DNS. Trusted infrastructure.",
            "geolocation": {"country": "US", "isp": "Google LLC"}
        },
        "1.1.1.1": {
            "reputation": "benign",
            "category": "dns_server",
            "threat_score": 0,
            "details": "Cloudflare Public DNS.",
            "geolocation": {"country": "US", "isp": "Cloudflare Inc"}
        }
    }

    def __init__(self):
        self.api_key = os.getenv("ABUSEIPDB_API_KEY")
        self.base_url = "https://api.abuseipdb.com/api/v2"
        self.logger = logging.getLogger(__name__)

    async def lookup_ip(self, ip_address) -> IPReputationResponse:
        """
        Check IP reputation. Tries AbuseIPDB first, falls back to Mock DB.
        """
        # 1. Try AbuseIPDB if Key exists
        if self.api_key:
            try:
                return await self._query_abuseipdb(ip_address)
            except Exception as e:
                self.logger.warning(f"AbuseIPDB lookup failed for {ip_address}: {str(e)}. Using fallback.")
        
        # 2. Fallback to Mock DB
        return self._query_mock_db(ip_address)
    
    async def _query_abuseipdb(self, ip_address: str) -> IPReputationResponse:
        """Query AbuseIPDB API"""
        url = f"{self.base_url}/check"
        headers = {
            'Key': self.api_key,
            'Accept': 'application/json'
        }
        params = {
            'ipAddress': ip_address,
            'maxAgeInDays': 90
        }

        # Use httpx for async request
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params, timeout=5.0)
        response.raise_for_status()
        data = response.json()['data']

        # Map API response to our schema
        score = data.get('abuseConfidenceScore', 0)

        # Determine reputation based on score
        if score > 80:
            reputation = "malicious"
        elif score > 20:
            reputation = "suspicious"
        else:
            reputation = "benign"

        return IPReputationResponse(
            ip_address=ip_address,
            reputation=reputation,
            threat_score=score,
            category="abuse_report" if score > 0 else "clean",
            details=f"Usage Type: {data.get('usageType', 'Unknown')}. Domain: {data.get('domain', 'N/A')}",
            last_seen=datetime.now(), # AbuseIPDB provides lastReportedAt, simplified here
            geolocation={
                "country": data.get("countryCode"),
                "isp": data.get("isp")
            },
            source="abuseipdb"
        )
    
    def _query_mock_db(self, ip_address: str) -> IPReputationResponse:
        """Query internal Mock DB"""
        if ip_address in self.MOCK_DB:
            record = self.MOCK_DB[ip_address]
            return IPReputationResponse(
                ip_address=ip_address,
                reputation=record["reputation"],
                threat_score=record["threat_score"],
                category=record["category"],
                details=record["details"],
                geolocation=record.get("geolocation"),
                source="mock_db"
            )
        
        # Unknown IP
        return IPReputationResponse(
            ip_address=ip_address,
            reputation="unknown",
            threat_score=0,
            category="unknown",
            details="No intelligence found in internal database.",
            source="mock_db_miss"
        )