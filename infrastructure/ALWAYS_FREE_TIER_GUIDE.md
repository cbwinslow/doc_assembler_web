# DocAssembler Always Free Tier Deployment Guide

This guide shows you how to deploy DocAssembler using **100% FREE** Oracle Cloud Infrastructure resources. No charges will be incurred using this configuration.

## 🎉 What's Included in Always Free Tier

### Oracle Cloud Infrastructure (OCI) Always Free Resources:
- ✅ **2x VM.Standard.E2.1.Micro instances** (1 OCPU, 1GB RAM each)
- ✅ **2x Block Storage volumes** (50GB each)
- ✅ **10GB Object Storage** (with versioning)
- ✅ **Virtual Cloud Network (VCN)** with internet gateway
- ✅ **Security lists and firewall rules**
- ✅ **Public IP addresses**
- ✅ **Load balancer traffic** (10Mbps)

### What We Removed for Zero Cost:
- ❌ **Load Balancer** (costs ~$15/month) - Using direct server access
- ❌ **Flexible VM shapes** - Using micro instances only
- ❌ **Additional storage** - Using free tier limits
- ❌ **Premium features** - Keeping it simple and free

## 💰 Total Cost: $0.00/month

This configuration will run indefinitely at **zero cost** as long as you stay within Oracle's Always Free Tier limits.

## 🏗️ Architecture Overview

```
Internet → Cloudflare CDN → OCI Application Server (Public) → Database Server (Private)
```

- **1x Application Server** (VM.Standard.E2.1.Micro) - Runs web app, API, Nginx
- **1x Database Server** (VM.Standard.E2.1.Micro) - Runs PostgreSQL and Redis
- **Object Storage** - Document storage and backups
- **Cloudflare** - Free CDN, DNS, and security

## 📋 Prerequisites

1. **Oracle Cloud Account** (Free tier)
2. **Cloudflare Account** (Free tier)
3. **Domain name** registered with Cloudflare

## 🚀 Step-by-Step Deployment

### Step 1: Oracle Cloud Setup

1. **Sign up for Oracle Cloud Free Tier**:
   - Go to https://cloud.oracle.com/
   - Create free account (no credit card required after initial verification)
   - Verify your account

2. **Generate API Keys**:
   ```bash
   mkdir -p ~/.oci
   openssl genrsa -out ~/.oci/oci_api_key.pem 2048
   openssl rsa -pubout -in ~/.oci/oci_api_key.pem -out ~/.oci/oci_api_key_public.pem
   ```

3. **Add Public Key to OCI**:
   - Login to OCI Console
   - User Settings → API Keys → Add API Key
   - Upload `~/.oci/oci_api_key_public.pem`
   - Save the fingerprint

4. **Collect Required Information**:
   - Tenancy OCID (Administration → Tenancy Details)
   - User OCID (User Settings → User Information)
   - Compartment OCID (Identity → Compartments)

### Step 2: Cloudflare Setup

1. **Domain Setup**:
   - Add your domain to Cloudflare (free)
   - Update nameservers at your registrar

2. **Get API Credentials**:
   - Cloudflare Dashboard → My Profile → API Tokens
   - Create token with Zone:Read, Zone:DNS:Edit permissions
   - Get Zone ID from domain dashboard

### Step 3: Configure Infrastructure

1. **Update Configuration**:
   ```bash
   cd infrastructure/terraform
   cp terraform.tfvars.example terraform.tfvars
   vim terraform.tfvars
   ```

2. **Replace with Your Actual Values**:
   ```hcl
   # OCI Configuration
   oci_tenancy_ocid      = "ocid1.tenancy.oc1..YOUR_ACTUAL_TENANCY_OCID"
   oci_user_ocid         = "ocid1.user.oc1..YOUR_ACTUAL_USER_OCID"
   oci_fingerprint       = "YOUR_ACTUAL_FINGERPRINT"
   oci_private_key_path  = "~/.oci/oci_api_key.pem"
   oci_region           = "us-ashburn-1"
   oci_compartment_id   = "ocid1.compartment.oc1..YOUR_COMPARTMENT_OCID"

   # Cloudflare Configuration
   cloudflare_api_token = "YOUR_ACTUAL_CLOUDFLARE_TOKEN"
   cloudflare_zone_id   = "YOUR_ACTUAL_ZONE_ID"
   cloudflare_account_id = "YOUR_ACTUAL_ACCOUNT_ID"

   # Application Configuration
   environment   = "prod"
   domain_name   = "yourdomain.com"
   subdomain     = "app"

   # Always Free Tier Settings (DO NOT CHANGE)
   app_server_count      = 1
   auto_scaling_enabled  = false
   max_app_servers       = 1
   ```

