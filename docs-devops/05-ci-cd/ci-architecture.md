# CI Architecture

## Stages

- Lint
- Build
- Test
- Package
- Security & law checks

The **security & law checks** stage must at minimum include:

- Static Application Security Testing (SAST)
- Dependency / vulnerability scanning
- Secret detection
- Platform law checks (small batch, trunk-based, unit tests, SLO/telemetry presence) as defined in `ai-context/platform-laws.yaml` và `ai-context/ci-enforcement/law-checks.yaml`.

## Artifact

Container image