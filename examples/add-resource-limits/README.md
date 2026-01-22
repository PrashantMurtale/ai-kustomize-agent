# Example: Add Resource Limits

This example shows how to add memory and CPU limits to all deployments.

## Command

```bash
ai-kustomize "Add memory limit 512Mi and CPU limit 500m to all deployments in staging"
```

## Generated Kustomization

```yaml
# kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

patches:
  - path: patches/deployment-api.yaml
  - path: patches/deployment-web.yaml
  - path: patches/deployment-worker.yaml
```

## Generated Patch Example

```yaml
# patches/deployment-api.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: staging
spec:
  template:
    spec:
      containers:
        - name: api
          resources:
            limits:
              memory: "512Mi"
              cpu: "500m"
            requests:
              memory: "256Mi"
              cpu: "250m"
```

## Apply

```bash
kubectl apply -k output/
```
