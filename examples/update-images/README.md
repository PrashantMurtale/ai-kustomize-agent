# Example: Update Container Images

This example shows how to update all container images to use a private registry.

## Command

```bash
ai-kustomize "Update all images from docker.io to ecr.aws/mycompany"
```

## Use Case

You're migrating from Docker Hub to AWS ECR. Instead of manually updating every deployment, use this agent.

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
      containers:
        - name: api
          image: ecr.aws/mycompany/api:v1.2.3
```

## Alternative: Use Kustomize Image Transformer

The agent can also generate a `kustomization.yaml` with image transformers:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

images:
  - name: docker.io/myapp/api
    newName: ecr.aws/mycompany/api
  - name: docker.io/myapp/web
    newName: ecr.aws/mycompany/web
```

## Apply

```bash
kubectl apply -k output/
```
