"""
Test script for Manager Agent (Day 3)
Run: python scripts/test_investigation.py
"""

import requests
import time

BASE_URL = "http://localhost:7071/api"

# Test scenarios covering different threat levels
SCENARIOS = [
    {
        "name": "Known Malicious IP (Critical Threat)",
        "payload": {
            "alert": "Suspicious login attempts detected from 89.248.172.16",
            "priority": "high"
        },
        "expected_verdict": ["critical", "high"]
    },
    {
        "name": "Benign IP (False Positive)",
        "payload": {
            "alert": "High traffic volume detected from 8.8.8.8",
            "priority": "medium"
        },
        "expected_verdict": ["low", "info", "medium"]
    },
    {
        "name": "Unknown IP Scanning (Behavioral Detection)",
        "payload": {
            "alert": "Port scanning activity detected from 198.50.201.145",
            "priority": "medium"
        },
        "expected_verdict": ["high", "medium"]
    }
]

def test_investigation_endpoint():
    print("=" * 80)
    print("🕵️  CYDERES AEGIS SWARM - INVESTIGATION TEST SUITE")
    print("=" * 80)
    
    for i, scenario in enumerate(SCENARIOS, 1):
        print(f"\n[SCENARIO {i}] {scenario['name']}")
        print("-" * 80)
        
        start_time = time.time()
        
        try:
            # Send request to local function
            response = requests.post(
                f"{BASE_URL}/investigate",
                json=scenario['payload'],
                timeout=60  # Give agents enough time to think/execute
            )
            
            duration = round(time.time() - start_time, 2)
            
            if response.status_code == 200:
                result = response.json()
                verdict = result['verdict']
                
                print(f"✅ Success ({duration}s)")
                print(f"   Verdict: {verdict['severity'].upper()}")
                print(f"   Confidence: {verdict['confidence']}")
                print(f"   Summary: {verdict['threat_summary']}")
                
                print("\n   📋 Tasks Executed:")
                for task in result.get('tasks_history', []):
                    print(f"   - [{task['agent'].upper()}] {task['action']}")
                
                # Validation
                if verdict['severity'] in scenario['expected_verdict']:
                    print(f"\n   🎯 Result matches expectation!")
                else:
                    print(f"\n   ⚠️ Result unexpected (Expected {scenario['expected_verdict']}, got {verdict['severity']})")
                    
            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            
        print("-" * 80)

    print("\n" + "=" * 80)
    print("TEST SUITE COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_investigation_endpoint()
