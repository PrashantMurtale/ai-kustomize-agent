"""
Cluster Scanner - Scans live Kubernetes cluster for resources.
"""

import logging
from typing import Dict, List, Optional, Any

from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)


class ClusterScanner:
    """Scans a live Kubernetes cluster for resources."""
    
    def __init__(
        self,
        kubeconfig: Optional[str] = None,
        context: Optional[str] = None,
        api_server: Optional[str] = None,
        token: Optional[str] = None
    ):
        self._load_config(kubeconfig, context, api_server, token)
        
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.networking_v1 = client.NetworkingV1Api()
    
    def _load_config(
        self,
        kubeconfig: Optional[str],
        context: Optional[str],
        api_server: Optional[str],
        token: Optional[str]
    ):
        """Load Kubernetes configuration."""
        try:
            if api_server and token:
                # Token-based auth
                configuration = client.Configuration()
                configuration.host = api_server
                configuration.api_key = {"authorization": f"Bearer {token}"}
                configuration.verify_ssl = False
                client.Configuration.set_default(configuration)
                logger.info(f"Connected to {api_server} with token auth")
            else:
                try:
                    # Try in-cluster config first
                    config.load_incluster_config()
                    logger.info("Loaded in-cluster config")
                except config.ConfigException:
                    # Fall back to kubeconfig
                    config.load_kube_config(
                        config_file=kubeconfig,
                        context=context
                    )
                    logger.info(f"Loaded kubeconfig (context: {context or 'default'})")
                    
        except Exception as e:
            logger.error(f"Failed to load Kubernetes config: {e}")
            raise
    
    def scan(
        self,
        resource_type: str = "deployments",
        namespace: Optional[str] = None,
        labels: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Scan cluster for resources.
        
        Args:
            resource_type: Type of resource to scan
            namespace: Specific namespace or None for all
            labels: Label selector (e.g., "app=web")
        
        Returns:
            List of resource dictionaries
        """
        resources = []
        
        try:
            if resource_type in ["deployments", "deployment", "deploy"]:
                resources = self._get_deployments(namespace, labels)
            
            elif resource_type in ["services", "service", "svc"]:
                resources = self._get_services(namespace, labels)
            
            elif resource_type in ["pods", "pod", "po"]:
                resources = self._get_pods(namespace, labels)
            
            elif resource_type in ["configmaps", "configmap", "cm"]:
                resources = self._get_configmaps(namespace, labels)
            
            elif resource_type == "all":
                resources = (
                    self._get_deployments(namespace, labels) +
                    self._get_services(namespace, labels) +
                    self._get_pods(namespace, labels)
                )
            
            else:
                logger.warning(f"Unknown resource type: {resource_type}")
        
        except ApiException as e:
            logger.error(f"API error scanning {resource_type}: {e}")
        
        return resources
    
    def _get_deployments(self, namespace: Optional[str], labels: Optional[str]) -> List[Dict]:
        """Get deployments."""
        if namespace:
            result = self.apps_v1.list_namespaced_deployment(
                namespace=namespace,
                label_selector=labels
            )
        else:
            result = self.apps_v1.list_deployment_for_all_namespaces(
                label_selector=labels
            )
        
        resources = []
        for item in result.items:
            d = self._to_dict(item)
            d["kind"] = "Deployment"
            d["apiVersion"] = "apps/v1"
            resources.append(d)
        return resources
    
    def _get_services(self, namespace: Optional[str], labels: Optional[str]) -> List[Dict]:
        """Get services."""
        if namespace:
            result = self.core_v1.list_namespaced_service(
                namespace=namespace,
                label_selector=labels
            )
        else:
            result = self.core_v1.list_service_for_all_namespaces(
                label_selector=labels
            )
        
        resources = []
        for item in result.items:
            d = self._to_dict(item)
            d["kind"] = "Service"
            d["apiVersion"] = "v1"
            resources.append(d)
        return resources
    
    def _get_pods(self, namespace: Optional[str], labels: Optional[str]) -> List[Dict]:
        """Get pods."""
        if namespace:
            result = self.core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=labels
            )
        else:
            result = self.core_v1.list_pod_for_all_namespaces(
                label_selector=labels
            )
        
        resources = []
        for item in result.items:
            d = self._to_dict(item)
            d["kind"] = "Pod"
            d["apiVersion"] = "v1"
            resources.append(d)
        return resources
    
    def _get_configmaps(self, namespace: Optional[str], labels: Optional[str]) -> List[Dict]:
        """Get configmaps."""
        if namespace:
            result = self.core_v1.list_namespaced_config_map(
                namespace=namespace,
                label_selector=labels
            )
        else:
            result = self.core_v1.list_config_map_for_all_namespaces(
                label_selector=labels
            )
        
        resources = []
        for item in result.items:
            d = self._to_dict(item)
            d["kind"] = "ConfigMap"
            d["apiVersion"] = "v1"
            resources.append(d)
        return resources
    
    def _to_dict(self, k8s_object) -> Dict:
        """Convert Kubernetes object to dictionary."""
        return client.ApiClient().sanitize_for_serialization(k8s_object)
    
    def apply_patch(self, patch: Dict) -> bool:
        """
        Apply a patch to the cluster.
        
        Args:
            patch: Patch dictionary with kind, namespace, name, and patch data
        
        Returns:
            True if successful
        """
        kind = patch.get("kind")
        name = patch["patch"]["metadata"]["name"]
        namespace = patch.get("namespace", "default")
        patch_body = patch["patch"]
        
        try:
            if kind == "Deployment":
                self.apps_v1.patch_namespaced_deployment(
                    name=name,
                    namespace=namespace,
                    body=patch_body
                )
            elif kind == "Service":
                self.core_v1.patch_namespaced_service(
                    name=name,
                    namespace=namespace,
                    body=patch_body
                )
            elif kind == "Pod":
                self.core_v1.patch_namespaced_pod(
                    name=name,
                    namespace=namespace,
                    body=patch_body
                )
            elif kind == "ConfigMap":
                self.core_v1.patch_namespaced_config_map(
                    name=name,
                    namespace=namespace,
                    body=patch_body
                )
            else:
                logger.warning(f"Cannot apply patch for kind: {kind}")
                return False
            
            return True
            
        except ApiException as e:
            logger.error(f"Failed to apply patch: {e}")
            return False
