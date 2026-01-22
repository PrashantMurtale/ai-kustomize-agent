"""
Intent Parser - Uses AI to understand user requests.
"""

import os
import json
import logging
from typing import Dict, Any

import google.generativeai as genai

logger = logging.getLogger(__name__)

# Initialize Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)


class IntentParser:
    """Parses natural language into structured modification intents."""
    
    def __init__(self):
        if api_key:
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.enabled = True
        else:
            self.enabled = False
            logger.warning("AI disabled - no GEMINI_API_KEY")
    
    def parse(self, request: str) -> Dict[str, Any]:
        """
        Parse a natural language request into a structured intent.
        
        Args:
            request: User's natural language request
        
        Returns:
            Structured intent dictionary
        """
        if not self.enabled:
            return self._fallback_parse(request)
        
        try:
            prompt = self._build_prompt(request)
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=1000,
                )
            )
            
            return self._parse_response(response.text)
            
        except Exception as e:
            logger.error(f"AI parsing failed: {e}")
            return {"error": str(e)}
    
    def _build_prompt(self, request: str) -> str:
        return f"""You are a Kubernetes expert. Parse this natural language request into a structured modification intent.

REQUEST: "{request}"

Output JSON with this exact structure:
{{
    "action": "add|update|remove|set",
    "resource_type": "deployments|pods|services|configmaps|all",
    "target_field": "resources.limits.memory|resources.limits.cpu|image|labels|annotations|securityContext|...",
    "value": "the value to set",
    "namespace": "namespace name or null for all",
    "label_selector": "app=web or null for all",
    "conditions": {{
        "only_if_missing": true/false,
        "container_name": "specific container or null"
    }},
    "description": "Human readable description of what will be changed"
}}

Examples:
- "Add memory limit 512Mi to all deployments" ->
  {{"action": "add", "resource_type": "deployments", "target_field": "resources.limits.memory", "value": "512Mi"}}

- "Update images from docker.io to ecr.aws" ->
  {{"action": "update", "resource_type": "deployments", "target_field": "image", "value": {{"from": "docker.io", "to": "ecr.aws"}}}}

- "Add label team=platform to services" ->
  {{"action": "add", "resource_type": "services", "target_field": "labels", "value": {{"team": "platform"}}}}

Return ONLY valid JSON, no markdown.
"""

    def _parse_response(self, text: str) -> Dict[str, Any]:
        """Parse AI response into structured intent."""
        try:
            # Clean up response
            text = text.strip()
            
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            intent = json.loads(text.strip())
            
            # Validate required fields
            required = ["action", "resource_type", "target_field"]
            for field in required:
                if field not in intent:
                    intent[field] = "unknown"
            
            return intent
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            return {"error": f"Invalid JSON: {e}", "raw": text[:200]}
    
    def _fallback_parse(self, request: str) -> Dict[str, Any]:
        """Basic keyword-based parsing when AI is unavailable."""
        request_lower = request.lower()
        
        intent = {
            "action": "add",
            "resource_type": "deployments",
            "target_field": "unknown",
            "value": None,
            "namespace": None,
            "description": request
        }
        
        # Detect resource type
        if "service" in request_lower:
            intent["resource_type"] = "services"
        elif "pod" in request_lower:
            intent["resource_type"] = "pods"
        elif "configmap" in request_lower:
            intent["resource_type"] = "configmaps"
        
        # Detect action
        if "remove" in request_lower or "delete" in request_lower:
            intent["action"] = "remove"
        elif "update" in request_lower or "change" in request_lower:
            intent["action"] = "update"
        
        # Detect common targets
        if "memory" in request_lower:
            intent["target_field"] = "resources.limits.memory"
        elif "cpu" in request_lower:
            intent["target_field"] = "resources.limits.cpu"
        elif "image" in request_lower:
            intent["target_field"] = "image"
        elif "label" in request_lower:
            intent["target_field"] = "labels"
        elif "annotation" in request_lower:
            intent["target_field"] = "annotations"
        
        # Detect namespace
        if " in " in request_lower:
            parts = request_lower.split(" in ")
            if len(parts) > 1:
                ns = parts[-1].split()[0]
                if ns not in ["all", "every"]:
                    intent["namespace"] = ns
        
        return intent
