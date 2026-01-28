#!/usr/bin/env python3
"""Test scanner in cluster."""
import sys
sys.path.insert(0, '/app/src')

from scanners.cluster_scanner import ClusterScanner

scanner = ClusterScanner()
result = scanner.scan('deployments', 'dev')
print(f'Found {len(result)} deployments in dev namespace:')
for r in result:
    print(f'  - {r["metadata"]["name"]}')
