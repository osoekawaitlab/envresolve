# Live Test Infrastructure

Terraform manifests in this directory provision the Azure resources required to run the live Key Vault tests. The module is intentionally minimal: a single resource group, one Key Vault, and a sample secret that the test suite reads.

## Prerequisites

- Terraform `>= 1.5`
- Azure CLI logged in with access to the target subscription, or environment variables that provide ARM credentials.
- An Azure AD service principal (or managed identity) that executes the live tests. Capture its **object ID** and grant it access by populating `test_principal_object_id`.
- Optional: object IDs for human operators who need read-only access while debugging (`operator_object_ids`).

## Configuration

1. Copy `terraform.tfvars.example` to `terraform.tfvars` and fill in the required values:

   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

   Required inputs:

   - `subscription_id`
   - `tenant_id`
   - `name_prefix` (lowercase, 3–10 characters; used in resource names)
   - `test_principal_object_id`

   The remaining variables have sensible defaults but can be customized for network ACLs, tags, and secret contents.

2. (Optional) Configure remote backend for state storage. For local development, local state is fine. For team/CI use, configure a remote backend:

   ```bash
   cp backend.tf.example backend.tf
   # Edit backend.tf with your Azure Storage account details
   terraform init -migrate-state
   ```

   See `backend.tf.example` for detailed instructions.

## Usage

### Initial Setup

```bash
terraform init
terraform plan
terraform apply
```

### Setting Up Test Environment

After applying terraform, export outputs as environment variables:

```bash
# Automated method (from project root)
source scripts/setup_live_tests.sh

# Manual method (from infra/terraform directory)
export ENVRESOLVE_LIVE_KEY_VAULT_NAME=$(terraform output -raw key_vault_name)
export ENVRESOLVE_LIVE_SECRET_NAME=$(terraform output -raw sample_secret_name)
export ENVRESOLVE_LIVE_SECRET_VALUE=$(terraform output -raw sample_secret_value)
export ENVRESOLVE_LIVE_SECRET_VERSION=$(terraform output -raw sample_secret_version)
```

### Cleanup

When no longer needed:

```bash
terraform destroy
```