### Step 4: Deploy Infrastructure

1. **Run Deployment**:
   ```bash
   cd infrastructure/terraform
   terraform init
   terraform plan
   terraform apply
   ```

2. **Wait for Setup** (5-10 minutes):
   ```bash
   # Check cloud-init progress
   ssh -i ~/.ssh/id_rsa opc@<app_server_ip>
   sudo cloud-init status --wait
   ```

### Step 5: Configure Application

1. **Set up SSL Certificates**:
   ```bash
   ssh -i ~/.ssh/id_rsa opc@<app_server_ip>
   sudo certbot --nginx -d app.yourdomain.com -d api.yourdomain.com
   ```

2. **Deploy Application**:
   ```bash
   sudo /opt/scripts/deploy.sh
   ```

## 📊 Performance Expectations

### Always Free Tier Specs:
- **CPU**: 1 OCPU per server (shared)
- **RAM**: 1GB per server
- **Storage**: 50GB block storage per server
- **Network**: 10Mbps bandwidth

### Expected Performance:
- **Concurrent Users**: 10-50 users
- **API Response Time**: 200-500ms
- **File Processing**: Small to medium documents
- **Database**: Handles typical web app workload

## 🔧 Optimization Tips for Free Tier

### Memory Management:
```bash
# Add swap file for extra memory
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Nginx Optimization:
```nginx
# /etc/nginx/nginx.conf
worker_processes 1;
worker_connections 512;
client_max_body_size 10M;
```

### PostgreSQL Tuning:
```sql
-- Optimize for small RAM
ALTER SYSTEM SET shared_buffers = '128MB';
ALTER SYSTEM SET effective_cache_size = '512MB';
ALTER SYSTEM SET work_mem = '4MB';
SELECT pg_reload_conf();
```

## 🚨 Important Limitations

### Always Free Tier Limits:
- **2 VM instances maximum** (we use both)
- **1 OCPU per instance** (cannot increase)
- **1GB RAM per instance** (cannot increase)
- **50GB storage per instance** (can expand if needed)
- **No load balancer** (direct server access)

### What Happens If You Exceed Limits:
- Oracle will **ask permission** before charging
- Services will be stopped, not billed
- You can upgrade to paid tier if needed

## 🎯 Production Considerations

### For Production Use:
1. **Upgrade to paid instances** for better performance
2. **Add load balancer** for high availability
3. **Use managed database** for better reliability
4. **Enable monitoring and alerting**
5. **Set up proper backup strategies**

### When to Upgrade:
- More than 50 concurrent users
- Large file processing requirements
- Need for high availability
- Business-critical applications

## 📈 Scaling Path

### Free Tier → Paid Tier Upgrade:
1. Change instance shapes in Terraform
2. Add load balancer
3. Enable auto-scaling
4. Add monitoring services

### Estimated Costs After Upgrade:
- **Small Production**: $25-50/month
- **Medium Production**: $100-200/month
- **Large Production**: $500+/month

## 🔒 Security Features (Included Free)

- ✅ **SSL/TLS encryption** (Let's Encrypt)
- ✅ **Cloudflare security** (DDoS protection, WAF)
- ✅ **Firewall rules** (OCI Security Lists)
- ✅ **Fail2ban** (brute force protection)
- ✅ **Private database subnet**
- ✅ **SSH key authentication**

## 📞 Support and Troubleshooting

### Common Issues:
1. **Out of Memory**: Add swap file (see optimization tips)
2. **Slow Performance**: Use Cloudflare caching
3. **Storage Full**: Clean logs and old backups
4. **Connection Issues**: Check security list rules

### Getting Help:
- Oracle Cloud Free Tier Forum
- Cloudflare Community
- Project GitHub Issues

## 🎉 Congratulations!

You now have a **production-ready, zero-cost** DocAssembler deployment running on enterprise-grade infrastructure!

### What You've Achieved:
- ✅ **Full web application stack**
- ✅ **Database with backups**
- ✅ **CDN and security**
- ✅ **SSL certificates**
- ✅ **Monitoring and health checks**
- ✅ **Professional domain setup**

**Total Monthly Cost: $0.00** 🎊

Your infrastructure will run indefinitely at zero cost as long as you stay within Oracle's Always Free Tier limits!

