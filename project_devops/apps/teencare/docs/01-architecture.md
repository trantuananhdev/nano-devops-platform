# Kiến trúc tổng thể — System Architecture

## 2.1 Pipeline Overview

Nguồn vào: **RAW TRANSCRIPT** (noisy audio-to-text).

Luồng xử lý:

- **Step 1**: Pre-processing & Speaker Diarization  
- **Step 2**: Context Assembly (3-layer RAG)  
- **Step 3**: Single Structured LLM Call (temp=0, JSON schema)  
- **Step 4**: Validation & Guardrails (semantic grounding check)  
- **Step 5**: Delivery to Parent (push, \<5 phút)

## 2.2 Thành phần (logical components)

- **Ingest Service**
  - Nhận `raw_transcript`, metadata session
  - Tạo `session_id`, chuẩn hóa thời gian, routing pipeline

- **Preprocess/Diarization Service (Step 1)**
  - Clean transcript (filler removal, sentence repair)
  - Diarization: TEEN / MENTOR / PARENT (Phase 1: rule-based)
  - Trả về `turns[]` + `quality_score`

- **Context Assembler (Step 2)**
  - Layer 1: teen profile summary (always)
  - Layer 2: history retrieval (dynamic; Phase 1 đơn giản theo date)
  - Layer 3: transcript hôm nay đã clean (always)
  - Quản lý token budget

- **LLM Orchestrator (Step 3)**
  - 1 call duy nhất, `temperature=0`
  - Output JSON theo schema bắt buộc
  - Lưu log request/response (redaction nếu cần)

- **Validation & Guardrails (Step 4)**
  - Schema validation
  - Semantic grounding check cho từng insight
  - LLM-as-judge cho `risk_level=high`
  - Retry strategy + circuit breaker

- **Delivery Service (Step 5)**
  - Push notification + in-app card
  - SLA: \<5 phút (Phase 1); có fallback “stale/last summary”

- **Storage**
  - Raw transcript (audit)
  - Clean turns
  - Rolling summaries
  - Outputs + flags + grounding scores

## 2.3 Phase rollout

- **Phase 1 (MVP ~2 tuần)**
  - Step 1 rule-based diarization
  - Context: Layer 1 + Layer 3; history theo date (top-k)
  - Validation: semantic grounding check cơ bản

- **Phase 2 (~1 tháng)**
  - Rolling summary
  - Embeddings + semantic retrieval (cosine similarity)
  - LLM-assisted diarization khi confidence thấp

- **Phase 3 (~3 tháng)**
  - Topic clustering + recency weighting + rerank theo family goals
  - Eval automation + prompt iteration loop chuẩn hóa

## 2.4 SLO/SLA mục tiêu

- **Latency end-to-end**: \<5 giây (compute) / \<5 phút (delivery)
- **Schema validity**: 100%
- **Grounding pass rate**: \>90% insights có similarity \>0.75
- **Hallucination rate**: \<5% (theo heuristic + judge + feedback)

