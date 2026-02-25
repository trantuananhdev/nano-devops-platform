# CI Directory

## Purpose

This directory contains CI/CD pipeline configurations and related scripts.

## Repository vs Runtime Mapping

- **Repository**: `project_devops/ci/`
- **Runtime**: `/opt/platform/ci/` (CI runner and related scripts)

## Contents

- CI pipeline definitions (GitHub Actions, GitLab CI, etc.)
- CI runner configurations
- Build scripts
- Test automation
- Security scanning configs
- Law enforcement checks

## Guidelines

- CI pipelines must enforce platform laws
- All code changes must go through CI
- CI must include: lint, build, test, package, security scans
- CI must check: small batch, trunk-based, unit tests, SLO, telemetry
- CI produces immutable container images
- Follow GitOps principles

## Structure Expectations

- Pipeline definitions
- CI runner configs
- Build automation
- Test frameworks
- Security scanning configs
