variable "subscription_id" {
  description = "Azure subscription ID where live test resources will be provisioned."
  type        = string
}

variable "tenant_id" {
  description = "Azure Active Directory tenant ID."
  type        = string
}

variable "location" {
  description = "Azure region for the live test resources."
  type        = string
  default     = "japaneast"
}

variable "environment" {
  description = "Short environment name used in resource tagging (e.g., dev, ci)."
  type        = string
  default     = "ci"
}

variable "name_prefix" {
  description = "Prefix used for Azure resources. Should be 3-10 lowercase characters."
  type        = string
}

variable "test_principal_object_id" {
  description = "Object ID of the service principal or managed identity used by the live tests."
  type        = string
}

variable "operator_object_ids" {
  description = "Optional list of Azure AD object IDs granted read access for manual verification."
  type        = list(string)
  default     = []
}

variable "sample_secret_name" {
  description = "Name of the sample secret created for live tests."
  type        = string
  default     = "envresolve-live-secret"
}

variable "sample_secret_value" {
  description = "Value stored in the sample secret."
  type        = string
  default     = "replace-me"
  sensitive   = true
}

variable "key_vault_sku" {
  description = "Azure Key Vault SKU (Standard or Premium)."
  type        = string
  default     = "standard"
}

variable "enable_purge_protection" {
  description = "Whether to enable purge protection on the Key Vault."
  type        = bool
  default     = false
}

variable "soft_delete_retention_days" {
  description = "Number of days to retain soft-deleted secrets."
  type        = number
  default     = 7
}

variable "public_network_access_enabled" {
  description = "Whether public network access is enabled for the Key Vault."
  type        = bool
  default     = true
}

variable "enable_rbac_authorization" {
  description = "Enable Azure RBAC instead of access policies."
  type        = bool
  default     = false
}

variable "network_acls" {
  description = "Network ACL configuration for the Key Vault."
  type = object({
    default_action = string
    bypass         = string
    ip_rules       = list(string)
  })
  default = {
    default_action = "Allow"  # Use "Allow" for dev/CI; override to "Deny" + ip_rules for production
    bypass         = "AzureServices"
    ip_rules       = []
  }
}

variable "tags" {
  description = "Tags applied to all live test resources."
  type        = map(string)
  default     = {}
}
