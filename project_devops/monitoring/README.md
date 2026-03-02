# Monitoring Directory

## Purpose

This directory contains monitoring and observability configurations.

## Repository vs Runtime Mapping

- **Repository**: `project_devops/monitoring/`
- **Runtime**: `/opt/platform/monitoring/`

## Contents

- Prometheus configuration files
- Grafana dashboards and provisioning
- Loki configuration
- Alert rules
- Service discovery configs
- Monitoring exporters configuration

## Guidelines

- All services must be monitored
- Metrics, logs, and traces must be configured
- SLO definitions must be present
- Alert rules must be defined
- Monitoring configs must be versioned in Git
- Follow observability-first principle

## Structure Expectations

- Prometheus scrape configs
- Grafana dashboard definitions
- Loki log collection configs
- Alert rule definitions
- Service discovery configurations
