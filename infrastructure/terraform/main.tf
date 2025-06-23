terraform {
  required_version = ">= 1.0"
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 4.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }

  # Local backend for initial setup
  # To use remote backend, configure after OCI credentials are set up
  # backend "s3" {
  #   bucket                      = "docassembler-terraform-state"
  #   key                         = "infrastructure/terraform.tfstate"
  #   region                      = "us-ashburn-1"
  #   endpoint                    = "https://objectstorage.us-ashburn-1.oraclecloud.com"
  #   skip_credentials_validation = true
  #   skip_metadata_api_check     = true
  #   skip_region_validation      = true
  #   force_path_style           = true
  # }
}

# Configure Oracle Cloud provider
provider "oci" {
  tenancy_ocid         = var.oci_tenancy_ocid
  user_ocid           = var.oci_user_ocid
  fingerprint         = var.oci_fingerprint
  private_key_path    = var.oci_private_key_path
  region              = var.oci_region
}

# Configure Cloudflare provider
provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

# Data sources
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.oci_compartment_id
}

data "oci_core_images" "oracle_linux" {
  compartment_id           = var.oci_compartment_id
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  shape                   = "VM.Standard.E2.1.Micro"  # Always Free Tier
  sort_by                 = "TIMECREATED"
  sort_order              = "DESC"
}

# Create VCN (Virtual Cloud Network)
resource "oci_core_vcn" "docassembler_vcn" {
  compartment_id = var.oci_compartment_id
  cidr_blocks    = ["10.0.0.0/16"]
  display_name   = "docassembler-vcn"
  dns_label      = "docassembler"

  freeform_tags = {
    Environment = var.environment
    Project     = "DocAssembler"
  }
}

# Internet Gateway
resource "oci_core_internet_gateway" "docassembler_igw" {
  compartment_id = var.oci_compartment_id
  vcn_id         = oci_core_vcn.docassembler_vcn.id
  display_name   = "docassembler-igw"
  enabled        = true

  freeform_tags = {
    Environment = var.environment
    Project     = "DocAssembler"
  }
}

# Route Table
resource "oci_core_route_table" "docassembler_route_table" {
  compartment_id = var.oci_compartment_id
  vcn_id         = oci_core_vcn.docassembler_vcn.id
  display_name   = "docassembler-route-table"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.docassembler_igw.id
  }

  freeform_tags = {
    Environment = var.environment
    Project     = "DocAssembler"
  }
}

# Security Lists
resource "oci_core_security_list" "docassembler_security_list" {
  compartment_id = var.oci_compartment_id
  vcn_id         = oci_core_vcn.docassembler_vcn.id
  display_name   = "docassembler-security-list"

  # Egress rules
  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
  }

  # Ingress rules
  ingress_security_rules {
    # SSH
    protocol = "6" # TCP
    source   = "0.0.0.0/0"

    tcp_options {
      min = 22
      max = 22
    }
  }

  ingress_security_rules {
    # HTTP
    protocol = "6" # TCP
    source   = "0.0.0.0/0"

    tcp_options {
      min = 80
      max = 80
    }
  }

  ingress_security_rules {
    # HTTPS
    protocol = "6" # TCP
    source   = "0.0.0.0/0"

    tcp_options {
      min = 443
      max = 443
    }
  }

  ingress_security_rules {
    # Backend API
    protocol = "6" # TCP
    source   = "10.0.0.0/16"

    tcp_options {
      min = 5000
      max = 5000
    }
  }

  ingress_security_rules {
    # PostgreSQL
    protocol = "6" # TCP
    source   = "10.0.0.0/16"

    tcp_options {
      min = 5432
      max = 5432
    }
  }

  ingress_security_rules {
    # Redis
    protocol = "6" # TCP
    source   = "10.0.0.0/16"

    tcp_options {
      min = 6379
      max = 6379
    }
  }

  freeform_tags = {
    Environment = var.environment
    Project     = "DocAssembler"
  }
}

