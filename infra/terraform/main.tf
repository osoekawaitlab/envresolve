terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.112.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.6.0"
    }
  }
}

provider "azurerm" {
  features {}

  subscription_id = var.subscription_id
}

resource "random_string" "suffix" {
  length  = 5
  upper   = false
  lower   = true
  numeric = true
  special = false
}

locals {
  resource_group_name = "${var.name_prefix}-${var.environment}-rg"

  # Key Vault name generation logic:
  # 1. Concatenate: name_prefix + environment + random_suffix (e.g., "envresolve-ci-abc12")
  # 2. Replace: Remove non-alphanumeric chars except hyphens (Azure KV naming rule)
  # 3. Truncate: Limit to 24 chars (Azure KV max length)
  # Result example: "envresolveciabc12" (hyphens removed to maximize name space)
  key_vault_name = substr(replace("${var.name_prefix}${var.environment}${random_string.suffix.result}", "/[^a-z0-9-]/", ""), 0, 24)

  tags = merge(var.tags, { "envresolve:environment" = var.environment })
}

resource "azurerm_resource_group" "live_tests" {
  name     = local.resource_group_name
  location = var.location

  tags = local.tags
}

resource "azurerm_key_vault" "live_tests" {
  name                          = local.key_vault_name
  resource_group_name           = azurerm_resource_group.live_tests.name
  location                      = azurerm_resource_group.live_tests.location
  tenant_id                     = var.tenant_id
  sku_name                      = var.key_vault_sku
  purge_protection_enabled      = var.enable_purge_protection
  soft_delete_retention_days    = var.soft_delete_retention_days
  public_network_access_enabled = var.public_network_access_enabled
  rbac_authorization_enabled    = var.enable_rbac_authorization

  access_policy {
    tenant_id = var.tenant_id
    object_id = var.test_principal_object_id

    secret_permissions = [
      "Backup",
      "Delete",
      "Get",
      "List",
      "Purge",
      "Recover",
      "Restore",
      "Set",
    ]
  }

  dynamic "access_policy" {
    for_each = toset(var.operator_object_ids)

    content {
      tenant_id = var.tenant_id
      object_id = access_policy.value

      secret_permissions = [
        "Get",
        "List",
      ]
    }
  }

  network_acls {
    default_action = var.network_acls.default_action
    bypass         = var.network_acls.bypass
    ip_rules       = var.network_acls.ip_rules
  }

  tags = local.tags
}

# Role assignments for RBAC authorization mode
# When enable_rbac_authorization is true, access policies are ignored
# and Azure RBAC must be used instead

resource "azurerm_role_assignment" "test_principal_secrets_officer" {
  count                = var.enable_rbac_authorization ? 1 : 0
  scope                = azurerm_key_vault.live_tests.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = var.test_principal_object_id
}

resource "azurerm_role_assignment" "operators_secrets_user" {
  for_each             = var.enable_rbac_authorization ? toset(var.operator_object_ids) : []
  scope                = azurerm_key_vault.live_tests.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = each.value
}

resource "azurerm_key_vault_secret" "sample" {
  name         = var.sample_secret_name
  value        = var.sample_secret_value
  key_vault_id = azurerm_key_vault.live_tests.id
  content_type = "text/plain"

  tags = local.tags

  # Role assignments must be in place before creating secrets in RBAC mode
  depends_on = [
    azurerm_role_assignment.test_principal_secrets_officer,
  ]
}
