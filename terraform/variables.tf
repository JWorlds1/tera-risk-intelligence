# =============================================================================
# OpenStack Authentifizierung (aus OpenRC)
# =============================================================================

variable "auth_url" {
  description = "OpenStack Authentication URL"
  type        = string
  default     = "https://h-da.cloud:13000"
}

variable "application_credential_id" {
  description = "OpenStack Application Credential ID"
  type        = string
  default     = "ba44dda4814e443faba80ae101d704a8"
}

variable "application_credential_secret" {
  description = "OpenStack Application Credential Secret"
  type        = string
  sensitive   = true
  default     = "Wesen"
}

variable "region" {
  description = "OpenStack Region"
  type        = string
  default     = "eu-central"
}

# =============================================================================
# Server Konfiguration
# =============================================================================

variable "server_name" {
  description = "Name der zu erstellenden VM Instanz"
  type        = string
  default     = "geospatial-server"
}

variable "image_name" {
  description = "Name des OS Images (z.B. Ubuntu 22.04)"
  type        = string
  default     = "Ubuntu 22.04"
}

variable "flavor_name" {
  description = "Flavor/Instanz-Größe (CPU, RAM, Disk)"
  type        = string
  default     = "m1.small"
}

variable "network_name" {
  description = "Name des Netzwerks"
  type        = string
  default     = "private-network"
}

variable "security_groups" {
  description = "Liste der Security Groups"
  type        = list(string)
  default     = ["default"]
}

# =============================================================================
# SSH Konfiguration
# =============================================================================

variable "ssh_key_name" {
  description = "Name des SSH Key-Pairs in OpenStack"
  type        = string
  default     = "geospatial-key"
}

variable "generate_ssh_key" {
  description = "Soll ein neuer SSH Key generiert werden?"
  type        = bool
  default     = true
}

variable "existing_public_key" {
  description = "Falls vorhanden: Pfad zum existierenden public SSH key"
  type        = string
  default     = ""
}

# =============================================================================
# Floating IP Konfiguration
# =============================================================================

variable "assign_floating_ip" {
  description = "Soll eine Floating IP zugewiesen werden?"
  type        = bool
  default     = true
}

variable "floating_ip_pool" {
  description = "Name des Floating IP Pools"
  type        = string
  default     = "public"
}

# =============================================================================
# User Data / Cloud-Init
# =============================================================================

variable "user_data_enabled" {
  description = "Soll Cloud-Init User Data verwendet werden?"
  type        = bool
  default     = true
}

