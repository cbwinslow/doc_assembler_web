# Minimal configuration for testing deployment
# Replace with your actual credentials for production deployment

# Oracle Cloud Infrastructure Configuration
# These are placeholder values - replace with your actual OCI credentials
oci_tenancy_ocid      = "ocid1.tenancy.oc1..example"
oci_user_ocid         = "ocid1.user.oc1..example"
oci_fingerprint       = "example:fingerprint"
oci_private_key_path  = "~/.oci/oci_api_key.pem"
oci_region           = "us-ashburn-1"
oci_compartment_id   = "ocid1.compartment.oc1..example"

# Cloudflare Configuration
# These are placeholder values - replace with your actual Cloudflare credentials
cloudflare_api_token = "your-cloudflare-api-token"
cloudflare_zone_id   = "your-cloudflare-zone-id"
cloudflare_account_id = "your-cloudflare-account-id"

# Application Configuration
environment   = "dev"
domain_name   = "docassembler.test"
subdomain     = "app"
ssh_public_key_path = "~/.ssh/id_rsa.pub"

# Database Configuration
db_name     = "docassembler"
db_username = "docassembler_user"
db_password = "Temp1234!"  # Using rule-specified default password

# Application Secrets
jwt_secret     = "dev-jwt-secret-key-change-in-production"
openai_api_key = "your-openai-api-key"
cohere_api_key = ""  # Optional

# Email Configuration (Optional for dev)
smtp_host     = ""
smtp_port     = 587
smtp_username = ""
smtp_password = ""

# Scaling Configuration (Always Free Tier - single server)
app_server_count      = 1
auto_scaling_enabled  = false
min_app_servers       = 1
max_app_servers       = 1  # Always Free Tier limited to 2 instances total
cpu_threshold         = 80
memory_threshold      = 85

# Monitoring and Backup
enable_monitoring        = false
enable_backups          = false
backup_retention_days   = 7

