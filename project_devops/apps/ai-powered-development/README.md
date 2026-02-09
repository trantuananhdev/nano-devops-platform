# AI-Powered Development: The Ghost Engineer 👻

> **"The Ghost Engineer is not just a tool; it's a silent SRE partner that haunts your infrastructure to fix bugs before you even wake up."**

Welcome to **The Ghost Engineer**, a self-healing AI Agentic ecosystem designed with the "Efficiency by Design" philosophy. This system is capable of autonomously detecting, analyzing, fixing, and submitting Pull Requests for incidents in Microservices environments—all operating smoothly within strict resource constraints (6GB RAM).

---

## 🧠 Design Philosophy & Architecture

The system is divided into two distinct entities, mimicking the "Eyes" and "Brain" of a real engineer:

### 1. **Production: The Silent Sentinel (Agent-Node)**
- **Language**: **Go** (Zero-dependency, Native Docker Socket communication).
- **Role**: The "Eyes" of the system. Runs directly on production nodes with an ultra-low footprint (**<20MB RAM**).
- **Functionality**: 
  - Monitors Docker Events (die, oom, crash) via Unix Sockets.
  - Captures the final log context before a container collapses.
  - **Zero Reasoning**: The Sentinel does not reason; it only **Detects -> Packages Context -> Reports** to the Brain. This ensures production performance is never impacted by heavy AI logic.

### 2. **Platform: The Ghost Workshop (AI-Agent)**
- **Language**: **Node.js** (Reasoning Engine).
- **Role**: The central "Brain". Completely isolated from Production.
- **Functionality**:
  - **Reasoning**: Uses LLMs (Gemini 2.5 Flash) to perform Root Cause Analysis (RCA) from logs.
  - **Sandbox Factory**: Spawns temporary Alpine-based environments to clone code and verify patches.
  - **Self-Correction**: If the initial patch fails the Verification Gate, the AI reads the test errors and performs a self-correction loop (up to 3 attempts).

---

## 🛠 End-to-End Agentic AI Flow

The system executes a full-cycle process without human intervention:

1.  **Detection**: The Sentinel detects a container (e.g., `faulty-service`) crashing with a non-zero exit code.
2.  **Context Injection**: The system automatically maps the container to its corresponding Repository, clones the source code, and extracts critical files (`server.js`, `app.py`, etc.) for prompt context.
3.  **Autonomous Reasoning**: The AI analyzes the discrepancy between expected behavior and actual logs (e.g., Race Condition or Memory Leak).
4.  **Multi-Strategy Patching**:
    - **Levels 1-3**: Attempts `git apply` with varying whitespace tolerance levels.
    - **Level 4 (Ultra-Fuzzy)**: Uses the system `patch` command to handle patches with line number offsets.
5.  **Verification Gate**: 
    - Automatically identifies the Tech Stack (Node.js, Python, Java, PHP).
    - Executes the corresponding install and test suite commands (`npm test`, `pytest`, etc.).
6.  **GitOps Delivery**: If the tests pass, the AI performs a commit and opens a Pull Request on GitHub with a full explanation of the bug and its fix.

---

## ⚡ Stack Agnostic Capabilities

Ghost Engineer is not limited to a single language. it "reads" the project to self-configure:
- **Node.js**: Detects `package.json`, uses `npm/yarn/pnpm`.
- **Python**: Detects `requirements.txt/poetry.lock`, uses `pytest`.
- **Java**: Detects `pom.xml` or `build.gradle`, runs Maven/Gradle.
- **PHP**: Detects `composer.json`, runs `phpunit`.

---

## 🚀 Why is this True Agentic AI?

Unlike Copilot tools that only assist in writing code, Ghost Engineer demonstrates **Agentic** thinking:
- **Autonomy**: Makes decisions from detection to PR submission.
- **Tool Use**: Proficiently uses Git, Docker, Patch, and Test Runners.
- **Feedback Loop**: Reads errors from test runners to self-correct its own patches.
- **Resource Efficiency**: The hybrid use of Go (Performance) and Node.js (Reasoning) demonstrates infrastructure optimization mindset.

---

## � Project Structure

- [agent-node/](file:///c:/TA-work/nano-project-devops/project_devops/apps/ai-powered-development/agent-node): Go-based monitoring sensor.
- [ai-agent/](file:///c:/TA-work/nano-project-devops/project_devops/apps/ai-powered-development/ai-agent): Node.js-based AI reasoning workshop.
- [guide-ai-agent/](file:///c:/TA-work/nano-project-devops/project_devops/apps/ai-powered-development/guide-ai-agent): System design documentation and "6 Layers of AI Engineering".
- [faulty-service/](file:///c:/TA-work/nano-project-devops/project_devops/apps/ai-powered-development/faulty-service): Demo target with intentional bugs (Race Condition, Memory Leak) for the AI to fix.

---
*Developed by Ghost Engineer Team - Haunting your bugs away.* 👻
