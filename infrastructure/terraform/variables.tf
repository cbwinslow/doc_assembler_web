# Oracle Cloud Infrastructure Variables
variable "oci_tenancy_ocid" {
  description = "OCID of the tenancy"
  type        = string
}

variable "oci_user_ocid" {
  description = "OCID of the user"
  type        = string
}

variable "oci_fingerprint" {
  description = "Fingerprint of the key"
  type        = string
}

variable "oci_private_key_path" {
  description = "Path to the private key file"
  type        = string
}

variable "oci_region" {
  description = "OCI region"
  type        = string
  default     = "us-ashburn-1"
}

variable "oci_compartment_id" {
  description = "OCID of the compartment"
  type        = string
}

# Cloudflare Variables
variable "cloudflare_api_token" {
  description = "Cloudflare API token"
  type        = string
  sensitive   = true
}

variable "cloudflare_zone_id" {
  description = "Cloudflare Zone ID for the domain"
  type        = string
}

variable "cloudflare_account_id" {
  description = "Cloudflare Account ID"
  type        = string
}

# General Variables
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "docassembler.com"
}

variable "subdomain" {
  description = "Subdomain for the application"
  type        = string
  default     = "app"
}

variable "app_server_count" {
  description = "Number of application servers"
  type        = number
  default     = 2
  
  validation {
    condition     = var.app_server_count >= 1 && var.app_server_count <= 10
    error_message = "App server count must be between 1 and 10."
  }
}

variable "ssh_public_key_path" {
  description = "Path to the SSH public key file"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

# Database Variables
variable "db_name" {
  description = "Database name"
  type        = string
  default     = "docassembler"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "docassembler_user"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

# Application Variables
variable "jwt_secret" {
  description = "JWT secret for authentication"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key for document processing"
  type        = string
  sensitive   = true
}

variable "cohere_api_key" {
  description = "Cohere API key for document processing"
  type        = string
  sensitive   = true
  default     = ""
}

variable "smtp_host" {
  description = "SMTP host for email notifications"
  type        = string
  default     = ""
}

variable "smtp_port" {
  description = "SMTP port"
  type        = number
  default     = 587
}

variable "smtp_username" {
  description = "SMTP username"
  type        = string
  default     = ""
}

variable "smtp_password" {
  description = "SMTP password"
  type        = string
  sensitive   = true
  default     = ""
}

# Monitoring Variables
variable "enable_monitoring" {
  description = "Enable monitoring and alerting"
  type        = bool
  default     = true
}

variable "enable_backups" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30
}

# Scaling Variables
variable "auto_scaling_enabled" {
  description = "Enable auto-scaling for application servers"
  type        = bool
  default     = true
}

variable "min_app_servers" {
  description = "Minimum number of application servers"
  type        = number
  default     = 2
}

variable "max_app_servers" {
  description = "Maximum number of application servers"
  type        = number
  default     = 10
}

variable "cpu_threshold" {
  description = "CPU threshold for auto-scaling (percentage)"
  type        = number
  default     = 70
}

variable "memory_threshold" {
  description = "Memory threshold for auto-scaling (percentage)"
  type        = number
  default     = 80
}

