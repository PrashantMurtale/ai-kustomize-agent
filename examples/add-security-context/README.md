# Example: Add Security Context

This example shows how to add security context to all pods for improved security.

## Command

```bash
ai-kustomize "Add runAsNonRoot and readOnlyRootFilesystem to all deployments"
```

## Why This Matters

Security best practices require:
- Containers should not run as root
- Filesystem should be read-only when possible
- Privilege escalation should be disabled

## Generated Patch Example

```yaml
# patches/deployment-api.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: default
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
        - name: api
          securityContext:
            readOnlyRootFilesystem: true
            allowPrivilegeEscalation: false
```

## Apply

```bash
kubectl apply -k output/
```
