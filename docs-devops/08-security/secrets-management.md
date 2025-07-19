# Secrets Management

This document describes how secrets are managed in the Nano DevOps Platform.

## Overview

Secrets (passwords, API keys, tokens) are managed using Docker secrets, which provides secure storage and access without exposing secrets in code or environment variables.

## Current Implementation

### Docker Secrets

Secrets are defined in `docker-compose.yml` and stored as files in the `./secrets/` directory:

```yaml
secrets:
  postgres_password:
    external: false
    file: ./secrets/postgres_password.txt
  grafana_password:
    external: false
    file: ./secrets/grafana_password.txt
```

### Secrets Storage

**Repository Location**: `project_devops/platform/secrets/`
**Runtime Location**: `/opt/platform/secrets/`

**Important**: The `secrets/` directory is gitignored (see `.gitignore`). Secrets are **never committed to Git**.

### Secrets Access

Services access secrets via Docker secrets mount point: `/run/secrets/<secret_name>`

**Example** (PostgreSQL password):
```python
def get_db_password():
    password_file = os.getenv('POSTGRES_PASSWORD_FILE', '/run/secrets/postgres_password')
    if os.path.exists(password_file):
        with open(password_file, 'r') as f:
            return f.read().strip()
    return os.getenv('POSTGRES_PASSWORD', 'platform_password')
```

## Secrets List

### Current Secrets

1. **postgres_password**
   - Used by: PostgreSQL container, data-api, user-api
   - Purpose: PostgreSQL database authentication
   - Location: `/run/secrets/postgres_password`

2. **grafana_password**
   - Used by: Grafana container
   - Purpose: Grafana admin password
   - Location: `/run/secrets/grafana_password`

## Secrets Generation

### Creating Secrets

Secrets must be created on the runtime VM before deployment:

```bash
# Create secrets directory
mkdir -p /opt/platform/secrets

# Generate PostgreSQL password (strong, random)
openssl rand -base64 32 > /opt/platform/secrets/postgres_password.txt
chmod 600 /opt/platform/secrets/postgres_password.txt

# Generate Grafana password (strong, random)
openssl rand -base64 32 > /opt/platform/secrets/grafana_password.txt
chmod 600 /opt/platform/secrets/grafana_password.txt
```

### Password Requirements

- **Minimum Length**: 32 characters
- **Character Set**: Base64 (alphanumeric + special characters)
- **Entropy**: High (use cryptographically secure random generation)
- **Storage**: File permissions: 600 (owner read/write only)

## Secrets Rotation

### Rotation Procedure

1. **Generate New Secret**:
   ```bash
   openssl rand -base64 32 > /opt/platform/secrets/postgres_password.txt.new
   chmod 600 /opt/platform/secrets/postgres_password.txt.new
   ```

2. **Update Service Configuration**:
   - Update PostgreSQL container with new password
   - Update application services that use the secret
   - Use rolling deployment to avoid downtime

3. **Verify Service Health**:
   - Check service health endpoints
   - Verify database connectivity
   - Monitor for errors

4. **Replace Old Secret**:
   ```bash
   mv /opt/platform/secrets/postgres_password.txt.new /opt/platform/secrets/postgres_password.txt
   ```

5. **Restart Services** (if needed):
   ```bash
   docker compose -f /opt/platform/docker-compose.yml restart <service>
   ```

### Rotation Schedule

- **PostgreSQL Password**: Every 90 days (or after security incident)
- **Grafana Password**: Every 180 days (or after security incident)
- **Application Secrets**: Per application security policy

## Security Best Practices

### ✅ DO

- ✅ Use Docker secrets for all sensitive data
- ✅ Generate secrets using cryptographically secure random generators
- ✅ Store secrets in gitignored directory
- ✅ Set file permissions to 600 (owner read/write only)
- ✅ Rotate secrets regularly
- ✅ Use different secrets for different services
- ✅ Monitor secret access (via audit logs)

### ❌ DON'T

- ❌ Commit secrets to Git
- ❌ Hardcode secrets in code
- ❌ Share secrets via email or chat
- ❌ Use weak or predictable passwords
- ❌ Store secrets in environment variables (unless necessary)
- ❌ Log secrets in application logs
- ❌ Expose secrets in error messages

## Secrets in CI/CD

### Secret Detection

The CI pipeline includes secret detection:

- **Gitleaks**: Scans git history for secrets
- **Platform Law Checks**: Basic secret detection in code
- **Semgrep**: Security audit patterns

### CI/CD Best Practices

- Secrets are **never** stored in CI/CD variables
- Secrets are **never** passed via build arguments
- Secrets are **only** available at runtime on the VM

## Troubleshooting

### Secret File Not Found

**Error**: `FileNotFoundError: [Errno 2] No such file or directory: '/run/secrets/postgres_password'`

**Solution**:
1. Verify secret file exists: `ls -la /opt/platform/secrets/`
2. Verify docker-compose.yml secrets configuration
3. Check container logs: `docker logs <container-name>`

### Permission Denied

**Error**: `PermissionError: [Errno 13] Permission denied: '/run/secrets/postgres_password'`

**Solution**:
1. Check file permissions: `ls -la /opt/platform/secrets/`
2. Ensure secrets directory has correct permissions: `chmod 600 /opt/platform/secrets/*`

### Secret Not Mounted

**Error**: Service cannot access secret

**Solution**:
1. Verify service has `secrets:` section in docker-compose.yml
2. Verify secret name matches in secrets definition
3. Restart service: `docker compose restart <service>`

## Future Enhancements

### Potential Improvements

1. **External Secret Management**: Integrate with HashiCorp Vault or AWS Secrets Manager
2. **Automatic Rotation**: Implement automatic secret rotation
3. **Secret Encryption**: Encrypt secrets at rest
4. **Audit Logging**: Enhanced secret access logging
5. **Secret Versioning**: Track secret versions and changes

### Constraints

- Single-node platform limits external secret management options
- Docker secrets provide adequate security for current scale
- External secret managers add complexity and resource overhead

## References

- [Docker Secrets Documentation](https://docs.docker.com/engine/swarm/secrets/)
- [OWASP Secrets Management](https://owasp.org/www-community/vulnerabilities/Use_of_hard-coded_cryptographic_key)
- Platform Security Baseline: `security-baseline.md`
