# Resource Optimization Guide

This document describes how to optimize resource allocation across the Nano DevOps Platform to ensure efficient resource usage while respecting the 6GB RAM constraint.

## Overview

Resource optimization is the process of adjusting resource limits and allocations based on actual usage patterns to:
- **Maximize efficiency**: Use resources effectively without waste
- **Respect constraints**: Stay within 6GB RAM limit
- **Maintain performance**: Ensure services have adequate resources
- **Enable growth**: Optimize to allow more services within constraints

## Current Resource Allocation

### Total Budget: 6GB RAM

**Infrastructure Services**: ~3GB
- Traefik: 200MB
- PostgreSQL: 1.5GB
- Redis: 300MB
- Prometheus: 400MB
- Grafana: 300MB
- Loki: 300MB

**Application Services**: ~1.5GB
- health-api: 50MB
- data-api: 100MB
- aggregator-api: 100MB
- user-api: 100MB
- Additional services: ~1.15GB available

**Buffer/Headroom**: ~800MB
- System overhead
- Temporary spikes
- Future growth

## Resource Optimization Workflow

### 1. Pre-Optimization Analysis

Before optimizing resources, analyze current usage:

**Metrics to Collect**:
- Actual memory usage per service (P50, P95, P99)
- Peak memory usage patterns
- Average memory usage over time
- CPU usage patterns
- Resource pressure indicators

**Data Sources**:
- Prometheus metrics (container_memory_usage_bytes)
- Grafana dashboards (Infrastructure Health)
- cAdvisor metrics
- Alert history (resource alerts)

**Questions to Answer**:
- Are services using their full allocated memory?
- Are there services with unused capacity?
- Are there services hitting limits frequently?
- What are peak usage patterns?
- Where is resource pressure occurring?

### 2. Identify Optimization Opportunities

**Common Optimization Scenarios**:

1. **Over-Allocated Services**:
   - Service allocated 100MB but only uses 30MB average
   - Can reduce limit to 50MB, freeing 50MB

2. **Under-Allocated Services**:
   - Service hitting memory limit frequently
   - Needs limit increase (if budget allows)

3. **Peak Usage Patterns**:
   - Services with predictable peaks
   - Can optimize based on peak timing

4. **Resource Pressure**:
   - Total usage approaching 6GB limit
   - Need to optimize to create headroom

### 3. Analyze Usage Patterns

**Prometheus Queries**:

```promql
# Average memory usage over 7 days
avg_over_time(container_memory_usage_bytes{name!=""}[7d])

# P95 memory usage over 7 days
quantile_over_time(0.95, container_memory_usage_bytes{name!=""}[7d])

# Peak memory usage
max_over_time(container_memory_usage_bytes{name!=""}[7d])

# Memory usage percentage of limit
(container_memory_usage_bytes{name!=""} / container_spec_memory_limit_bytes{name!=""}) * 100

# Total platform memory usage
sum(container_memory_usage_bytes{name!=""}) / 6144000000 * 100
```

**Analysis Steps**:
1. Query historical metrics (7-30 days)
2. Identify average, peak, and P95 usage
3. Compare usage to allocated limits
4. Identify optimization opportunities
5. Calculate potential savings

### 4. Optimize Resource Limits

**Optimization Strategy**:

1. **Start Conservative**: Begin with limits slightly above actual usage
2. **Monitor Impact**: Track resource usage after optimization
3. **Iterate**: Adjust based on results
4. **Document**: Record limit changes and rationale

**Limit Adjustment Guidelines**:

- **Memory Limit**: Set to P95 usage + 20% buffer
- **Memory Reservation**: Set to average usage + 10% buffer
- **CPU Limit**: Usually not needed (shared CPU)
- **Consider Peak Usage**: Ensure limits accommodate peaks

**Example Optimization**:

```yaml
# Before: Over-allocated
deploy:
  resources:
    limits:
      memory: 100M
    reservations:
      memory: 50M
# Actual usage: 30MB average, 45MB peak

# After: Optimized
deploy:
  resources:
    limits:
      memory: 60M  # P95 + 20% buffer
    reservations:
      memory: 35M  # Average + 10% buffer
# Savings: 40MB freed
```

### 5. Validate Changes

**Validation Steps**:

1. **Monitor Resource Usage**: Track usage after changes
2. **Check for OOM**: Monitor for out-of-memory events
3. **Verify Performance**: Ensure service performance maintained
4. **Check Alerts**: Verify resource alerts still appropriate
5. **Team Feedback**: Get feedback from service owners

