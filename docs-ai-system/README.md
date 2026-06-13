# HDTV AI System Design Documentation

![AI Agents Coverage](https://img.shields.io/badge/AI_Agents_Roadmap_Coverage-85%25-green)
![MCP](https://img.shields.io/badge/MCP-Supported-blue)
![RAG](https://img.shields.io/badge/RAG-Implemented-orange)
![Multi-Agent](https://img.shields.io/badge/Multi_Agent-Ready-purple)

## Overview

Chào mừng bạn đến với tài liệu thiết kế hệ thống AI của HDTV! Tài liệu này được cấu trúc lại để phục vụ 2 nhóm người đọc chính (CEO & CTO) nhằm làm nổi bật cả giá trị nghiệp vụ lẫn chiều sâu kỹ thuật của hệ thống.

---

## Cấu trúc thư mục

| Thư mục | Audience | Mục đích |
|---------|----------|----------|
| [`00-executive-summary/`](./00-executive-summary/) | **CEO + CTO** | Bức tranh tổng quan — đọc đầu tiên (~5 phút) để nắm rõ những gì đã build, giá trị mang lại và bằng chứng ship. |
| [`01-system-architecture/`](./01-system-architecture/) | **CTO** | Biểu đồ kiến trúc 3 layers: từ Platform hạ tầng, mô hình HDTV AI đến Sequence Flow chi tiết. |
| [`02-ai-agent-design/`](./02-ai-agent-design/) | **CTO** | Trọng tâm AI Engine: Kiến trúc Agent loop (Plan-Execute-Reflect-Critic), LLM Router, Memory, và Human-in-the-loop. |
| [`03-component-deep-dive/`](./03-component-deep-dive/) | **CTO** | Đào sâu từng thành phần: Execution Harness, MCP Server, Legal RAG, và Frontend Architecture. |
| [`04-platform-engineering/`](./04-platform-engineering/) | **CTO** | Nền tảng DevOps: Quy hoạch hạ tầng 2-node topology, CI/CD Pipeline, và quản lý giới hạn tài nguyên RAM 6GB. |
| [`05-security-and-reliability/`](./05-security-and-reliability/) | **CTO** | Đảm bảo vận hành: Thiết kế bảo mật Sandbox/API key, Resilience patterns, và hệ thống giám sát Observability. |
| [`06-delivery-evidence/`](./06-delivery-evidence/) | **CEO** | Bằng chứng bàn giao: Lịch sử Sprint (T-01 đến T-66), API coverage, Demo guide, và Roadmap coverage. |
| [`99-appendix/`](./99-appendix/) | **Internal** | Tài liệu kỹ thuật cũ làm reference, nhật ký phát triển, và **Lộ trình scale hệ thống (Scaling Roadmap)**. |

---

## Các điểm công nghệ nổi bật

* ✅ **MCP (Model Context Protocol)**: Hiện thực chuẩn hóa với SSE streaming, bảo mật và audit log đầy đủ.
* ✅ **Plan-Execute-Reflect-Critic Loop**: Quy trình agentic thông minh tự sửa lỗi và tối ưu hiệu suất qua execution batch song song.
* ✅ **Hệ thống Memory phân tầng**: Short-term + Long-term Vector DB (Chroma) + Feedback loop để Agent tự học hỏi.
* ✅ **Hạ tầng tối ưu**: Vận hành lean trên VM 6GB RAM (Alpine Linux cho các service và Ubuntu cho LLM Gemma 4).
* ✅ **Observability hoàn thiện**: Prometheus + Grafana + Loki + Jaeger với 14 alert rules thiết lập sẵn.
