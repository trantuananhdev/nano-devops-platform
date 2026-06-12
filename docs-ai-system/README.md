# HDTV AI System Design Documentation

![AI Agents Coverage](https://img.shields.io/badge/AI_Agents_Roadmap_Coverage-85%25-green)
![MCP](https://img.shields.io/badge/MCP-Supported-blue)
![RAG](https://img.shields.io/badge/RAG-Implemented-orange)
![Multi-Agent](https://img.shields.io/badge/Multi_Agent-Ready-purple)

## Overview

Chào mừng bạn đến với tài liệu thiết kế hệ thống AI của HDTV! Tài liệu này được tổ chức theo **roadmap.sh/ai-agents** để chứng minh độ phủ và chất lượng của kiến trúc hệ thống chúng tôi.

## Cấu trúc thư mục

| Thư mục | Audience | Mục đích |
|---------|----------|----------|
| `00-executive-summary/` | CEO + CTO | Bức tranh tổng quan — đọc đầu tiên (~5 phút) |
| `01-system-architecture/` | CTO | Biểu đồ kiến trúc 3 layers: Platform → HDTV AI → Flow |
| `02-ai-agent-design/` | CTO | AI Engine: Agent loop, LLM Router, Memory, HITL |
| `03-component-deep-dive/` | CTO | Từng component: Harness, MCP, RAG, Frontend |
| `04-platform-engineering/` | CTO | DevOps: Infra topology, CI/CD, Resource constraints |
| `05-security-and-reliability/` | CTO | Security design, Resilience patterns, Observability |
| `06-delivery-evidence/` | CEO | Proof of delivery: Sprint history, API coverage, Demo guide |
| `07-scaling-roadmap/` | CEO + CTO | Lộ trình scale: Medium → Enterprise → Air-gapped LLM |
| `99-appendix/` | Internal | Raw docs, task lists, implementation notes |

## Điểm nổi bật

- ✅ **MCP (Model Context Protocol)** - Hiện thực đầy đủ với streaming, audit logs
- ✅ **Plan-Execute-Reflect-Critic Loop** - Luồng agentic hoàn chỉnh
- ✅ **Multi-Agent System** - Planner, Executor, Reflector, Critic
- ✅ **Agent Memory** - Short/Long term + Vector DB (Chroma)
- ✅ **RAG** - Legal RAG với ingestion tự động
- ✅ **Execution Harness** - Validation, timeout, retry, error taxonomy
- ✅ **Observability** - Prometheus + Grafana + Loki + Jaeger
- ✅ **2-Node Production Topology** - Alpine cho everything, Ubuntu cho LLM
- ✅ **Circuit Breaker** - Độ bền cao với LLM API
