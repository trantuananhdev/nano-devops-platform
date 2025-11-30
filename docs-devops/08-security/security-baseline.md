# Security Baseline

This document defines the security baseline for the Nano DevOps Platform.

## Core Security Principles

1. **Non-root containers**: All containers run as non-root users
2. **Secrets management**: Secrets managed via Docker secrets, never in code
3. **Network isolation**: Internal services isolated from external network
4. **Limited exposed ports**: Only Traefik exposes ports to host
5. **Immutable deployment**: No runtime modifications, GitOps-only changes
6. **Observability**: All actions logged and monitored

## Container Security

### Non-Root Execution

- **Principle**: Containers run as non-root users when possible
- **Implementation**: Base images use non-root users
- **Exceptions**: Some system containers (cAdvisor) require privileged access

### Resource Limits

- **Memory Limits**: All services have memory limits defined
- **CPU Limits**: CPU limits prevent resource exhaustion
- **Total Constraint**: Platform respects 6GB RAM limit

### Image Security

- **Base Images**: Use official, maintained images
- **Image Scanning**: CI pipeline scans images for vulnerabilities
- **Updates**: Regularly update base images for security patches

## Secrets Management

### Current Approach

- **Docker Secrets**: Secrets stored as files, mounted into containers
- **Git Ignored**: Secrets directory never committed to Git
- **File Permissions**: Secrets files have 600 permissions (owner read/write only)
- **Rotation**: Manual rotation process documented

See `secrets-management.md` for detailed documentation.

## Network Security

### Network Isolation

- **Single Network**: All services on `platform-network` (bridge)
- **Internal Only**: Most services not exposed to host
- **Traefik Entry Point**: Single entry point for external traffic
- **No Direct Access**: Databases and internal services not directly accessible

See `network-policies.md` for detailed documentation.

### Port Exposure

**Exposed Ports**:
- Traefik: 80, 443, 8080 (dashboard)
- Prometheus: 9090 (via Traefik)
- Grafana: 3000 (via Traefik)

**Internal Only**:
- PostgreSQL: 5432
- Redis: 6379
- Application services: 8080

## Access Control

### Authentication

- **PostgreSQL**: Password authentication via Docker secrets
- **Grafana**: Admin password via Docker secrets
- **Redis**: No authentication (internal network only)
- **Application Services**: No authentication (internal network only)

### Authorization

- **Service-to-Service**: Services can communicate via Docker network
- **External Access**: Only via Traefik with appropriate routing rules
- **Monitoring**: Prometheus scrapes metrics from all services

## Security Monitoring

### Secret Detection

- **Gitleaks**: Scans git history for secrets
- **Platform Law Checks**: Basic secret detection in code
- **Semgrep**: Security audit patterns

### Vulnerability Scanning

- **CodeQL**: Static analysis for security vulnerabilities
- **Semgrep**: Security-focused SAST
- **OWASP Dependency Check**: Dependency vulnerability scanning

### Logging and Auditing

- **Application Logs**: Collected via Loki
- **Container Logs**: Available via Docker logs
- **Access Logs**: Traefik access logs

## Security Checklist

### Pre-Deployment

- [ ] All secrets generated and stored securely
- [ ] Secrets files have correct permissions (600)
- [ ] No secrets committed to Git
- [ ] Images scanned for vulnerabilities
- [ ] Resource limits configured
- [ ] Network isolation verified

### Post-Deployment

- [ ] Services running as non-root (where applicable)
- [ ] Only Traefik exposed to external network
- [ ] Secrets mounted correctly
- [ ] Monitoring and alerting configured
- [ ] Logs being collected

### Ongoing

- [ ] Regular secret rotation
- [ ] Regular image updates
- [ ] Monitor security alerts
- [ ] Review access logs
- [ ] Update security documentation

## Security Best Practices

See `security-best-practices.md` for comprehensive best practices guide.

## Compliance

### Platform Laws

- **delivery.gitops**: All changes via Git
- **infra.immutable**: No runtime modifications
- **reliability.observability**: All actions logged

### Security Standards

- **OWASP Top 10**: Addressed via secure coding practices
- **CIS Docker Benchmark**: Followed where applicable
- **Defense in Depth**: Multiple security layers

## Incident Response

### Security Incidents

1. **Identify**: Detect security issue via monitoring or alerts
2. **Contain**: Isolate affected services if needed
3. **Remediate**: Fix security issue (rotate secrets, update images)
4. **Document**: Document incident and resolution
5. **Prevent**: Update security practices to prevent recurrence

See `docs-devops/10-runbook/incident-response.md` for detailed procedures.

## References

- Secrets Management: `secrets-management.md`
- Network Policies: `network-policies.md`
- Security Best Practices: `security-best-practices.md`
- Incident Response: `docs-devops/10-runbook/incident-response.md`