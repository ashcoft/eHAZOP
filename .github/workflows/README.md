# GitHub Workflows Documentation

This document describes the CI/CD workflows configured for the EHAZOP Platform.

## Overview

The project uses GitHub Actions for continuous integration and deployment with the following workflows:

| Workflow | File | Description | Triggers |
|----------|------|-------------|----------|
| **CI** | `ci.yml` | Basic CI checks for backend, frontend, and Docker | Push/PR to main, develop |
| **CodeQL** | `codeql.yml` | Security scanning with CodeQL | Push/PR to main, scheduled weekly |
| **Python Tests** | `python-tests.yml` | Backend testing, linting, type checking, security | Push/PR to main, develop |
| **Frontend Tests** | `frontend-tests.yml` | Frontend testing, linting, type checking, security | Push/PR to main, develop |
| **Playwright** | `playwright.yml` | End-to-end browser testing | Push/PR to main, develop |
| **Docker** | `docker.yml` | Build and push Docker images | Push/PR to main, develop, tags |
| **Release** | `release.yml` | Auto-release using Changesets | Push to main |
| **Dependency Updates** | `dependency-updates.yml` | Automated dependency updates | Weekly (Mondays 2 AM UTC) |

## Workflows Detail

### 1. CI (Continuous Integration) - `ci.yml`

**Purpose**: Basic continuous integration checks

**Jobs**:
- **backend**: Python syntax verification, import tests
- **frontend**: Node.js setup, dependency installation, build
- **docker**: Docker image build validation

**Triggers**:
- Push to `main` or `develop` branches
- Pull requests targeting `main` or `develop` branches

### 2. CodeQL Analysis - `codeql.yml`

**Purpose**: Advanced security scanning using GitHub's CodeQL

**Languages Analyzed**:
- Python
- JavaScript/TypeScript
- GitHub Actions

**Triggers**:
- Push to `main` branch
- Pull requests targeting `main` branch
- Scheduled weekly (Sundays at 10:27 AM UTC)

### 3. Python Tests and Linting - `python-tests.yml`

**Purpose**: Comprehensive backend testing and code quality checks

**Jobs**:
- **python-tests**: 
  - Ruff linting and formatting
  - mypy type checking
  - pytest with coverage reporting
  - Codecov integration
  
- **security-check**:
  - Safety dependency vulnerability scanning
  - Bandit security linter

**Services**:
- PostgreSQL (pgvector)
- Redis

**Triggers**:
- Push to `main` or `develop` branches
- Pull requests targeting `main` or `develop` branches

**Artifacts**:
- Coverage reports (HTML and XML)
- Bandit security report

### 4. Frontend Tests and Linting - `frontend-tests.yml`

**Purpose**: Frontend code quality and build validation

**Jobs**:
- **frontend-tests**:
  - ESLint linting
  - TypeScript type checking
  - Production build
  
- **frontend-security**:
  - npm audit
  - Snyk security scanning

**Triggers**:
- Push to `main` or `develop` branches
- Pull requests targeting `main` or `develop` branches

**Artifacts**:
- Frontend build artifacts

### 5. Playwright E2E Tests - `playwright.yml`

**Purpose**: End-to-end browser testing

**Features**:
- Chromium browser testing
- Full application stack (backend + frontend)
- HTML test reports
- Failure screenshots

**Services**:
- PostgreSQL (pgvector)
- Redis

**Triggers**:
- Push to `main` or `develop` branches
- Pull requests targeting `main` or `develop` branches

**Artifacts**:
- Playwright HTML report
- Failure screenshots

### 6. Docker Build and Push - `docker.yml`

**Purpose**: Build and publish Docker images

**Jobs**:
- **build-backend**: Multi-platform backend image (amd64, arm64)
- **build-frontend**: Frontend image
- **compose-validation**: Docker Compose configuration validation

**Image Tags**:
- `latest`: From `main` branch
- `develop`: From `develop` branch
- `<version>`: From version tags (e.g., `v1.0.0`)
- `pr-<number>`: From pull requests

**Registry**: GitHub Container Registry (ghcr.io)

**Triggers**:
- Push to `main` or `develop` branches
- Version tags (e.g., `v*`)
- Pull requests targeting `main` or `develop` branches

### 7. Auto Release with Changesets - `release.yml`

**Purpose**: Automated versioning and releases using Changesets

