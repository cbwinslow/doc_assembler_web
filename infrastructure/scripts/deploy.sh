#!/bin/bash

# DocAssembler Infrastructure Deployment Script
# This script helps deploy the complete infrastructure for DocAssembler

set -e

echo "🚀 DocAssembler Infrastructure Deployment"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Change to terraform directory
cd "$(dirname "$0")/../terraform"

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    print_error "terraform.tfvars file not found!"
    echo ""
    echo "Please create terraform.tfvars based on the example file:"
    echo "  cp terraform.tfvars.example terraform.tfvars"
    echo ""
    echo "Then edit terraform.tfvars with your actual credentials and configuration."
    echo ""
    echo "Required credentials:"
    echo "  - Oracle Cloud Infrastructure (OCI) API credentials"
    echo "  - Cloudflare API token and zone ID"
    echo "  - Application secrets (JWT, OpenAI API key, etc.)"
    echo ""
    exit 1
fi

# Check if SSH key exists
SSH_KEY_PATH=$(grep ssh_public_key_path terraform.tfvars | cut -d'"' -f2 | sed 's/~/$HOME/')
if [ ! -f "$SSH_KEY_PATH" ]; then
    print_warning "SSH public key not found at: $SSH_KEY_PATH"
    echo ""
    echo "Generating SSH key pair..."
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
    print_status "SSH key pair generated at ~/.ssh/id_rsa"
fi

# Check if OCI CLI is configured (optional but recommended)
if command -v oci &> /dev/null; then
    if [ -f ~/.oci/config ]; then
        print_status "OCI CLI is configured"
    else
        print_warning "OCI CLI is installed but not configured"
        echo "You can configure it with: oci setup config"
    fi
else
    print_warning "OCI CLI is not installed"
    echo "Consider installing it for easier credential management"
fi

# Terraform deployment steps
print_status "Starting Terraform deployment..."

echo ""
echo "Step 1: Terraform Init"
echo "====================="
terraform init

echo ""
echo "Step 2: Terraform Validate"
echo "=========================="
terraform validate

echo ""
echo "Step 3: Terraform Plan"
echo "====================="
terraform plan -out=tfplan

echo ""
echo "Step 4: Review and Apply"
echo "======================="
echo "The infrastructure plan has been generated. Review the planned changes above."
echo ""
read -p "Do you want to apply these changes? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    print_status "Applying Terraform configuration..."
    terraform apply tfplan
    
    echo ""
    print_status "Deployment completed successfully! 🎉"
    echo ""
    echo "Next steps:"
    echo "1. Wait for instances to finish initialization (5-10 minutes)"
    echo "2. Configure DNS records in Cloudflare"
    echo "3. Set up SSL certificates"
    echo "4. Deploy the application code"
    echo ""
    echo "Run 'terraform output' to see the infrastructure details."
else
    print_warning "Deployment cancelled by user"
    rm -f tfplan
fi

