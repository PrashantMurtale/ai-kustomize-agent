#!/usr/bin/env python3
"""Test intent parser."""
import sys
import json
sys.path.insert(0, '/app/src')

from agents.intent_parser import IntentParser

parser = IntentParser()
result = parser.parse('Add memory limit 512Mi to all deployments')
print("Intent Parser Result:")
print(json.dumps(result, indent=2))
