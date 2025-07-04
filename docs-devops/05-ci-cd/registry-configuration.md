# Container Image Registry Configuration

## Registry Choice

**GitHub Container Registry (ghcr.io)** is used as the container image registry for the Nano DevOps Platform.

### Rationale

- **Integrated with GitHub**: Native integration with GitHub Actions and repositories
- **No additional infrastructure**: No need to set up or maintain a separate registry service
- **Resource-efficient**: Fits the 6GB single-node constraint (no self-hosted registry overhead)
- **GitOps-aligned**: Images are versioned alongside code in the same repository ecosystem
- **Free for public repos**: No additional cost for public repositories

## Image Naming Convention

Images are tagged using the following pattern:

```
ghcr.io/{repository-owner}/{repository-name}:{tag}
```

### Tagging Strategy

- **Commit SHA**: `ghcr.io/{owner}/{repo}:{sha}` - Immutable, versioned images per commit
- **Latest**: `ghcr.io/{owner}/{repo}:latest` - Points to the latest successful build on main branch

### Example

For repository `owner/nano-project-devops`:
- Commit SHA tag: `ghcr.io/owner/nano-project-devops:abc123def456`
- Latest tag: `ghcr.io/owner/nano-project-devops:latest`

## CI/CD Integration

### CI Pipeline

The CI pipeline (`/.github/workflows/ci.yml`) automatically:
1. Builds Docker images during the `build` stage (without pushing)
2. Pushes images to ghcr.io during the `package` stage (only on push to main)
3. Tags images with both commit SHA and `latest` (on main branch)

### Registry Authentication

GitHub Actions automatically authenticates using `GITHUB_TOKEN` secret:
- No additional secrets required
- Automatic token management
- Secure and GitOps-compliant

## Deployment Integration

### Docker Compose Configuration

When services are added, docker-compose.yml should reference registry images:

```yaml
services:
  my-service:
    image: ghcr.io/{owner}/{repo}:${IMAGE_TAG:-latest}
    # ... other configuration
```

### Environment Variables

Deployment scripts use the following environment variables:
- `REGISTRY`: Registry hostname (default: `ghcr.io`)
- `IMAGE_NAME`: Full image name including registry (e.g., `ghcr.io/owner/repo`)
- `IMAGE_TAG`: Image tag to deploy (default: `latest`)

### Deployment Scripts

- `project_devops/scripts/deploy.sh`: Pulls images from registry and deploys
- `project_devops/scripts/rollback.sh`: Re-deploys previous image tag from registry

## Rollback Strategy

Rollback is performed by:
1. Identifying the previous image tag (from Git history or deployment logs)
2. Using `rollback.sh` with `PREVIOUS_IMAGE_TAG` environment variable
3. Script pulls and re-deploys the previous image from registry

## Future Considerations

- **Private repositories**: May require additional authentication configuration
- **Multi-registry support**: Can be extended to support multiple registries if needed
- **Image retention**: GitHub Container Registry retention policies should be configured
- **Registry mirroring**: Can add mirror registries for redundancy if needed
