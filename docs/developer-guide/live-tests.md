# Live Azure Tests

This project includes optional integration tests that run against a real Azure Key Vault instance. These tests are marked with the `live` and `azure` pytest markers.

## Why Live Tests?

While most of the application can be tested using mocked SDKs (E2E tests), live tests provide an extra layer of confidence by verifying the integration with the actual Azure service. This helps catch issues related to authentication, permissions, or unexpected API changes.

## Setup Instructions

Running these tests requires one-time setup using Terraform to provision the necessary Azure resources.

### 1. Install Tools

Ensure you have [Terraform](https://learn.hashicorp.com/tutorials/terraform/install-cli) and the [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed.

### 2. Configure Terraform

Navigate to the Terraform directory:

```bash
cd infra/terraform
```

Create a `terraform.tfvars` file from the example:

```bash
cp terraform.tfvars.example terraform.tfvars
```

**Edit `terraform.tfvars`** and fill in your Azure subscription details and desired resource names.

### 3. Provision Resources

Initialize and apply the Terraform configuration:

```bash
terraform init
terraform apply
```

This will create an Azure Resource Group, a Key Vault, and a secret to be used for testing.

## Running the Tests

### 1. Authenticate

Log in to Azure via the CLI:

```bash
az login
```

### 2. Set Environment Variables

Run the setup script to export the Key Vault details as environment variables for the test runner:

```bash
source scripts/setup_live_tests.sh
```

This script reads the Terraform output and sets `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, etc.

### 3. Execute Tests

Finally, run the live tests using `nox`:

```bash
nox -s tests_live
```

## Cleaning Up

To avoid incurring costs, destroy the Azure resources when you are done testing:

```bash
cd infra/terraform
terraform destroy
```
