#!/usr/bin/env python3
"""Simple test for Azure OpenAI - no emojis for Windows compatibility."""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, 'src')

print("=" * 60)
print("Testing Azure OpenAI Integration")
print("=" * 60)

# Check config
api_key = os.getenv("AZURE_OPENAI_API_KEY")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

print(f"\nConfiguration:")
print(f"  API Key: {'SET' if api_key else 'MISSING'}")
print(f"  Endpoint: {'SET' if endpoint else 'MISSING'}")
print(f"  Deployment: {deployment}")

if not api_key or not endpoint:
    print("\n[ERROR] Missing credentials. Update .env file.")
    sys.exit(1)

# Test IntentParser
print("\nInitializing IntentParser...")

try:
    from agents.intent_parser import IntentParser
    parser = IntentParser()
    
    if not parser.enabled:
        print("[ERROR] Parser not enabled")
        sys.exit(1)
    
    print(f"  Provider: {parser.provider}")
    print("  [OK] Parser initialized")
    
    # Test AI parsing
    test_request = "Add memory limit 512Mi to all deployments in staging"
    print(f"\nTest request: \"{test_request}\"")
    print("Calling Azure OpenAI...")
    
    result = parser.parse(test_request)
    
    if result.get("error"):
        print(f"[ERROR] {result['error']}")
        sys.exit(1)
    
    print("\n[SUCCESS] Azure OpenAI Response:")
    print(f"  Action: {result.get('action')}")
    print(f"  Resource: {result.get('resource_type')}")
    print(f"  Field: {result.get('target_field')}")
    print(f"  Value: {result.get('value')}")
    print(f"  Namespace: {result.get('namespace')}")
    
    print("\n" + "=" * 60)
    print("[PASS] Azure OpenAI integration working!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
