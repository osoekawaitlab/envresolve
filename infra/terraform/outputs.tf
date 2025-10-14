output "resource_group_name" {
  description = "Name of the resource group supporting the live tests."
  value       = azurerm_resource_group.live_tests.name
}

output "key_vault_name" {
  description = "Azure Key Vault name provisioned for live tests."
  value       = azurerm_key_vault.live_tests.name
}

output "key_vault_uri" {
  description = "URI of the Azure Key Vault."
  value       = azurerm_key_vault.live_tests.vault_uri
}

output "sample_secret_name" {
  description = "Name of the sample secret created for live testing."
  value       = azurerm_key_vault_secret.sample.name
}

output "sample_secret_version" {
  description = "Version identifier of the sample secret."
  value       = azurerm_key_vault_secret.sample.version
}

output "sample_secret_value" {
  description = "Value stored in the sample secret. Use for local verification only."
  value       = azurerm_key_vault_secret.sample.value
  sensitive   = true
}
