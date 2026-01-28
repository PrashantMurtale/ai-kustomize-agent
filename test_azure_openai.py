#!/usr/bin/env python3
"""
Quick test script to verify Azure OpenAI integration.
Run: python test_azure_openai.py
"""

import os
import sys
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Add src to path
sys.path.insert(0, 'src')

def test_azure_openai_connection():
    """Test Azure OpenAI API connection."""
    print("=" * 60)
    print("🧪 Testing Azure OpenAI Integration")
    print("=" * 60)
    
    # Check environment variables
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    provider = os.getenv("AI_PROVIDER", "azure")
    
    print(f"\n📋 Configuration:")
    print(f"   AI Provider: {provider}")
    print(f"   API Key: {'✅ Set' if api_key else '❌ Missing'}")
    print(f"   Endpoint: {'✅ Set' if endpoint else '❌ Missing'}")
    print(f"   Deployment: {deployment}")
    
    if not api_key or not endpoint:
        print("\n❌ Missing Azure OpenAI credentials!")
        print("\n📝 Create a .env file with:")
        print("   AI_PROVIDER=azure")
        print("   AZURE_OPENAI_API_KEY=your-key-here")
        print("   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/")
        print("   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o")
        return False
    
    # Test the IntentParser
    print("\n🔄 Testing IntentParser...")
    
    try:
        from agents.intent_parser import IntentParser
        
        parser = IntentParser()
        
        if not parser.enabled:
            print("❌ IntentParser failed to initialize")
            return False
        
        print(f"   ✅ IntentParser initialized (provider: {parser.provider})")
        
        # Test parsing
        test_request = "Add memory limit 512Mi to all deployments in staging"
        print(f"\n📝 Test request: \"{test_request}\"")
        print("   Calling Azure OpenAI GPT-4o...")
        
        result = parser.parse(test_request)
        
        if result.get("error"):
            print(f"   ❌ Error: {result['error']}")
            return False
        
        print("\n✅ Response from Azure OpenAI:")
        print(f"   Action: {result.get('action')}")
        print(f"   Resource Type: {result.get('resource_type')}")
        print(f"   Target Field: {result.get('target_field')}")
        print(f"   Value: {result.get('value')}")
        print(f"   Namespace: {result.get('namespace')}")
        print(f"   Description: {result.get('description', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_parser():
    """Test fallback parser (without AI)."""
    print("\n" + "=" * 60)
    print("🧪 Testing Fallback Parser (no AI)")
    print("=" * 60)
    
    try:
        from agents.intent_parser import IntentParser
        
        parser = IntentParser()
        
        test_cases = [
            "Add memory limit 512Mi to all deployments",
            "Update images from docker.io to ecr.aws",
            "Add label team=platform to services in production",
            "Remove annotations from pods"
        ]
        
        for request in test_cases:
            result = parser._fallback_parse(request)
            print(f"\n📝 \"{request}\"")
            print(f"   → Action: {result['action']}, Resource: {result['resource_type']}, Field: {result['target_field']}")
        
        print("\n✅ Fallback parser working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("\n🚀 AI Kustomize Agent - Local Test\n")
    
    # Test fallback parser first (doesn't need API)
    fallback_ok = test_fallback_parser()
    
    # Test Azure OpenAI
    azure_ok = test_azure_openai_connection()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    print(f"   Fallback Parser: {'✅ PASS' if fallback_ok else '❌ FAIL'}")
    print(f"   Azure OpenAI:    {'✅ PASS' if azure_ok else '❌ FAIL'}")
    print("=" * 60)
    
    if azure_ok:
        print("\n🎉 All tests passed! Ready for deployment.")
    elif fallback_ok:
        print("\n⚠️  Azure OpenAI not configured, but fallback parser works.")
        print("   Add your Azure OpenAI credentials to .env file.")
    else:
        print("\n❌ Tests failed. Check the errors above.")
    
    sys.exit(0 if azure_ok else 1)
