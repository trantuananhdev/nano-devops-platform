# Alert Tuning Guide

This document describes how to tune monitoring alerts based on actual usage patterns to ensure alerts are actionable and reduce alert fatigue.

## Overview

Alert tuning is the process of adjusting alert thresholds, durations, and conditions based on actual system behavior to ensure:
- **Actionable alerts**: Alerts indicate real issues requiring attention
- **Reduced noise**: Minimize false positives and alert fatigue
- **Appropriate sensitivity**: Alerts fire when issues occur, not during normal operation
- **Clear priorities**: Critical alerts get immediate attention

## Alert Tuning Workflow

### 1. Pre-Tuning Evaluation

Before tuning alerts, evaluate current alert effectiveness:

**Metrics to Track**:
- Alert frequency (alerts per day/week)
- Alert resolution time
- False positive rate
- Alert acknowledgment rate
- Alert fatigue indicators

**Questions to Answer**:
- Are alerts firing too frequently?
- Are alerts being ignored?
- Are alerts actionable?
- Do alerts indicate real issues?
- Are thresholds appropriate for actual usage?

### 2. Identify Alert Issues

**Common Alert Problems**:

1. **Too Sensitive**:
   - Alerts fire during normal operation
   - High false positive rate
   - Alerts resolve themselves quickly
   - No action required

2. **Too Insensitive**:
   - Alerts don't fire when issues occur
   - Issues discovered manually
   - Alerts fire too late

3. **Wrong Thresholds**:
   - Thresholds don't match actual usage patterns
   - Alerts fire at wrong times
   - Thresholds based on assumptions, not data

4. **Alert Fatigue**:
   - Too many alerts
   - Alerts ignored
   - Team desensitized to alerts

### 3. Analyze Usage Patterns

**Data Sources**:
- Prometheus metrics (historical data)
- Grafana dashboards (trends)
- Alert history (frequency, patterns)
- Service logs (correlation)

**Patterns to Identify**:
- Normal operating ranges
- Peak usage times
- Baseline metrics
- Anomaly patterns
- Seasonal variations

**Example Analysis**:
```promql
# Average memory usage over 7 days
avg_over_time(container_memory_usage_bytes[7d])

# P95 latency over 7 days
histogram_quantile(0.95, rate(request_duration_seconds_bucket[7d]))

# Error rate trends
rate(http_requests_total{status=~"5.."}[5m])
```

### 4. Adjust Alert Thresholds

**Threshold Adjustment Strategy**:

1. **Start Conservative**: Begin with thresholds slightly above normal operation
2. **Monitor Impact**: Track alert frequency after adjustment
3. **Iterate**: Adjust based on results
4. **Document**: Record threshold changes and rationale

**Common Adjustments**:

- **Increase Thresholds**: If alerts fire too frequently
- **Decrease Thresholds**: If issues not detected
- **Adjust Duration**: Change `for` clause based on alert type
- **Add Conditions**: Combine multiple conditions for better accuracy

### 5. Validate Changes

**Validation Steps**:

1. **Test in Staging**: If possible, test alert changes in staging
2. **Monitor Alert Frequency**: Track alert rate after changes
3. **Verify Actionability**: Ensure alerts still indicate real issues
4. **Check False Positives**: Monitor for false positives
5. **Team Feedback**: Get feedback from on-call team

### 6. Document Changes

**Documentation Requirements**:

- Threshold values (before and after)
- Rationale for changes
- Date of change
- Expected impact
- Monitoring period

## Alert Evaluation Guidelines

### Alert Effectiveness Metrics

**Key Metrics**:
- **Alert Frequency**: Number of alerts per time period
- **False Positive Rate**: Percentage of alerts that don't require action
- **Mean Time to Acknowledge (MTTA)**: Time from alert to acknowledgment
- **Mean Time to Resolve (MTTR)**: Time from alert to resolution
- **Alert Resolution Rate**: Percentage of alerts resolved

**Target Metrics**:
- False positive rate: < 10%
- MTTA: < 5 minutes (critical), < 30 minutes (warning)
- Alert resolution rate: > 90%
- Alert frequency: Reasonable for team capacity

