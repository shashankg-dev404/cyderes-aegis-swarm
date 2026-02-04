"""
Test script for Analyst Agent
Run: python scripts/test_analyst.py
"""

import requests
import json


BASE_URL = "http://localhost:7071/api"

TEST_QUERIES = [
    "How many total attack records are there?",
    "Which IP address has the most brute force attempts?",
    "What is the average bytes sent in data exfiltration attacks?",
    "Find all unique source IPs involved in port scanning",
    "How many SQL injection attempts were blocked vs allowed?"
]


def test_analyst_agent():
    """Test the analyst agent with various queries"""
    print("=" * 80)
    print("ANALYST AGENT TEST SUITE")
    print("=" * 80)
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n[TEST {i}] Query: {query}")
        print("-" * 80)
        
        try:
            response = requests.post(
                f"{BASE_URL}/analyze-logs",
                json={"query": query},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success!")
                print(f"Generated Code:\n{result['generated_code']}\n")
                print(f"Execution Time: {result['execution_result']['execution_time_ms']}ms")
                print(f"Answer: {result['natural_language_answer']}")
                print(f"Confidence: {result['confidence']}")
            else:
                print(f"❌ Failed: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n" + "=" * 80)
    print("TEST SUITE COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_analyst_agent()
