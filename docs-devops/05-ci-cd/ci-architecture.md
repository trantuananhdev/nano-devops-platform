# CI Architecture

## Stages

- Lint
- Build
- Test
- Package
- Security & law checks

### Lint Stage

The lint stage performs static code analysis on all code in the repository:

- **ShellCheck**: Lints all shell scripts in `project_devops/` directory
  - Format: GCC-style output
  - Severity: Warning level (non-blocking)
  - Scans: All `.sh` files recursively

- **YAML Lint**: Validates YAML files for syntax and style
  - Config: `.yamllint.yml`
  - Format: GitHub annotations
  - Non-blocking: Continues on errors

- **Hadolint**: Lints Dockerfiles for best practices
  - Scans: All Dockerfiles in `project_devops/`
  - Ignores: DL3008 (apt-get pinning), DL3009 (apt-get cleanup)
  - Threshold: Warning level (non-blocking)

- **Markdown Lint**: Validates Markdown documentation
  - Tool: markdownlint-cli2
  - Scans: All `.md` files
  - Non-blocking: Exit code 0

### Build Stage

Builds container images for all services:
- health-api
- data-api
- aggregator-api
- user-api

Images are built but not pushed (push happens in package stage).

### Test Stage

Runs automated tests and validations:

- **Docker Compose Validation**: Validates `docker-compose.yml` syntax
  - Uses: `docker compose config`
  - Validates: Service definitions, networks, volumes, environment variables
  - Blocking: Fails build if validation fails

- **Deployment Script Tests**: Integration tests for deployment scripts
  - Script: `project_devops/ci/tests/test-deployment-scripts.sh`
  - Tests: Syntax validation, environment variable checks, error handling
  - Blocking: Fails build if tests fail

- **ShellCheck on Scripts**: Additional shellcheck validation
  - Scans: `deploy.sh`, `rollback.sh`
  - Non-blocking: Warnings only

### Package Stage

Builds and pushes container images to GitHub Container Registry:
- Images tagged with commit SHA and `latest` (on main branch)
- Only pushes on push to main branch
- Uses GitHub Actions cache for faster builds

### Security & Law Checks Stage

The **security & law checks** stage must at minimum include:

- **Platform Law Checks**: Validates compliance with platform laws
  - Script: `project_devops/ci/check-platform-laws.sh`
  - Checks: Small batch, trunk-based, unit tests, SLO/telemetry presence
  - Defined in: `ai-context/platform-laws.yaml` and `ai-context/ci-enforcement/law-checks.yaml`

- **Static Application Security Testing (SAST)**:
  - CodeQL: Security analysis for shell, YAML, Dockerfile
  - Semgrep: Security audit patterns for multiple languages
  - Results: Uploaded to GitHub Security tab

- **Dependency / Vulnerability Scanning**:
  - OWASP Dependency Check: Scans for known vulnerabilities
  - CVSS Threshold: Fails on CVSS >= 7.0
  - Format: SARIF (uploaded to GitHub Security)

- **Secret Detection**:
  - Gitleaks: Scans git history for secrets
  - Config: `.gitleaks.toml`
  - Non-blocking: Reports only (exit code 0)

## Artifact

Container image

## Automation Enhancements

### Implemented Enhancements (Phase 2 Task 6)

1. **Linting Tool Integration**:
   - Added ShellCheck, YAML lint, Hadolint, Markdown lint to lint stage
   - All linting tools configured with appropriate severity levels
   - Non-blocking by default to avoid breaking builds on style issues

2. **Test Automation Improvements**:
   - Added Docker Compose configuration validation
   - Improved shellcheck integration in test stage
   - Enhanced test runner script with docker-compose validation

3. **Why Post-Deployment Automation Not Implemented**:
   - Deployment is manual and GitOps-compliant (intentional design)
   - Deployments happen on VM, not in GitHub Actions
   - Smoke tests are run manually after deployment (see deployment runbook)
   - Automated deployment would require VM access and compromise GitOps safety

### Future Enhancement Opportunities

- **Deployment Notifications**: Could add GitHub Actions workflow dispatch for deployment status updates
- **Automated Smoke Tests**: Could be added as a separate workflow triggered after manual deployment
- **Linting Stricter Enforcement**: Could make linting blocking for critical issues
- **Test Coverage Reporting**: Could add coverage reports for application tests