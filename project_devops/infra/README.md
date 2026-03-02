# Infrastructure Directory

## Purpose

This directory contains Infrastructure as Code (IaC) definitions and infrastructure-related configurations.

## Repository vs Runtime Mapping

- **Repository**: `project_devops/infra/`
- **Runtime**: Infrastructure definitions are used to configure `/opt/platform/` runtime

## Contents

- Infrastructure service definitions
- Network configurations
- Storage/volume definitions
- Infrastructure monitoring configs
- Infrastructure deployment scripts

## Guidelines

- Infrastructure must be immutable
- Infrastructure must be idempotent
- All infrastructure changes go through Git
- Follow GitOps principles
- Infrastructure definitions should be versioned
