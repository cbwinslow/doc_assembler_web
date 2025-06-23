# Load Balancer removed for Always Free Tier
# Using direct access to application server

# Application Server Outputs
output "app_server_public_ips" {
  description = "Public IP addresses of application servers"
  value       = oci_core_instance.docassembler_app_server[*].public_ip
}

output "app_server_private_ips" {
  description = "Private IP addresses of application servers"
  value       = oci_core_instance.docassembler_app_server[*].private_ip
}

output "app_server_ids" {
  description = "OCIDs of application servers"
  value       = oci_core_instance.docassembler_app_server[*].id
}

# Database Server Outputs
output "db_server_private_ip" {
  description = "Private IP address of database server"
  value       = oci_core_instance.docassembler_db_server.private_ip
}

output "db_server_id" {
  description = "OCID of database server"
  value       = oci_core_instance.docassembler_db_server.id
}

# Network Outputs
output "vcn_id" {
  description = "OCID of the VCN"
  value       = oci_core_vcn.docassembler_vcn.id
}

output "public_subnet_id" {
  description = "OCID of the public subnet"
  value       = oci_core_subnet.docassembler_public_subnet.id
}

output "private_subnet_id" {
  description = "OCID of the private subnet"
  value       = oci_core_subnet.docassembler_private_subnet.id
}

# Object Storage Outputs
output "object_storage_bucket_name" {
  description = "Name of the object storage bucket"
  value       = oci_objectstorage_bucket.docassembler_storage.name
}

output "object_storage_namespace" {
  description = "Object storage namespace"
  value       = data.oci_objectstorage_namespace.ns.namespace
}

# DNS Outputs
output "application_url" {
  description = "URL of the application"
  value       = "https://${var.subdomain}.${var.domain_name}"
}

output "api_url" {
  description = "URL of the API"
  value       = "https://api.${var.domain_name}"
}

# SSH Connection Strings
output "ssh_connection_app_servers" {
  description = "SSH connection strings for application servers"
  value = [
    for i, ip in oci_core_instance.docassembler_app_server[*].public_ip :
    "ssh -i ~/.ssh/id_rsa opc@${ip}"
  ]
}

output "ssh_connection_db_server" {
  description = "SSH connection string for database server (via bastion)"
  value       = "ssh -i ~/.ssh/id_rsa -J opc@${oci_core_instance.docassembler_app_server[0].public_ip} opc@${oci_core_instance.docassembler_db_server.private_ip}"
}

# Environment Information
output "environment" {
  description = "Deployment environment"
  value       = var.environment
}

output "region" {
  description = "OCI region"
  value       = var.oci_region
}

# Deployment Commands
output "deployment_commands" {
  description = "Commands to deploy the application"
  value = {
    deploy_backend = "ansible-playbook -i inventory/production.yml playbooks/deploy-backend.yml"
    deploy_frontend = "ansible-playbook -i inventory/production.yml playbooks/deploy-frontend.yml"
    deploy_database = "ansible-playbook -i inventory/production.yml playbooks/setup-database.yml"
    setup_ssl = "ansible-playbook -i inventory/production.yml playbooks/setup-ssl.yml"
  }
}

# Health Check URLs
output "health_check_urls" {
  description = "Health check URLs for monitoring"
  value = {
    app_server = "http://${oci_core_instance.docassembler_app_server[0].public_ip}/api/health"
    application = "https://${var.subdomain}.${var.domain_name}/api/health"
    api = "https://api.${var.domain_name}/health"
  }
}

# Monitoring Information
output "monitoring_endpoints" {
  description = "Monitoring and metrics endpoints"
  value = {
    prometheus = "https://prometheus.${var.domain_name}"
    grafana = "https://grafana.${var.domain_name}"
    logs = "https://logs.${var.domain_name}"
  }
}

