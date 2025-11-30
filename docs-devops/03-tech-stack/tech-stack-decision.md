# Tech Stack Decisions

## Why Docker instead of Kubernetes

- Lower resource usage
- Simpler operation
- Phù hợp single-node

## Why Traefik

- Dynamic configuration
- Native Docker integration
- Lightweight

## Why Self-hosted

- Full control
- Cost optimization
- Production-like learning environment

All tools must satisfy:

- Memory footprint < 300MB (steady state)
- Low idle CPU
- Single-node compatible