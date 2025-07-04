# Environment Variables Reference

This document provides a comprehensive reference for all environment variables used in the Nano DevOps Platform CI/CD pipeline and deployment processes.

## CI/CD Pipeline Variables

### GitHub Actions Variables

These variables are automatically set by GitHub Actions:

- `GITHUB_REPOSITORY`: Repository name (e.g., `owner/repo-name`)
- `GITHUB_SHA`: Commit SHA of the current build
- `GITHUB_REF`: Git reference (branch or tag)
- `GITHUB_ACTOR`: GitHub username of the actor triggering the workflow
- `GITHUB_TOKEN`: Authentication token for GitHub API and registry

### CI Workflow Variables

Defined in `.github/workflows/ci.yml`:

```yaml
env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}
```

- `REGISTRY`: Container registry hostname (default: `ghcr.io`)
- `IMAGE_NAME`: Full repository name (automatically set from `GITHUB_REPOSITORY`)

## Deployment Script Variables

### Required Variables

These variables **must** be set before running deployment scripts:

#### `SERVICE_NAME`
- **Description**: Name of the service to deploy
- **Required**: Yes
- **Example**: `health-api`
- **Notes**: Must match the service name in `docker-compose.yml`

#### `IMAGE_NAME`
- **Description**: GitHub repository name (owner/repo-name format)
- **Required**: Yes (for registry image references)
- **Example**: `owner/nano-project-devops`
- **Notes**: Should match `GITHUB_REPOSITORY` format

#### `IMAGE_TAG`
- **Description**: Image tag to deploy (commit SHA or `latest`)
- **Required**: Yes
- **Example**: `abc123def456` or `latest`
- **Notes**: Prefer commit SHA for production deployments

### Optional Variables

These variables have defaults but can be overridden:

#### `REGISTRY`
- **Description**: Container registry hostname
- **Required**: No
- **Default**: `ghcr.io`
- **Example**: `ghcr.io`
- **Notes**: Currently only GitHub Container Registry is supported

#### `COMPOSE_FILE`
- **Description**: Path to docker-compose.yml file
- **Required**: No
- **Default**: `project_devops/platform/docker-compose.yml`
- **Example**: `project_devops/platform/docker-compose.yml`

#### `HEALTH_CHECK_TIMEOUT`
- **Description**: Health check timeout in seconds
- **Required**: No
- **Default**: `60`
- **Example**: `120`
- **Notes**: Increase for services with longer startup times

### Rollback Script Variables

#### `PREVIOUS_IMAGE_TAG`
- **Description**: Image tag of the previous version to rollback to
- **Required**: Yes (for rollback script)
- **Example**: `previous-sha-here`
- **Notes**: Must be a valid image tag that exists in the registry

## Docker Compose Variables

### Service Image References

Services in `docker-compose.yml` use environment variables for image references:

```yaml
services:
  health-api:
    image: ${REGISTRY:-ghcr.io}/${IMAGE_NAME:-owner/repo}/health-api:${IMAGE_TAG:-latest}
```

**Variables Used**:
- `REGISTRY`: Registry hostname (default: `ghcr.io`)
- `IMAGE_NAME`: Repository name (default: `owner/repo`)
- `IMAGE_TAG`: Image tag (default: `latest`)

**Note**: These defaults are placeholders. Always set `IMAGE_NAME` to your actual repository name.

## Environment Variable Setup

### For Deployment Scripts

Create a `.env` file or export variables before running scripts:

```bash
# Option 1: Export in current shell
export REGISTRY=ghcr.io
export IMAGE_NAME=owner/nano-project-devops
export IMAGE_TAG=latest
export SERVICE_NAME=health-api

# Option 2: Use .env file (if supported)
cat > .env << EOF
REGISTRY=ghcr.io
IMAGE_NAME=owner/nano-project-devops
IMAGE_TAG=latest
SERVICE_NAME=health-api
EOF

# Option 3: Set inline
REGISTRY=ghcr.io IMAGE_NAME=owner/repo IMAGE_TAG=latest SERVICE_NAME=health-api ./deploy.sh
```

### For Docker Compose

Docker Compose automatically reads `.env` file in the same directory:

```bash
# Create .env file in project_devops/platform/
cat > project_devops/platform/.env << EOF
REGISTRY=ghcr.io
IMAGE_NAME=owner/nano-project-devops
IMAGE_TAG=latest
EOF
```

Or export variables before running docker-compose:

```bash
export REGISTRY=ghcr.io
export IMAGE_NAME=owner/nano-project-devops
export IMAGE_TAG=latest
docker-compose -f project_devops/platform/docker-compose.yml up -d
```

## Variable Validation

### Check Required Variables

```bash
# Verify all required variables are set
[ -z "$SERVICE_NAME" ] && echo "ERROR: SERVICE_NAME not set" && exit 1
[ -z "$IMAGE_NAME" ] && echo "ERROR: IMAGE_NAME not set" && exit 1
[ -z "$IMAGE_TAG" ] && echo "ERROR: IMAGE_TAG not set" && exit 1

# Display current values
echo "Registry: ${REGISTRY:-ghcr.io}"
echo "Image Name: ${IMAGE_NAME:-NOT SET}"
echo "Image Tag: ${IMAGE_TAG:-NOT SET}"
echo "Service Name: ${SERVICE_NAME:-NOT SET}"
```

## Common Patterns

### Pattern 1: Deploy Latest from Main Branch

```bash
export REGISTRY=ghcr.io
export IMAGE_NAME=owner/nano-project-devops
export IMAGE_TAG=latest
export SERVICE_NAME=health-api
./project_devops/scripts/deploy.sh
```

### Pattern 2: Deploy Specific Commit SHA

```bash
export REGISTRY=ghcr.io
export IMAGE_NAME=owner/nano-project-devops
export IMAGE_TAG=$(git rev-parse HEAD)  # Current commit
export SERVICE_NAME=health-api
./project_devops/scripts/deploy.sh
```

### Pattern 3: Deploy Previous Commit

```bash
export REGISTRY=ghcr.io
export IMAGE_NAME=owner/nano-project-devops
export IMAGE_TAG=$(git rev-parse HEAD~1)  # Previous commit
export SERVICE_NAME=health-api
./project_devops/scripts/deploy.sh
```

### Pattern 4: Rollback to Previous Version

```bash
export SERVICE_NAME=health-api
export PREVIOUS_IMAGE_TAG=previous-sha-here
./project_devops/scripts/rollback.sh
```

## Security Considerations

### Secrets Management

**Never commit secrets to Git**. Use:

1. **GitHub Secrets** (for CI/CD):
   - `GITHUB_TOKEN`: Automatically provided by GitHub Actions
   - Custom secrets: Add via repository Settings → Secrets

2. **Environment Variables** (for local deployment):
   - Export in shell session (not persisted)
   - Use `.env` files (add to `.gitignore`)
   - Use secret management tools (e.g., HashiCorp Vault)

3. **Docker Secrets** (for runtime):
   - Use Docker secrets for sensitive data
   - Reference in docker-compose.yml via `secrets:` section

### Private Repository Authentication

For private GitHub Container Registry:

```bash
# Authenticate with GitHub token
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Or use personal access token
echo $PAT_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

## Troubleshooting

### Variable Not Set Error

**Error**: `SERVICE_NAME environment variable is required`

**Solution**: Export the variable before running the script:
```bash
export SERVICE_NAME=health-api
```

### Image Pull Fails

**Error**: `Failed to pull image`

**Possible Causes**:
- `IMAGE_NAME` not set correctly
- `IMAGE_TAG` doesn't exist
- Registry authentication required

**Solution**: Verify variables and authenticate:
```bash
echo "IMAGE_NAME: $IMAGE_NAME"
echo "IMAGE_TAG: $IMAGE_TAG"
docker pull ${REGISTRY}/${IMAGE_NAME}/${SERVICE_NAME}:${IMAGE_TAG}
```

### Docker Compose Uses Wrong Image

**Issue**: Service uses default `owner/repo` instead of actual repository

**Solution**: Set `IMAGE_NAME` environment variable:
```bash
export IMAGE_NAME=your-actual-owner/your-actual-repo
```

## Related Documentation

- [Deployment Runbook](../06-deployment-strategy/deployment-runbook.md) - Step-by-step deployment guide
- [Registry Configuration](registry-configuration.md) - Image registry setup
- [CD Strategy](cd-strategy.md) - Continuous deployment strategy
