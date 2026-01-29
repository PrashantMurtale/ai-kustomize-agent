"""
Intent Parser - Uses AI to understand user requests.
Supports both Google Gemini and Azure OpenAI.
"""

import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Determine AI provider
AI_PROVIDER = os.getenv("AI_PROVIDER", "azure").lower()


class IntentParser:
    """Parses natural language into structured modification intents."""
    
    def __init__(self):
        self.enabled = False
        self.provider = AI_PROVIDER
        
        if self.provider == "azure":
            self._init_azure_openai()
        elif self.provider == "gemini":
            self._init_gemini()
        else:
            logger.warning(f"Unknown AI provider: {self.provider}. Using fallback parsing.")
    
    def _init_azure_openai(self):
        """Initialize Azure OpenAI client."""
        try:
            from openai import AzureOpenAI
            
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
            
            if api_key and endpoint:
                self.client = AzureOpenAI(
                    api_key=api_key,
                    api_version=api_version,
                    azure_endpoint=endpoint
                )
                self.deployment_name = deployment
                self.enabled = True
                logger.info(f"Azure OpenAI initialized with deployment: {deployment}")
            else:
                logger.warning("Azure OpenAI disabled - missing AZURE_OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT")
                
        except ImportError:
            logger.error("openai package not installed. Run: pip install openai")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI: {e}")
    
    def _init_gemini(self):
        """Initialize Google Gemini client."""
        try:
            import google.generativeai as genai
            
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.genai = genai
                self.enabled = True
                logger.info("Gemini AI initialized")
            else:
                logger.warning("Gemini disabled - no GEMINI_API_KEY")
                
        except ImportError:
            logger.error("google-generativeai package not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
    
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
            
            if self.provider == "azure":
                return self._parse_with_azure(prompt)
            elif self.provider == "gemini":
                return self._parse_with_gemini(prompt)
            else:
                return self._fallback_parse(request)
            
        except Exception as e:
            logger.error(f"AI parsing failed: {e}")
            return {"error": str(e)}
    
    def _parse_with_azure(self, prompt: str) -> Dict[str, Any]:
        """Parse using Azure OpenAI."""
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a Kubernetes expert. Your task is to parse user requests into SPECIFIC structured JSON intents for Kustomize patch generation. \nCRITICAL: DO NOT return a Kubernetes manifest. DO NOT return markdown. Return a JSON object with a list of one or more intent objects."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        return self._parse_response(response.choices[0].message.content)
    
    def _parse_with_gemini(self, prompt: str) -> Dict[str, Any]:
        """Parse using Google Gemini."""
        response = self.model.generate_content(
            prompt,
            generation_config=self.genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=1000,
            )
        )
        
        return self._parse_response(response.text)
    
    def _build_prompt(self, request: str) -> str:
        return f"""Parse this natural language request into one or more structured modification intent objects.
If the request involves multiple changes (e.g. \"add label AND set memory\"), provide multiple intent objects.

REQUEST: "{request}"

Output JSON with this exact structure:
{{
    "intents": [
        {{
            "action": "add|update|remove|set",
            "resource_type": "deployments|pods|services|configmaps|all",
            "target_field": "resources.limits.memory|resources.limits.cpu|image|labels|annotations|securityContext|...",
            "value": "the value to set (can be a string or a detailed object/dict)",
            "namespace": "namespace name or null for all",
            "label_selector": "app=web or null for all",
            "conditions": {{
                "only_if_missing": true/false,
                "container_name": "specific container or null"
            }},
            "description": "Human readable description of what will be changed"
        }}
    ]
}}

Examples:
- \"Add memory limit 512Mi to all deployments\" ->
  {{
    \"intents\": [
      {{\"action\": \"add\", \"resource_type\": \"deployments\", \"target_field\": \"resources.limits.memory\", \"value\": \"512Mi\"}}
    ]
  }}

- \"Scale deployments to 3 and update nginx image to v1.2\" ->
  {{
    \"intents\": [
      {{\"action\": \"set\", \"resource_type\": \"deployments\", \"target_field\": \"replicas\", \"value\": 3}},
      {{\"action\": \"update\", \"resource_type\": \"deployments\", \"target_field\": \"image\", \"value\": \"nginx:v1.2\"}}
    ]
  }}

Return ONLY valid JSON intent object. 
CRITICAL: DO NOT RETURN A KUBERNETES MANIFEST. RETURN ONLY THE STRUCTURED INTENT JSON ABOVE.
"""

    def _parse_response(self, text: str) -> Dict[str, Any]:
        """Parse AI response into structured intent."""
        import re
        import json
        
        try:
            # Clean up response
            text = text.strip()
            
            # Remove markdown markers if present
            text = re.sub(r"```(?:json)?", "", text)
            text = text.replace("```", "").strip()
            
            # Find the first '{' to start decoding
            start_idx = text.find('{')
            if start_idx == -1:
                return {"error": "No JSON object found in response", "raw": text}
            
            # We'll try to find a valid JSON object starting from each '{'
            decoder = json.JSONDecoder()
            data = None
            
            for i in range(len(text)):
                if text[i] == '{':
                    try:
                        segment = text[i:]
                        segment = re.sub(r',\s*([\]\}])', r'\1', segment)
                        
                        obj, end_pos = decoder.raw_decode(segment)
                        if isinstance(obj, dict):
                            data = obj
                            break
                    except (json.JSONDecodeError, ValueError):
                        continue
            
            if not data:
                return {"error": "Could not extract valid JSON from AI response", "raw": text}
            
            # Normalize to include "intents" list
            intents = []
            if "intents" in data and isinstance(data["intents"], list):
                intents = data["intents"]
            elif "action" in data:
                # Single intent returned at top level
                intents = [data]
            elif isinstance(data, list):
                # List of intents returned at top level
                intents = data
            else:
                return {"error": "Invalid JSON structure: missing 'intents' or intent fields", "raw": text}

            # Validate each intent
            required = ["action", "resource_type", "target_field"]
            for intent in intents:
                for field in required:
                    if field not in intent:
                        intent[field] = "unknown"
            
            return {"intents": intents}
            
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to parse AI response: {e} - Raw text: {text[:200]}")
            return {"error": f"Invalid JSON response from AI: {e}", "raw": text[:200]}
    
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