**Validation Period**: Monitor for 7-14 days after optimization

### 6. Document Changes

**Documentation Requirements**:

- Resource limits (before and after)
- Rationale for changes
- Date of change
- Expected impact
- Monitoring period
- Validation results

## Resource Allocation Guidelines

### Infrastructure Services

**Traefik** (Edge Layer):
- **Current**: 200MB limit, 100MB reservation
- **Typical Usage**: 50-100MB
- **Optimization**: Usually adequate, monitor for spikes

**PostgreSQL** (Data Layer):
- **Current**: 1.5GB limit, 1GB reservation
- **Typical Usage**: 800MB-1.2GB (varies with data)
- **Optimization**: Critical service, be conservative
- **Considerations**: Database size, connection count, query patterns

**Redis** (Cache Layer):
- **Current**: 300MB limit, 100MB reservation
- **Typical Usage**: 50-200MB (varies with cache size)
- **Optimization**: Monitor cache hit rate and memory usage
- **Considerations**: Cache size, eviction policy

**Prometheus** (Metrics):
- **Current**: 400MB limit, 200MB reservation
- **Typical Usage**: 200-350MB
- **Optimization**: Monitor series count, retention settings
- **Considerations**: Metrics volume, retention period

**Grafana** (Visualization):
- **Current**: 300MB limit, 150MB reservation
- **Typical Usage**: 100-250MB
- **Optimization**: Usually adequate
- **Considerations**: Dashboard complexity, user count

**Loki** (Logs):
- **Current**: 300MB limit, 150MB reservation
- **Typical Usage**: 100-250MB
- **Optimization**: Monitor log volume, retention settings
- **Considerations**: Log volume, retention period

### Application Services

**Guidelines**:
- **Target**: 50-100MB per service
- **Reservation**: 50% of limit
- **Optimization**: Based on actual usage patterns

**Service Types**:
- **Simple Services** (health-api): 50MB limit
- **Database Services** (data-api, user-api): 100MB limit
- **Service-to-Service** (aggregator-api): 100MB limit

**New Services**:
- Start with 100MB limit, 50MB reservation
- Monitor actual usage
- Optimize based on metrics

## Resource Optimization Best Practices

### Memory Optimization

**✅ DO**:
- Base limits on actual usage data (7-30 days)
- Use P95 usage + buffer for limits
- Use average usage + buffer for reservations
- Monitor for OOM events
- Document limit changes

**❌ DON'T**:
- Use arbitrary limits
- Ignore historical data
- Set limits too close to actual usage
- Ignore peak usage patterns
- Skip validation after changes

### CPU Optimization

**✅ DO**:
- Monitor CPU usage patterns
- Identify CPU-intensive services
- Consider CPU limits for noisy neighbors
- Monitor CPU pressure alerts

**❌ DON'T**:
- Set CPU limits unnecessarily
- Ignore CPU usage patterns
- Set CPU limits too low

### Resource Monitoring

**✅ DO**:
- Monitor resource usage continuously
- Track resource trends over time
- Alert on resource pressure
- Review resource allocation regularly

**❌ DON'T**:
- Ignore resource metrics
- Skip regular reviews
- Ignore resource alerts
- Optimize without data

### Service Design

**✅ DO**:
- Design services to be resource-efficient
- Use lightweight base images
- Optimize application code
- Release resources promptly

**❌ DON'T**:
- Design services without resource constraints
- Use bloated base images
- Hold resources unnecessarily
- Ignore resource efficiency

## Resource Optimization Checklist

### Pre-Optimization

- [ ] Review current resource allocation
- [ ] Collect usage metrics (7-30 days)
- [ ] Identify optimization opportunities
- [ ] Calculate potential savings
- [ ] Review resource alerts

### Optimization Process

- [ ] Identify services to optimize
- [ ] Analyze historical usage patterns
- [ ] Calculate new resource limits
- [ ] Update docker-compose.yml
- [ ] Document changes and rationale
- [ ] Test changes (if possible)

### Post-Optimization

- [ ] Monitor resource usage after changes
- [ ] Check for OOM events
- [ ] Verify service performance
- [ ] Validate resource alerts
- [ ] Get team feedback
- [ ] Document results

### Ongoing

- [ ] Regular resource review (monthly/quarterly)
- [ ] Monitor resource trends
- [ ] Adjust based on usage changes
- [ ] Update documentation
- [ ] Review resource budget

## Resource Monitoring and Analysis