# Public Subnet
resource "oci_core_subnet" "docassembler_public_subnet" {
  compartment_id      = var.oci_compartment_id
  vcn_id              = oci_core_vcn.docassembler_vcn.id
  cidr_block          = "10.0.1.0/24"
  display_name        = "docassembler-public-subnet"
  dns_label           = "public"
  route_table_id      = oci_core_route_table.docassembler_route_table.id
  security_list_ids   = [oci_core_security_list.docassembler_security_list.id]
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name

  freeform_tags = {
    Environment = var.environment
    Project     = "DocAssembler"
  }
}

# Private Subnet for Database
resource "oci_core_subnet" "docassembler_private_subnet" {
  compartment_id             = var.oci_compartment_id
  vcn_id                     = oci_core_vcn.docassembler_vcn.id
  cidr_block                 = "10.0.2.0/24"
  display_name               = "docassembler-private-subnet"
  dns_label                  = "private"
  prohibit_public_ip_on_vnic = true
  availability_domain        = data.oci_identity_availability_domains.ads.availability_domains[0].name

  freeform_tags = {
    Environment = var.environment
    Project     = "DocAssembler"
  }
}

# Load Balancer removed - not included in Always Free Tier
# Using direct access to application server instead
# For production, consider using a paid load balancer or implement software load balancing

# Application Server Instances (Always Free Tier)
resource "oci_core_instance" "docassembler_app_server" {
  count               = var.app_server_count
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  compartment_id      = var.oci_compartment_id
  display_name        = "docassembler-app-${count.index + 1}"
  shape               = "VM.Standard.E2.1.Micro"  # Always Free Tier

  # No shape_config needed for Always Free Tier - fixed 1 OCPU, 1GB RAM

  create_vnic_details {
    subnet_id        = oci_core_subnet.docassembler_public_subnet.id
    assign_public_ip = true
    display_name     = "docassembler-app-${count.index + 1}-vnic"
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.oracle_linux.images[0].id
  }

  metadata = {
    ssh_authorized_keys = file(var.ssh_public_key_path)
    user_data = base64encode(templatefile("${path.module}/cloud-init.yaml", {
      environment = var.environment
      domain_name = var.domain_name
      ssh_public_key = file(var.ssh_public_key_path)
    }))
  }

  freeform_tags = {
    Environment = var.environment
    Project     = "DocAssembler"
    Role        = "AppServer"
  }
}

# Database Server Instance (Always Free Tier)
resource "oci_core_instance" "docassembler_db_server" {
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  compartment_id      = var.oci_compartment_id
  display_name        = "docassembler-db"
  shape               = "VM.Standard.E2.1.Micro"  # Always Free Tier

  # No shape_config needed for Always Free Tier - fixed 1 OCPU, 1GB RAM

  create_vnic_details {
    subnet_id        = oci_core_subnet.docassembler_private_subnet.id
    assign_public_ip = false
    display_name     = "docassembler-db-vnic"
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.oracle_linux.images[0].id
  }

  metadata = {
    ssh_authorized_keys = file(var.ssh_public_key_path)
    user_data = base64encode(templatefile("${path.module}/cloud-init-db.yaml", {
      environment = var.environment
    }))
  }

  freeform_tags = {
    Environment = var.environment
    Project     = "DocAssembler"
    Role        = "Database"
  }
}

# Object Storage Bucket
resource "oci_objectstorage_bucket" "docassembler_storage" {
  compartment_id = var.oci_compartment_id
  name           = "docassembler-${var.environment}-storage"
  namespace      = data.oci_objectstorage_namespace.ns.namespace

  access_type    = "NoPublicAccess"
  storage_tier   = "Standard"
  versioning     = "Enabled"

  freeform_tags = {
    Environment = var.environment
    Project     = "DocAssembler"
  }
}

data "oci_objectstorage_namespace" "ns" {
  compartment_id = var.oci_compartment_id
}

# Load balancer components removed for Always Free Tier
# Direct access to application server will be used instead

