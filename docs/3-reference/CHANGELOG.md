# Changelog

All notable changes to the Emotion CT Pipeline will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Complete Phase 2 Enhanced Pipeline infrastructure
- Complete Phase 3 Production Pipeline infrastructure

---

## [1.1.0] - 2026-03-08

### Added
- **Docker Infrastructure**: docker-compose-infra.yml với đầy đủ services
  - Argilla UI (human labeling interface)
  - MLflow (experiment tracking)
  - PostgreSQL (database)
  - Elasticsearch (search engine)
  - Redis (job queue)
  - MinIO (S3-compatible storage)

### Changed
- Update port configurations để tránh conflict
- Cập nhật .env với MLFLOW_PORT=5010

---

## [1.0.0] - 2026-03-08

### Added

#### Phase 1: Core Pipeline
- CSV data collection from Datadog exports
- AI labeling with GPT-4o-mini via Distilabel
- 3-way agreement logic (5 cases)
- Train/val/test split (70/15/15 stratified)
- LoRA fine-tuning with TRL (Qwen2.5-1.5B-Instruct)
- AWQ 4-bit quantization
- Sklearn evaluation metrics (accuracy, F1 macro, per-class F1, confusion matrix)
- Promotion decision based on thresholds
- Unit tests for domain logic

#### Phase 2: Enhanced Pipeline
- **Argilla Integration**: Human review workflow with `review` command
- **HuggingFace Hub**: Dataset and model publishing
  - `push-dataset` command
  - Model card generation
- **MLflow Integration**: Experiment tracking and model registry
  - Training metrics logging
  - Evaluation metrics logging
  - Model versioning
- **Langfuse Observability**: Tracing and cost tracking
  - Langfuse tracer for pipeline steps
  - Cost tracker for API usage
  - Notification client (Slack/Discord)

#### Phase 3: Production Pipeline
- **GitHub Actions Workflow**: Automated pipeline
  - Scheduled weekly (Monday 2 AM UTC)
  - Manual dispatch support
  - Slack notifications
- **Drift Monitoring**: Data and performance drift detection
  - DataDriftDetector (KL divergence, PSI, chi-squared)
  - PerformanceDriftDetector (accuracy/F1 trends)
  - BaselineStore for historical metrics
  - `monitor-drift` command
- **Canary Deployment**: Gradual rollout and rollback
  - HealthChecker for monitoring
  - `canary-deploy` command
  - `rollback` command
  - MLflow staging integration

### Changed
- Updated Plan.md with complete phase status
- Improved CLI with new commands

### Fixed
- Model accuracy improved through proper evaluation

### Known Issues
- Initial dataset size small (697 train samples) causing lower accuracy
- Class imbalance (happy 35%, thinking 31%, calm 24% dominate)

---

## [0.1.0] - 2026-03-06

### Added
- Initial project setup
- Clean Architecture structure
- Domain layer (entities, value objects, services)
- Application layer (use cases)
- Infrastructure layer (loaders, trainers, evaluators)
- Basic CLI commands (collect, label, build, train, evaluate, decide)
- Configuration files
- Documentation (PRD, HLD, LLD, Plan)

---

## Version History

| Version | Date | Status |
|---------|------|--------|
| 1.1.0 | 2026-03-08 | Docker Infrastructure + Full Pipeline |
| 1.0.0 | 2026-03-08 | Complete Phases 1-3 |
| 0.1.0 | 2026-03-06 | Initial release (Phase 1) |

---

## Breaking Changes

None yet - this is the first stable release.

---

## Deprecations

None yet.

---

*For older versions, see the git history.*
