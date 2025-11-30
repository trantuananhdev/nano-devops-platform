# Engineering Report: Resource Optimization & Kernel Tuning

This report details the technical measures taken to stabilize a 15+ service enterprise stack on a single-node Alpine Linux environment with only **6GB RAM**.

## 🚀 The Challenge
Running Odoo (ERP), PostgreSQL, Redis, and a full Prometheus/Grafana observability suite typically requires 12GB+ RAM. Our constraint was 50% of the industry standard.

## 🛠 Technical Implementation

### 1. Kernel-Level Hardening & Tuning
Through [sysctl_tuning.sh](../../project_devops/platform/infra/scripts/system/sysctl_tuning.sh), we didn't just use defaults. We optimized:
- **Virtual Memory:** Adjusted `vm.swappiness=10` to avoid disk thrashing while keeping RAM available for critical cache.
- **Network Stack:** Increased `net.core.somaxconn` and optimized TCP buffers to handle the inter-service communication overhead of the microservices architecture without latency spikes.
- **ZRAM Integration:** Implemented [zram_config.sh](../../project_devops/platform/infra/scripts/system/zram_config.sh) to create a compressed swap device in RAM, effectively "expanding" our 6GB capacity by ~2GB with minimal CPU overhead.

### 2. Docker Resource Orchestration
Our [docker-compose.yml](../../project_devops/platform/composition/docker-compose.yml) utilizes advanced `deploy.resources` constraints:
- **Hard Limits:** Every service has a strictly defined `memory.limit`. This prevents a single service (e.g., a heavy Odoo report) from triggering an Out-Of-Memory (OOM) event for the entire host.
- **Reservations:** We use `memory.reservation` to ensure critical services like `platform-postgres` and `platform-traefik` always have their required footprint guaranteed, regardless of other service spikes.

### 3. Redis Memory Management
By passing `--maxmemory 128mb --maxmemory-policy allkeys-lru` directly to the Redis engine, we ensured that our cache layer never becomes a memory liability, automatically evicting the least used keys when limits are reached.

## 📊 Results
- **Idle State:** ~1.8GB RAM usage.
- **Full Load (Odoo + Observability):** ~4.5GB RAM usage.
- **Headroom:** ~1.5GB remaining for burst operations.

**Conclusion:** The platform is stabilized through precise system-level engineering rather than hardware over-provisioning.
