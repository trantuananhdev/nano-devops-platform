# Network Policies and Segmentation

This document describes network architecture, policies, and segmentation strategies for the Nano DevOps Platform.

## Overview

The platform uses Docker networking to provide service isolation and secure communication between services.

## Current Network Architecture

### Single Network: platform-network

All services are connected to a single bridge network: `platform-network`

```yaml
networks:
  platform-network:
    driver: bridge
    name: platform-network
```

### Network Characteristics

- **Type**: Bridge network (default Docker network)
- **Isolation**: Services can communicate with each other by service name
- **External Access**: Only Traefik exposes ports to host (80, 443, 8080)
- **Internal Communication**: All inter-service communication is internal

## Service Network Access

### Public-Facing Services

**Traefik** (Edge Layer):
- Exposes ports: 80, 443, 8080 (dashboard)
- Routes external traffic to internal services
- Only service with direct external access

### Internal Services

All other services are **not** directly exposed to the host:

- **PostgreSQL**: Internal only (port 5432)
- **Redis**: Internal only (port 6379)
- **Prometheus**: Internal only (port 9090), accessible via Traefik
- **Grafana**: Internal only (port 3000), accessible via Traefik
- **Loki**: Internal only (port 3100), accessible via Traefik
- **Application Services**: Internal only (port 8080), accessible via Traefik

## Network Segmentation Strategy

### Current Approach: Single Network

**Rationale**:
- Single-node platform simplifies network management
- All services need to communicate with each other
- Bridge network provides adequate isolation from host
- Resource constraints favor simplicity

**Security Benefits**:
- Services not directly exposed to host network
- Internal communication isolated from external network
- Traefik acts as single entry point

### Recommended Segmentation (Future)

For enhanced security, consider network segmentation:

#### Option 1: Service Layer Networks

```yaml
networks:
  edge-network:      # Traefik only
  app-network:       # Application services
  data-network:      # PostgreSQL, Redis
  monitoring-network: # Prometheus, Grafana, Loki
```

**Benefits**:
- Better isolation between service layers
- Reduced attack surface
- Compliance with network segmentation requirements

**Trade-offs**:
- Increased complexity
- Requires service-to-service communication configuration
- More network management overhead

#### Option 2: Service-Specific Networks

Each service gets its own network with explicit connections:

```yaml
services:
  data-api:
    networks:
      - app-network
      - data-network  # Explicit connection to PostgreSQL
```

**Benefits**:
- Fine-grained control
- Explicit service dependencies
- Better security boundaries

**Trade-offs**:
- High complexity
- Difficult to manage at scale
- May not be necessary for single-node platform

## Service-to-Service Communication

### Communication Patterns

1. **HTTP/REST**: Application services communicate via HTTP
   - Example: `aggregator-api` calls `health-api` and `data-api`
   - Uses Docker service names: `http://health-api:8080`

2. **Database Connections**: Applications connect to PostgreSQL
   - Service name: `platform-postgres`
   - Port: `5432`
   - Authentication: Via Docker secrets

3. **Cache Access**: Applications connect to Redis
   - Service name: `platform-redis`
   - Port: `6379`
   - No authentication (internal network only)

### Security Considerations

- **No TLS**: Internal communication does not use TLS (internal network)
- **Service Names**: Use Docker service names (DNS resolution)
- **Ports**: Use standard ports within containers
- **Authentication**: Database connections use secrets

## Network Policies

### Ingress Policies

**Allowed**:
- HTTP/HTTPS traffic to Traefik (ports 80, 443)
- Traefik dashboard (port 8080) - should be restricted in production

**Denied**:
- Direct access to internal services from host
- Direct access to databases from external network
- Direct access to monitoring services from external network

### Egress Policies

**Allowed**:
- All outbound traffic (for updates, external APIs)
- Container-to-container communication within network

**Restrictions**:
- None currently (single-node platform)

### Inter-Service Policies

**Allowed**:
- Application services can communicate with each other
- Application services can access PostgreSQL and Redis
- Monitoring services can scrape metrics from all services

**Denied**:
- External services cannot directly access internal services
- Services cannot access other services' data volumes

## Network Security Best Practices

### ✅ DO

- ✅ Use Docker service names for service discovery
- ✅ Keep internal services on internal network only
- ✅ Use Traefik as single entry point
- ✅ Monitor network traffic (via Prometheus/Loki)
- ✅ Document service dependencies
- ✅ Use secrets for authentication

### ❌ DON'T

- ❌ Expose internal services directly to host
- ❌ Use hardcoded IP addresses
- ❌ Skip authentication for database connections
- ❌ Expose monitoring dashboards publicly without authentication
- ❌ Allow unrestricted access to Traefik dashboard

## Network Monitoring

### Metrics

Prometheus collects network metrics:
- Container network I/O
- Network errors
- Connection counts

### Logging

Loki aggregates network-related logs:
- Service connection attempts
- Network errors
- Traffic patterns

### Alerts

Consider alerts for:
- Unusual network traffic patterns
- Connection failures
- Network errors

## Troubleshooting

### Service Cannot Reach Another Service

**Symptoms**: Connection timeout, DNS resolution failure

**Diagnosis**:
1. Verify both services are on same network: `docker network inspect platform-network`
2. Check service names match: `docker ps --format '{{.Names}}'`
3. Verify service is running: `docker ps | grep <service-name>`

**Solution**:
- Ensure services are on `platform-network`
- Use exact service names from docker-compose.yml
- Check service health: `docker logs <service-name>`

### Port Already in Use

**Symptoms**: `Error: bind: address already in use`

**Solution**:
- Check for conflicting services: `netstat -tulpn | grep <port>`
- Change port mapping in docker-compose.yml
- Stop conflicting service

## Future Enhancements

### Potential Improvements

1. **Network Segmentation**: Implement multi-network architecture
2. **TLS for Internal Communication**: Add mTLS between services
3. **Network Policies**: Implement Docker network policies
4. **Traffic Encryption**: Encrypt all inter-service traffic
5. **Network Monitoring**: Enhanced network traffic analysis

### Constraints

- Single-node platform limits network segmentation benefits
- Current bridge network provides adequate isolation
- Additional network layers add complexity and overhead

## References

- [Docker Networking Documentation](https://docs.docker.com/network/)
- Platform Security Baseline: `security-baseline.md`
- Service Communication Patterns: `docs-devops/02-system-architecture/service-communication-patterns.md`
