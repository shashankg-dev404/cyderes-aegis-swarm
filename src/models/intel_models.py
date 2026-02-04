"""
Pydantic models for Intel Agent
Threat intelligence and IP reputation schemas
"""

from pydantic import BaseModel, Field, IPvAnyAddress
from typing import Literal, Optional, List, Dict, Any
from datetime import datetime

class IPReputationRequest(BaseModel):
    """Request to check IP reputation"""
    ip_address: IPvAnyAddress = Field(..., description="IPv4 or IPv6 address to lookup")

class IPReputationResponse(BaseModel):
    """IP reputation lookup result"""
    ip_address: IPvAnyAddress
    reputation: Literal["malicious", "suspicious", "benign", "unknown"] = Field(
        ..., 
        description="Overall reputation classification"
    )
    threat_score: int = Field(..., ge=0, le=100, description="Threat score (0=benign, 100=highly malicious)")
    category: str = Field(..., description="Classification category (e.g., brute_force, isp, tor_exit)")
    details: str = Field(..., description="Human-readable explanation")
    first_seen: Optional[datetime] = Field(None, description="When this IP was first observed")
    last_seen: Optional[datetime] = Field(None, description="Most recent activity")
    associated_threats: List[str] = Field(default_factory=list, description="List of malware families or attack types")
    geolocation: Optional[Dict[str, Any]] = Field(None, description="Country, city, ISP data")
    source: str = Field("mock_db", description="Source of intelligence (abuseipdb, virustotal, mock)")