### Alert Classification

**Alert Severity Levels**:

1. **Critical**: Immediate action required, service down or critical failure
2. **Warning**: Action required soon, potential issue or degradation
3. **Info**: Informational, no immediate action required

**Alert Categories**:

- **Service Health**: Service up/down, availability
- **Performance**: Latency, throughput, response time
- **Resource**: Memory, CPU, disk usage
- **Errors**: Error rates, exception rates
- **Business**: Business metrics, SLO breaches

### False Positive Identification

**False Positive Indicators**:
- Alert fires but no issue exists
- Alert resolves without action
- Alert fires during known maintenance
- Alert fires during normal operation spikes
- Alert fires but investigation shows no problem

**False Positive Reduction**:
- Adjust thresholds based on actual patterns
- Add conditions to filter known false positives
- Increase duration (`for` clause) to reduce transient alerts
- Add exclusions for maintenance windows

### Alert Fatigue Prevention

**Signs of Alert Fatigue**:
- Alerts ignored or muted
- Team desensitized to alerts
- High alert volume
- Low alert resolution rate
- Team complaints about alert noise

**Prevention Strategies**:
- Reduce alert volume (tune thresholds)
- Group related alerts
- Use alert severity appropriately
- Implement alert routing
- Regular alert review and cleanup

## Alert Tuning Best Practices

### Threshold Selection

**✅ DO**:
- Base thresholds on actual usage data (7-30 days)
- Use percentiles (P95, P99) for latency alerts
- Consider normal operating ranges
- Account for peak usage periods
- Set thresholds slightly above normal operation

**❌ DON'T**:
- Use arbitrary thresholds
- Ignore historical data
- Set thresholds too close to normal operation
- Ignore peak usage patterns
- Copy thresholds from other systems without validation

### Duration Selection

**✅ DO**:
- Use longer durations for resource alerts (5-10 minutes)
- Use shorter durations for critical service alerts (1-2 minutes)
- Consider alert type and impact
- Account for transient spikes

**❌ DON'T**:
- Use same duration for all alerts
- Set durations too short (causes noise)
- Set durations too long (delays detection)

### Alert Grouping

**✅ DO**:
- Group related alerts
- Use alert labels for grouping
- Reduce duplicate alerts
- Consolidate similar alerts

**❌ DON'T**:
- Create too many individual alerts
- Ignore alert relationships
- Duplicate alerts unnecessarily

### Alert Documentation

**✅ DO**:
- Document alert purpose
- Document threshold rationale
- Document expected response
- Document runbook links
- Keep documentation updated

**❌ DON'T**:
- Leave alerts undocumented
- Use unclear alert descriptions
- Ignore documentation updates

## Alert Tuning Checklist

### Pre-Tuning

- [ ] Review alert frequency and patterns
- [ ] Identify alert issues (too sensitive, too insensitive)
- [ ] Analyze usage patterns (metrics, trends)
- [ ] Gather team feedback on alerts
- [ ] Review alert history and resolution

### Tuning Process

- [ ] Identify alerts needing tuning
- [ ] Analyze historical metrics for thresholds
- [ ] Adjust alert thresholds appropriately
- [ ] Adjust alert durations if needed
- [ ] Test alert changes (if possible)
- [ ] Document threshold changes

### Post-Tuning

- [ ] Monitor alert frequency after changes
- [ ] Track false positive rate
- [ ] Verify alert actionability
- [ ] Get team feedback
- [ ] Document changes and rationale
- [ ] Schedule follow-up review

### Ongoing

- [ ] Regular alert review (monthly/quarterly)
- [ ] Monitor alert effectiveness metrics
- [ ] Adjust based on usage changes
- [ ] Remove unused alerts
- [ ] Update documentation

## Alert Noise Reduction Strategies

### Threshold Tuning

**Strategy**: Adjust thresholds to match actual usage patterns

**Example**:
```yaml
# Before: Too sensitive
- alert: HighMemoryUsage
  expr: memory_usage > 80
  for: 1m

# After: Tuned based on actual usage (normal: 60-70%)
- alert: HighMemoryUsage
  expr: memory_usage > 85
  for: 5m
```