### Monitoring Resource Usage

**Grafana Dashboards**:
- Infrastructure Health Dashboard: Total and per-service resource usage
- Service-specific dashboards: Individual service resource metrics

**Prometheus Queries**:

```promql
# Total memory usage percentage
(sum(container_memory_usage_bytes{name!=""}) / 6144000000) * 100

# Memory usage by service
container_memory_usage_bytes{name!=""} / container_spec_memory_limit_bytes{name!=""} * 100

# Services near memory limit (>80%)
(container_memory_usage_bytes{name!=""} / container_spec_memory_limit_bytes{name!=""}) * 100 > 80

# Memory usage trends
avg_over_time(container_memory_usage_bytes{name!=""}[1h])
```

### Identifying Resource Pressure

**Signs of Resource Pressure**:
- Total memory usage >85% of 6GB
- Services frequently hitting limits
- OOM events occurring
- Resource alerts firing frequently
- Service performance degradation

**Resource Pressure Indicators**:
- HighMemoryUsage alert firing
- CriticalMemoryUsage alert firing
- ServiceMemoryExhaustion alerts
- Container OOM kills

### Analyzing Resource Trends

**Trend Analysis**:
- Compare usage over time periods
- Identify growth patterns
- Predict future resource needs
- Plan for capacity changes

**Growth Planning**:
- Monitor resource usage trends
- Project future needs
- Plan optimizations proactively
- Reserve capacity for growth

## Common Optimization Scenarios

### Scenario 1: Over-Allocated Service

**Symptoms**: Service allocated 100MB but only uses 30MB average

**Solution**:
1. Analyze historical usage (P95: 45MB)
2. Reduce limit to 60MB (P95 + 20% buffer)
3. Reduce reservation to 35MB (average + 10%)
4. Monitor for 7 days
5. Document savings: 40MB freed

### Scenario 2: Under-Allocated Service

**Symptoms**: Service hitting memory limit frequently, OOM events

**Solution**:
1. Analyze peak usage (80MB peak)
2. Increase limit to 100MB (peak + 20% buffer)
3. Increase reservation to 50MB
4. Monitor for OOM events
5. Verify performance improvement

### Scenario 3: Resource Pressure

**Symptoms**: Total usage approaching 6GB, frequent resource alerts

**Solution**:
1. Identify over-allocated services
2. Optimize multiple services
3. Free up 200-300MB total
4. Monitor total usage
5. Verify alerts reduce

### Scenario 4: New Service Addition

**Symptoms**: Need to add new service but near resource limit

**Solution**:
1. Optimize existing services first
2. Free up capacity for new service
3. Add new service with conservative limits
4. Monitor and optimize new service
5. Document resource budget impact

## Resource Budget Management

### Budget Allocation

**Current Budget** (6GB):
- Infrastructure: 3GB (fixed)
- Applications: 1.5GB (growing)
- Buffer: 800MB (safety margin)

**Optimization Goals**:
- Free up capacity for new services
- Maintain safety margin
- Optimize without impacting performance

### Budget Tracking

**Track**:
- Total allocated memory
- Total used memory
- Available capacity
- Growth trends

**Alert On**:
- Total allocation >5.5GB (92%)
- Available capacity <500MB
- Rapid growth trends

## Troubleshooting

### Service OOM Events

**Symptoms**: Container killed due to OOM

**Diagnosis**:
1. Check container logs for OOM
2. Review memory usage before OOM
3. Compare usage to limit

**Solution**:
- Increase memory limit if legitimate usage
- Optimize service code if excessive usage
- Review memory leaks

### Resource Exhaustion

**Symptoms**: Platform running out of memory

**Diagnosis**:
1. Check total memory usage
2. Identify high-usage services
3. Review resource allocation

**Solution**:
- Optimize over-allocated services
- Reduce buffer if necessary
- Consider constraint increase (if approved)

### Performance Degradation

**Symptoms**: Services slow after optimization

**Diagnosis**:
1. Compare performance before/after
2. Check memory usage patterns
3. Review resource limits

**Solution**:
- Increase limits if too aggressive
- Review optimization assumptions
- Balance optimization with performance

## References

- Runtime Environment: `runtime-environment.md`
- Monitoring Architecture: `docs-devops/07-observability/monitoring-architecture.md`
- Resource Alerts: `project_devops/monitoring/prometheus/alerts/platform-alerts.yml`
- Platform Constraints: `docs-devops/00-overview/platform-constraints.md`
