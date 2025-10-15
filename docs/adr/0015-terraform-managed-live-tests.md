# Architecture Decision Record (ADR)

## Title

Manage Azure Live Test Infrastructure with Terraform

## Status

Accepted

## Date

2025-10-15

## Context

envresolve includes optional support for Azure Key Vault. Unit and end-to-end tests currently use mocks to avoid external dependencies, but they cannot guarantee the integration behaves correctly against real Azure services. We also want a reproducible way to provision the required Azure resources (resource group, Key Vault, sample secrets) for contributors and CI without manual setup.

Key considerations:

- Ensure infra can be created and destroyed deterministically for on-demand live tests.
- Capture secrets and configuration outputs so the pytest suite can authenticate and assert on real data.
- Keep costs low (single Key Vault, sample secret) and enable quick cleanup.
- Avoid leaking credentials by relying on standard Azure service principal flows and environment variables.

## Decision

Adopt Terraform to manage live-test infrastructure and introduce an `azure and live` pytest marker for the real Azure integration tests. Provisioning is documented under `infra/terraform`, including helper Nox sessions (`terraform_plan_live`, `terraform_apply_live`, `terraform_destroy_live`) that wrap common operations. Terraform outputs supply the values consumed by live tests via environment variables such as `ENVRESOLVE_LIVE_KEY_VAULT_NAME` and `ENVRESOLVE_LIVE_SECRET_VALUE`.

Live tests are opt-in: they skip automatically when configuration variables or Azure credentials are absent. A dedicated CI workflow (manual/cron) can apply Terraform, run the live suite, and tear down the resources afterwards.

## Rationale

- **Repeatability**: Terraform defines the full resource graph, removing ad-hoc setup steps.
- **Safety**: Helper sessions ensure `terraform destroy` is easy to run and can be wired into CI cleanup even on failures.
- **Isolation**: Live tests sit behind explicit pytest markers, so day-to-day development remains fast and free from cloud dependencies.
- **Documentation**: A focused user guide page explains the workflow for both local and CI executions, lowering the barrier for contributors.

## Consequences

### Positive

- Real Azure regressions are caught before release.
- All required secrets and outputs are version-controlled and discoverable.
- CI pipelines can gate live tests separately from the core suite.

### Negative

- Terraform and Azure CLI become prerequisites for running the live suite.
- Sensitive Terraform outputs must be handled carefully (e.g., stored in CI secrets rather than printed to logs).
- Additional maintenance is required to keep infrastructure definitions aligned with evolving test needs.

## Alternatives Considered

1. **Manual Azure setup instructions only**
   - *Rejected*: Too error-prone; contributors might misconfigure permissions or forget cleanup.

2. **Dynamic resource creation inside pytest fixtures**
   - *Rejected*: Implementing provisioning in Python would duplicate Terraform features, complicate teardown, and intertwine infrastructure logic with tests.

3. **Always rely on mocked tests**
   - *Rejected*: Mocks cannot detect changes in Azure SDK behavior, identity requirements, or Key Vault service quirks.

## Follow-Up Actions

- Wire the Terraform workflow into CI (manual dispatch or scheduled job).
- Consider adding Key Vault network ACL configuration once CI egress addresses are known.
- Expand live coverage as new Azure providers or features are added.