### Duration Adjustment

**Strategy**: Increase duration to reduce transient alerts

**Example**:
```yaml
# Before: Fires on transient spikes
- alert: HighCPUUsage
  expr: cpu_usage > 80
  for: 1m

# After: Only fires on sustained usage
- alert: HighCPUUsage
  expr: cpu_usage > 80
  for: 10m
```

### Alert Grouping

**Strategy**: Group related alerts to reduce volume

**Example**:
```yaml
# Group multiple service alerts
- alert: ServiceHealth
  expr: up{service=~"api-.*"} == 0
  labels:
    service: "{{ $labels.service }}"
```

### Alert Suppression

**Strategy**: Suppress alerts during known events

**Example**:
- Maintenance windows
- Expected load spikes
- Known issues being resolved

### Severity Levels

**Strategy**: Use appropriate severity to prioritize

**Example**:
- Critical: Service down, immediate action
- Warning: Degradation, action soon
- Info: Informational, no action

### Alert Routing

**Strategy**: Route alerts to appropriate channels

**Example**:
- Critical alerts → On-call pager
- Warning alerts → Slack channel
- Info alerts → Dashboard only

## Common Alert Tuning Scenarios

### Scenario 1: Too Many False Positives

**Symptoms**: Alerts fire frequently but no action needed

**Solution**:
1. Analyze alert patterns
2. Identify false positive causes
3. Adjust thresholds upward
4. Increase duration
5. Add conditions to filter false positives

### Scenario 2: Missing Real Issues

**Symptoms**: Issues occur but alerts don't fire

**Solution**:
1. Analyze missed incidents
2. Review alert thresholds
3. Lower thresholds if needed
4. Add new alerts if gaps exist
5. Reduce duration for faster detection

### Scenario 3: Alert Fatigue

**Symptoms**: Too many alerts, team ignoring them

**Solution**:
1. Reduce alert volume (tune thresholds)
2. Group related alerts
3. Use severity levels appropriately
4. Implement alert routing
5. Remove unnecessary alerts

### Scenario 4: Thresholds Don't Match Usage

**Symptoms**: Alerts fire at wrong times, don't reflect actual usage

**Solution**:
1. Analyze historical metrics
2. Identify normal operating ranges
3. Adjust thresholds to match patterns
4. Account for peak usage
5. Document threshold rationale

## Alert Tuning Examples

### Example 1: Memory Usage Alert

**Initial Configuration**:
```yaml
- alert: HighMemoryUsage
  expr: (sum(container_memory_usage_bytes) / 6144000000) * 100 > 80
  for: 1m
```

**Issue**: Fires too frequently during normal operation

**Analysis**: Historical data shows normal usage 60-75%, peaks at 78%

**Tuned Configuration**:
```yaml
- alert: HighMemoryUsage
  expr: (sum(container_memory_usage_bytes) / 6144000000) * 100 > 85
  for: 5m
```

**Rationale**: Increased threshold to 85% and duration to 5m to reduce false positives while still detecting real issues

### Example 2: Latency Alert

**Initial Configuration**:
```yaml
- alert: HighLatency
  expr: histogram_quantile(0.95, rate(request_duration_seconds_bucket[5m])) > 0.5
  for: 2m
```

**Issue**: Doesn't fire when users report slow responses

**Analysis**: Historical P95 latency: 0.3s normal, 0.8s during issues

**Tuned Configuration**:
```yaml
- alert: HighLatency
  expr: histogram_quantile(0.95, rate(request_duration_seconds_bucket[5m])) > 0.7
  for: 5m
```

**Rationale**: Lowered threshold to 0.7s and increased duration to 5m to catch real issues while reducing noise

## References

- Monitoring Architecture: `monitoring-architecture.md`
- Alert Rules: `project_devops/monitoring/prometheus/alerts/platform-alerts.yml`
- Prometheus Query Language: [PromQL Documentation](https://prometheus.io/docs/prometheus/latest/querying/basics/)
