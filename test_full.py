#!/usr/bin/env python3
"""Full end-to-end test with better error handling."""
import sys
import json
import traceback
sys.path.insert(0, '/app/src')

# Test 1: Import test
print("=== Test 1: Import Check ===")
try:
    from agents.intent_parser import IntentParser
    from agents.patch_generator import PatchGenerator
    from scanners.cluster_scanner import ClusterScanner
    print("OK: All imports successful")
except Exception as e:
    print(f"FAIL: Import error: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 2: Parser test
print("\n=== Test 2: Intent Parser ===")
try:
    parser = IntentParser()
    print(f"Provider: {parser.provider}")
    print(f"Enabled: {parser.enabled}")
    
    intent = parser.parse('Add memory limit 512Mi to all deployments')
    print(f"Intent: {json.dumps(intent, indent=2)}")
    
    if 'error' in intent:
        print(f"FAIL: Parser returned error")
    else:
        print("OK: Intent parsed successfully")
except Exception as e:
    print(f"FAIL: Parser error: {e}")
    traceback.print_exc()

# Test 3: Scanner test
print("\n=== Test 3: Cluster Scanner ===")
try:
    scanner = ClusterScanner()
    resources = scanner.scan('deployments', 'dev')
    print(f"Found {len(resources)} resources in dev namespace")
    for r in resources:
        print(f"  - {r['metadata']['name']}")
    print("OK: Scanner working")
except Exception as e:
    print(f"FAIL: Scanner error: {e}")
    traceback.print_exc()

# Test 4: Patch generator test
print("\n=== Test 4: Patch Generator ===")
try:
    generator = PatchGenerator()
    
    # Create a simple test intent
    test_intent = {
        "action": "add",
        "resource_type": "deployments",
        "target_field": "resources.limits",
        "value": {"memory": "512Mi", "cpu": "500m"},
        "namespace": "dev"
    }
    
    if resources:
        patches = generator.generate(test_intent, resources)
        print(f"Generated {len(patches)} patches")
        
        for p in patches:
            print(f"\n--- Patch: {p['name']} ---")
            print(p['yaml'][:500])
        
        if patches:
            print("OK: Patches generated successfully")
        else:
            print("WARN: No patches generated")
    else:
        print("SKIP: No resources to patch")
except Exception as e:
    print(f"FAIL: Patch generator error: {e}")
    traceback.print_exc()

print("\n=== Done ===")
