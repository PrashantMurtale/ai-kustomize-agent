#!/usr/bin/env python3
"""Debug patch generator - check kind."""
import sys
import json
sys.path.insert(0, '/app/src')

from agents.patch_generator import PatchGenerator
from scanners.cluster_scanner import ClusterScanner

scanner = ClusterScanner()
resources = scanner.scan('deployments', 'dev')

print(f"Found {len(resources)} resources")
for r in resources:
    name = r.get('metadata', {}).get('name')
    kind = r.get('kind')
    print(f"\nResource Name: {name}")
    print(f"Resource Kind: {kind}")
    print(f"Available keys: {list(r.keys())}")

# Test patch generation
print("\n=== Testing Patch Generator ===")
generator = PatchGenerator()

intent = {
    "action": "add",
    "resource_type": "deployments",
    "target_field": "resources.limits",
    "value": {"memory": "512Mi", "cpu": "500m"},
    "namespace": "dev"
}

from transformers.factory import get_transformer

for r in resources:
    # Fix for missing kind in list items
    if not r.get('kind') and 'spec' in r and 'template' in r['spec']:
        r['kind'] = 'Deployment'
        print(f"Manually set kind to {r['kind']}")

    print(f"\nProcessing: {r['metadata']['name']}")
    try:
        transformer = get_transformer(r, intent)
        print(f"  Transformer: {type(transformer).__name__}")
        patch = transformer.transform()
        if patch:
            print(f"  Patch generated!")
            print(f"  JSON: {json.dumps(patch, indent=2)}")
        else:
            print(f"  No patch returned")
    except Exception as e:
        print(f"  Error: {e}")
