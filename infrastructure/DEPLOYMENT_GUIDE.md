# DocAssembler Infrastructure Deployment Guide

This guide will walk you through deploying the complete DocAssembler infrastructure on Oracle Cloud Infrastructure (OCI) with Cloudflare integration.

## Prerequisites

1. **Oracle Cloud Infrastructure (OCI) Account**
   - Free tier account is sufficient for testing
   - Access to compute instances, networking, and storage

2. **Cloudflare Account**
   - Domain registered with Cloudflare
   - API access enabled

3. **Required Tools**
   - Terraform >= 1.0
   - Git
   - SSH client
   - OCI CLI (optional but recommended)

## Step 1: OCI Credentials Setup

### 1.1 Generate API Key Pair

```bash
# Create OCI config directory
mkdir -p ~/.oci

# Generate API key pair
openssl genrsa -out ~/.oci/oci_api_key.pem 2048
openssl rsa -pubout -in ~/.oci/oci_api_key.pem -out ~/.oci/oci_api_key_public.pem
```

### 1.2 Add Public Key to OCI Console

1. Log into OCI Console
2. Go to User Settings → API Keys
3. Click "Add API Key"
4. Upload the public key file (`~/.oci/oci_api_key_public.pem`)
5. Copy the fingerprint value

### 1.3 Get Required OCIDs

From the OCI Console, collect:
- **Tenancy OCID**: Go to Administration → Tenancy Details
- **User OCID**: Go to User Settings → User Information
- **Compartment OCID**: Go to Identity → Compartments

## Step 2: Cloudflare Setup

### 2.1 Get API Token

1. Log into Cloudflare Dashboard
2. Go to My Profile → API Tokens
3. Create Token with permissions:
   - Zone:Zone:Read
   - Zone:DNS:Edit
   - Account:Cloudflare Tunnel:Edit

### 2.2 Get Zone ID

1. Go to your domain in Cloudflare Dashboard
2. Copy the Zone ID from the right sidebar

## Step 3: Configure Terraform Variables

### 3.1 Create terraform.tfvars

```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
```

### 3.2 Edit terraform.tfvars

Replace the placeholder values with your actual credentials:

```hcl
# Oracle Cloud Infrastructure Configuration
oci_tenancy_ocid      = "ocid1.tenancy.oc1..your-actual-tenancy-ocid"
oci_user_ocid         = "ocid1.user.oc1..your-actual-user-ocid"
oci_fingerprint       = "your-actual-key-fingerprint"
oci_private_key_path  = "~/.oci/oci_api_key.pem"
oci_region           = "us-ashburn-1"
oci_compartment_id   = "ocid1.compartment.oc1..your-actual-compartment-ocid"

# Cloudflare Configuration
cloudflare_api_token = "your-actual-cloudflare-api-token"
cloudflare_zone_id   = "your-actual-cloudflare-zone-id"
cloudflare_account_id = "your-actual-cloudflare-account-id"

# Application Configuration
environment   = "prod"
domain_name   = "yourdomain.com"
subdomain     = "app"

# Database Configuration
db_name     = "docassembler"
db_username = "docassembler_user"
db_password = "YourSecurePassword123!"

# Application Secrets
jwt_secret     = "your-secure-jwt-secret-key"
openai_api_key = "your-openai-api-key"
```

## Step 4: Deploy Infrastructure

### 4.1 Run Deployment Script

```bash
# Make script executable
chmod +x infrastructure/scripts/deploy.sh

# Run deployment
./infrastructure/scripts/deploy.sh
```

### 4.2 Manual Deployment (Alternative)

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Plan deployment
terraform plan -out=tfplan

# Apply deployment
terraform apply tfplan
```

## Step 5: Post-Deployment Configuration

### 5.1 Wait for Initialization

The cloud-init scripts will take 5-10 minutes to complete. You can monitor progress by:

```bash
# SSH into application server
ssh -i ~/.ssh/id_rsa opc@<app_server_public_ip>

# Check cloud-init status
sudo cloud-init status --wait

# View cloud-init logs
sudo tail -f /var/log/cloud-init-output.log
```

### 5.2 Configure SSL Certificates

```bash
# SSH into application server
ssh -i ~/.ssh/id_rsa opc@<app_server_public_ip>

# Generate SSL certificates with Let's Encrypt
sudo certbot --nginx -d app.yourdomain.com -d api.yourdomain.com
```

### 5.3 Deploy Application

```bash
# On the application server
sudo /opt/scripts/deploy.sh
```

## Step 6: Verify Deployment

### 6.1 Check Infrastructure

```bash
# Get infrastructure details
terraform output

# Check application health
curl http://<load_balancer_ip>/api/health
```

### 6.2 Check Services

```bash
# SSH into application server
ssh -i ~/.ssh/id_rsa opc@<app_server_public_ip>

# Run health check
sudo /opt/scripts/health-check.sh

# Check Docker containers
docker ps

# Check logs
docker logs docassembler-backend
docker logs docassembler-frontend
```

## Troubleshooting

### Common Issues

1. **SSH Key Not Found**
   ```bash
   # Generate SSH key if missing
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa
   ```

2. **OCI API Authentication Failed**
   - Verify OCIDs are correct
   - Check API key permissions
   - Ensure fingerprint matches

3. **Cloudflare API Issues**
   - Verify API token permissions
   - Check zone ID is correct
   - Ensure domain is active in Cloudflare

4. **Cloud-init Failed**
   ```bash
   # Check cloud-init logs
   sudo cat /var/log/cloud-init-output.log
   sudo journalctl -u cloud-init
   ```

### Logs and Monitoring

- **Cloud-init logs**: `/var/log/cloud-init-output.log`
- **Application logs**: `/var/log/docassembler/`
- **Health checks**: `/var/log/docassembler/health.log`
- **Backup logs**: `/var/log/docassembler-backup.log`

## Next Steps

1. **Enable Remote Backend**: Configure S3-compatible backend for state management
2. **Set up Monitoring**: Deploy Prometheus and Grafana for monitoring
3. **Configure Backups**: Set up automated database backups to object storage
4. **Security Hardening**: Review and implement additional security measures
5. **Performance Tuning**: Optimize instance sizes and configurations

## Infrastructure Components

- **Load Balancer**: Public-facing with health checks
- **Application Servers**: Auto-scaling compute instances
- **Database Server**: PostgreSQL with Redis cache
- **Object Storage**: Document and backup storage
- **Networking**: VCN with public/private subnets
- **Security**: Firewall rules, SSL certificates, fail2ban
- **DNS**: Cloudflare managed DNS and CDN

For support or questions, refer to the project documentation or open an issue.

