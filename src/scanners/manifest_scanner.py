"""
Manifest Scanner - Scans local YAML manifest files.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

import yaml

logger = logging.getLogger(__name__)


class ManifestScanner:
    """Scans local YAML manifest files for resources."""
    
    def __init__(self, path: str):
        self.path = Path(path)
        
        if not self.path.exists():
            raise ValueError(f"Path does not exist: {path}")
    
    def scan(
        self,
        resource_type: str = "deployments",
        namespace: Optional[str] = None,
        labels: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Scan manifest files for resources.
        
        Args:
            resource_type: Type of resource to scan
            namespace: Filter by namespace
            labels: Label selector (e.g., "app=web")
        
        Returns:
            List of resource dictionaries
        """
        all_resources = self._load_all_manifests()
        
        # Filter by type
        kind_map = {
            "deployments": "Deployment",
            "deployment": "Deployment",
            "deploy": "Deployment",
            "services": "Service",
            "service": "Service",
            "svc": "Service",
            "pods": "Pod",
            "pod": "Pod",
            "po": "Pod",
            "configmaps": "ConfigMap",
            "configmap": "ConfigMap",
            "cm": "ConfigMap",
        }
        
        if resource_type != "all":
            target_kind = kind_map.get(resource_type, resource_type)
            all_resources = [r for r in all_resources if r.get("kind") == target_kind]
        
        # Filter by namespace
        if namespace:
            all_resources = [
                r for r in all_resources 
                if r.get("metadata", {}).get("namespace") == namespace
            ]
        
        # Filter by labels
        if labels:
            label_filters = self._parse_labels(labels)
            all_resources = [
                r for r in all_resources
                if self._matches_labels(r, label_filters)
            ]
        
        return all_resources
    
    def _load_all_manifests(self) -> List[Dict]:
        """Load all YAML manifests from path."""
        resources = []
        
        if self.path.is_file():
            resources.extend(self._load_file(self.path))
        else:
            # Recursively find all YAML files
            for ext in ["*.yaml", "*.yml"]:
                for file_path in self.path.rglob(ext):
                    resources.extend(self._load_file(file_path))
        
        return resources
    
    def _load_file(self, file_path: Path) -> List[Dict]:
        """Load resources from a single YAML file."""
        resources = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Handle multi-document YAML
            for doc in yaml.safe_load_all(content):
                if doc and isinstance(doc, dict):
                    # Add source file reference
                    if "metadata" not in doc:
                        doc["metadata"] = {}
                    doc["metadata"]["_source_file"] = str(file_path)
                    
                    resources.append(doc)
                    
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
        
        return resources
    
    def _parse_labels(self, labels: str) -> Dict[str, str]:
        """Parse label selector string."""
        result = {}
        
        for pair in labels.split(","):
            if "=" in pair:
                key, value = pair.split("=", 1)
                result[key.strip()] = value.strip()
        
        return result
    
    def _matches_labels(self, resource: Dict, filters: Dict[str, str]) -> bool:
        """Check if resource matches label filters."""
        resource_labels = resource.get("metadata", {}).get("labels", {})
        
        for key, value in filters.items():
            if resource_labels.get(key) != value:
                return False
        
        return True
    
    def apply_patch(self, patch: Dict) -> bool:
        """
        In file mode, patches are exported, not applied.
        This is a no-op placeholder.
        """
        logger.warning("Cannot apply patches in file mode. Use --export instead.")
        return False
