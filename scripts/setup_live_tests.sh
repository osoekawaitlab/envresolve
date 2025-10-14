#!/bin/bash
# Helper script to export terraform outputs as environment variables for live tests
#
# Usage:
#   source scripts/setup_live_tests.sh
#
# This script must be sourced (not executed) to export variables to the current shell:
#   source scripts/setup_live_tests.sh    # Correct
#   ./scripts/setup_live_tests.sh         # Won't work (variables not exported to parent)
#
# Prerequisites:
#   - Terraform must be initialized and applied in infra/terraform/
#   - Run: cd infra/terraform && terraform apply

set -eo pipefail

# Get script directory (handle both source and direct execution)
if [ -n "${BASH_SOURCE:-}" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
fi
TERRAFORM_DIR="${SCRIPT_DIR}/../infra/terraform"

# Check if terraform directory exists
if [ ! -d "${TERRAFORM_DIR}" ]; then
    echo "Error: Terraform directory not found at ${TERRAFORM_DIR}" >&2
    return 1 2>/dev/null || exit 1
fi

# Check if terraform state exists
if [ ! -f "${TERRAFORM_DIR}/terraform.tfstate" ]; then
    echo "Error: Terraform state not found. Run 'terraform apply' first." >&2
    echo "  cd infra/terraform && terraform apply" >&2
    return 1 2>/dev/null || exit 1
fi

# Navigate to terraform directory
cd "${TERRAFORM_DIR}"

# Export environment variables from terraform outputs
export ENVRESOLVE_LIVE_KEY_VAULT_NAME=$(terraform output -raw key_vault_name)
export ENVRESOLVE_LIVE_SECRET_NAME=$(terraform output -raw sample_secret_name)
export ENVRESOLVE_LIVE_SECRET_VALUE=$(terraform output -raw sample_secret_value)
export ENVRESOLVE_LIVE_SECRET_VERSION=$(terraform output -raw sample_secret_version)

# Return to original directory
cd - > /dev/null

echo "✓ Live test environment variables configured:"
echo "  ENVRESOLVE_LIVE_KEY_VAULT_NAME=${ENVRESOLVE_LIVE_KEY_VAULT_NAME}"
echo "  ENVRESOLVE_LIVE_SECRET_NAME=${ENVRESOLVE_LIVE_SECRET_NAME}"
echo "  ENVRESOLVE_LIVE_SECRET_VERSION=${ENVRESOLVE_LIVE_SECRET_VERSION}"
echo "  ENVRESOLVE_LIVE_SECRET_VALUE=<redacted>"
echo ""
echo "You can now run live tests:"
echo "  pytest -m live"
echo "  nox -s tests_live"