**Features**:
- Automatic version bumping based on changesets
- Creates release PRs or publishes directly
- Generates GitHub releases
- Triggers Docker builds on release

**Requirements**:
- Changesets must be added to `frontend/.changeset/` directory
- NPM token for publishing (if publishing to npm)

**Triggers**:
- Push to `main` branch

**Permissions Required**:
- `contents: write` - To create releases and tags
- `pull-requests: write` - To create version PRs

### 8. Dependency Updates - `dependency-updates.yml`

**Purpose**: Automated dependency management

**Jobs**:
- **update-python-deps**: Updates Python dependencies via pip-tools
- **update-node-deps**: Updates Node.js dependencies via npm-check-updates
- **docker-image-updates**: Checks for Docker base image updates

**Triggers**:
- Scheduled: Every Monday at 2 AM UTC
- Manual trigger via workflow_dispatch

**Output**:
- Creates pull requests for dependency updates
- Labels: `dependencies`, `python`, `javascript`, `docker`

## Required Secrets

Configure the following secrets in your GitHub repository settings (`Settings > Secrets and variables > Actions`):

| Secret Name | Description | Required For |
|-------------|-------------|--------------|
| `GITHUB_TOKEN` | Automatically provided by GitHub | All workflows |
| `NPM_TOKEN` | npm registry authentication | Release workflow (if publishing to npm) |
| `CODECOV_TOKEN` | Codecov upload authentication | Python tests workflow |
| `SNYK_TOKEN` | Snyk security scanning | Frontend security workflow |

## How to Use Changesets for Releases

1. **Add a changeset** when making changes:
   ```bash
   cd frontend
   npx changeset
   ```

2. **Select the packages** that changed and the type of change:
   - `patch` - Bug fixes
   - `minor` - New features (backwards compatible)
   - `major` - Breaking changes

3. **Commit the changeset** file:
   ```bash
   git add .changeset/*.md
   git commit -m "docs(changeset): describe your change"
   ```

4. **When merged to main**, the release workflow will:
   - Create a version PR (if multiple changesets)
   - Or directly publish and create a GitHub release

## Branch Strategy

```
main          - Production-ready code, auto-releases from here
develop       - Integration branch, latest development
feature/*     - Feature branches, merge to develop
```

## Local Testing

### Run Python Tests Locally
```bash
cd ehazop_backend
pip install -r requirements.txt
pytest tests/ -v --cov=app
```

### Run Frontend Tests Locally
```bash
cd frontend
npm install
npm run lint
npm run type-check
npm run build
```

### Run Playwright Tests Locally
```bash
cd frontend
npx playwright install
npx playwright test
```

### Build Docker Images Locally
```bash
# Backend
docker build -t ehazop-backend:test ./ehazop_backend

# Frontend
docker build -t ehazop-frontend:test ./frontend

# Validate compose
docker compose config
```

## Troubleshooting

### Workflow Failures

1. **Check logs**: Navigate to Actions tab → Select workflow → Select run
2. **Re-run jobs**: Click "Re-run jobs" button for transient failures
3. **Debug locally**: Reproduce the issue using local testing commands above

### Common Issues

**Node version mismatch**: Ensure you're using Node 24 as specified in workflows

**Python version mismatch**: Ensure you're using Python 3.14 as specified

**Docker build failures**: Check Dockerfile and ensure all dependencies are available

**Changesets not working**: Verify `.changeset` directory exists and contains valid markdown files

## Maintenance

### Updating Workflow Files

1. Test changes in a feature branch first
2. Use `workflow_dispatch` trigger for manual testing
3. Monitor workflow runs for errors

### Adding New Workflows

1. Create new `.yml` file in `.github/workflows/`
2. Follow existing naming conventions
3. Add documentation to this file
4. Test thoroughly before merging

## Security Considerations

- Never commit secrets or tokens
- Use `continue-on-error: true` for non-critical security checks
- Review dependency update PRs before merging
- Keep workflow actions updated to latest versions
- Use pinned action versions (e.g., `@v4`) instead of `@latest`

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Changesets Documentation](https://github.com/changesets/changesets)
- [Playwright Documentation](https://playwright.dev/)
- [CodeQL Documentation](https://codeql.github.com/docs/)
- [Docker Buildx Documentation](https://docs.docker.com/buildx/working-with-buildx/)
