#!/usr/bin/env python3
"""Debug Azure OpenAI response."""
import sys
import os
import json
sys.path.insert(0, '/app/src')

from openai import AzureOpenAI

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

print(f"Deployment: {deployment_name}")
print(f"Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")

response = client.chat.completions.create(
    model=deployment_name,
    messages=[
        {"role": "system", "content": "You are a Kubernetes expert. Return only valid JSON."},
        {"role": "user", "content": """Parse this request into JSON:
REQUEST: "Add memory limit 512Mi to all deployments"

Return JSON with this structure:
{
    "action": "add",
    "resource_type": "deployments",
    "target_field": "resources.limits.memory",
    "value": "512Mi",
    "namespace": null
}

Return ONLY the JSON, nothing else."""}
    ],
    temperature=0.1,
    max_tokens=500
)

print("\nResponse type:", type(response))
print("Choices type:", type(response.choices))
print("Choices length:", len(response.choices))
print("\nFirst choice:", response.choices[0])
print("\nMessage content:", response.choices[0].message.content)

content = response.choices[0].message.content
print("\n--- Parsing JSON ---")
intent = json.loads(content.strip())
print(json.dumps(intent, indent=2))
