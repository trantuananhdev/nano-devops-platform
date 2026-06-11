# HDTV AI System Design Documentation

![AI Agents Coverage](https://img.shields.io/badge/AI_Agents_Roadmap_Coverage-85%25-green)
![MCP](https://img.shields.io/badge/MCP-Supported-blue)
![RAG](https://img.shields.io/badge/RAG-Implemented-orange)
![Multi-Agent](https://img.shields.io/badge/Multi_Agent-Ready-purple)

## Overview

Chào mừng bạn đến với tài liệu thiết kế hệ thống AI của HDTV! Tài liệu này được tổ chức theo **roadmap.sh/ai-agents** để chứng minh độ phủ và chất lượng của kiến trúc hệ thống chúng tôi.

## Cấu trúc thư mục

| Thư mục | Mục đích |
|---------|----------|
| `00-overview` | Tổng quan hệ thống, mục tiêu và kiến trúc tổng quát |
| `01-core-concepts` | Khái niệm cốt lõi: Agent Loop, Prompt Engineering, ... |
| `02-components` | Từng thành phần chi tiết: MCP, Memory, Tools, LLM Router, ... |
| `03-architectures` | Các mẫu kiến trúc: Plan-Execute-Reflect, ReAct, ... |
| `04-security` | An ninh hệ thống, sandboxing, API keys, guardrails |
| `05-observability` | Monitoring, logging, audit trails |
| `06-infrastructure` | Cơ sở hạ tầng: Docker, K8s, 2-node topology |
| `07-evaluation` | Đánh giá và testing agent |
| `08-roadmap-coverage` | Độ phủ so với roadmap.sh, chỉ ra thành tựu |
| `99-appendix` | Tham khảo, glossary, quick reference |

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
