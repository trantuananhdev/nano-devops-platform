# System Overview

## Purpose

Nano DevOps Platform là một self-hosted DevOps environment được thiết kế để:

- Triển khai ứng dụng với zero-downtime
- Tối ưu tài nguyên (6GB RAM constraint)
- Chuẩn hoá CI/CD
- Cung cấp observability đầy đủ
- Sẵn sàng migrate lên cloud hoặc Kubernetes

## Core Values

- Automation First
- GitOps Driven
- Resource Efficiency
- Production-like Environment
- Self-healing mindset

## Target Users

- DevOps Engineers
- Backend Developers
- AI Agents
- System Operators

## System Scope

System bao gồm:

- Source Control
- CI/CD Pipeline
- Container Runtime
- Reverse Proxy
- Application Services
- Database
- Monitoring & Logging
- Backup & Restore

## Onboarding & Validation Entry Point

Để đưa platform từ zero → chạy đầy đủ và validate các capabilities chính (CI/CD, deploy, observability, backup, security), sử dụng guide:

- `docs-devops/00-overview/platform-onboarding-and-validation.md`

## Out of Scope

- Multi-region deployment
- High availability cluster
- Cloud-managed services