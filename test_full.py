#!/usr/bin/env python3
"""Full end-to-end test."""
import sys
import json
sys.path.insert(0, '/app/src')

from agents.intent_parser import IntentParser
from agents.patch_generator import PatchGenerator
from scanners.cluster_scanner import ClusterScanner

# Initialize
parser = IntentParser()
generator = PatchGenerator()
scanner = ClusterScanner()

# Parse intent
print("Step 1: Parsing intent...")
intent = parser.parse('Add memory limit 512Mi and CPU limit 500m to all deployments in dev')
print(f"Intent: {json.dumps(intent, indent=2)}")

# Scan resources
print("\nStep 2: Scanning resources...")
resources = scanner.scan('deployments', 'dev')
print(f"Found {len(resources)} resources")
for r in resources:
    print(f"  - {r['metadata']['name']}")

# Generate patches
print("\nStep 3: Generating patches...")
patches = generator.generate(intent, resources)
print(f"Generated {len(patches)} patches")

for p in patches:
    print(f"\n--- Patch for {p['name']} ---")
    print(p['yaml'])
