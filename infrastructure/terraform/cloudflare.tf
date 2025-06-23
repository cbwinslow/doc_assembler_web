# Cloudflare Zone Data
data "cloudflare_zone" "main" {
  zone_id = var.cloudflare_zone_id
}

# DNS Records
resource "cloudflare_record" "app" {
  zone_id = var.cloudflare_zone_id
  name    = var.subdomain
  value   = oci_core_instance.docassembler_app_server[0].public_ip
  type    = "A"
  ttl     = 300
  proxied = true

  comment = "DocAssembler application main domain"
}

resource "cloudflare_record" "api" {
  zone_id = var.cloudflare_zone_id
  name    = "api"
  value   = oci_core_instance.docassembler_app_server[0].public_ip
  type    = "A"
  ttl     = 300
  proxied = true

  comment = "DocAssembler API endpoint"
}

resource "cloudflare_record" "www" {
  zone_id = var.cloudflare_zone_id
  name    = "www"
  value   = "${var.subdomain}.${var.domain_name}"
  type    = "CNAME"
  ttl     = 300
  proxied = true

  comment = "WWW redirect to app subdomain"
}

# Additional subdomains for monitoring and admin
resource "cloudflare_record" "monitoring" {
  zone_id = var.cloudflare_zone_id
  name    = "monitoring"
  value   = oci_core_instance.docassembler_app_server[0].public_ip
  type    = "A"
  ttl     = 300
  proxied = true

  comment = "Monitoring dashboard"
}

resource "cloudflare_record" "grafana" {
  zone_id = var.cloudflare_zone_id
  name    = "grafana"
  value   = oci_core_instance.docassembler_app_server[0].public_ip
  type    = "A"
  ttl     = 300
  proxied = true

  comment = "Grafana monitoring dashboard"
}

resource "cloudflare_record" "prometheus" {
  zone_id = var.cloudflare_zone_id
  name    = "prometheus"
  value   = oci_core_instance.docassembler_app_server[0].public_ip
  type    = "A"
  ttl     = 300
  proxied = true

  comment = "Prometheus metrics endpoint"
}

# Page Rules for performance optimization
resource "cloudflare_page_rule" "api_cache" {
  zone_id  = var.cloudflare_zone_id
  target   = "api.${var.domain_name}/api/*"
  priority = 1
  status   = "active"

  actions {
    cache_level = "bypass"
    ssl         = "full"
  }
}

resource "cloudflare_page_rule" "app_cache" {
  zone_id  = var.cloudflare_zone_id
  target   = "${var.subdomain}.${var.domain_name}/*"
  priority = 2
  status   = "active"

  actions {
    cache_level                = "aggressive"
    edge_cache_ttl             = 86400  # 24 hours
    browser_cache_ttl          = 3600   # 1 hour
    ssl                        = "full"
    automatic_https_rewrites   = "on"
    security_level            = "medium"
  }
}

resource "cloudflare_page_rule" "static_assets" {
  zone_id  = var.cloudflare_zone_id
  target   = "${var.subdomain}.${var.domain_name}/assets/*"
  priority = 3
  status   = "active"

  actions {
    cache_level       = "cache_everything"
    edge_cache_ttl    = 2592000  # 30 days
    browser_cache_ttl = 2592000  # 30 days
    ssl              = "full"
  }
}

# Security Settings
resource "cloudflare_zone_settings_override" "security" {
  zone_id = var.cloudflare_zone_id

  settings {
    ssl                      = "full"
    always_use_https        = "on"
    min_tls_version         = "1.2"
    opportunistic_encryption = "on"
    tls_1_3                 = "zrt"
    automatic_https_rewrites = "on"
    security_level          = "medium"
    challenge_ttl           = 1800
    privacy_pass            = "on"
    security_header {
      enabled = true
    }
    brotli = "on"
    minify {
      css  = "on"
      js   = "on"
      html = "on"
    }
    rocket_loader = "on"
    mirage        = "on"
    polish        = "lossless"
    webp          = "on"
  }
}

# Firewall Rules
resource "cloudflare_filter" "rate_limit_api" {
  zone_id     = var.cloudflare_zone_id
  description = "Rate limit API requests"
  expression  = "(http.request.uri.path matches \"^/api/.*\" and rate(5m) > 100)"
}

resource "cloudflare_firewall_rule" "rate_limit_api" {
  zone_id     = var.cloudflare_zone_id
  description = "Rate limit API requests to 100 per 5 minutes"
  filter_id   = cloudflare_filter.rate_limit_api.id
  action      = "challenge"
  priority    = 1
}

resource "cloudflare_filter" "block_admin_access" {
  zone_id     = var.cloudflare_zone_id
  description = "Block access to admin endpoints from non-whitelisted IPs"
  expression  = "(http.request.uri.path matches \"^/(admin|monitoring|grafana|prometheus).*\" and not ip.src in {1.2.3.4 2.3.4.5})"
}

resource "cloudflare_firewall_rule" "block_admin_access" {
  zone_id     = var.cloudflare_zone_id
  description = "Block admin access from non-whitelisted IPs"
  filter_id   = cloudflare_filter.block_admin_access.id
  action      = "block"
  priority    = 2
}

# Access Application for Admin Areas
resource "cloudflare_access_application" "admin_panel" {
  zone_id          = var.cloudflare_zone_id
  name             = "DocAssembler Admin Panel"
  domain           = "monitoring.${var.domain_name}"
  type             = "self_hosted"
  session_duration = "24h"

  cors_headers {
    allowed_methods = ["GET", "POST", "OPTIONS"]
    allowed_origins = ["https://${var.subdomain}.${var.domain_name}"]
    allow_credentials = true
    max_age = 600
  }
}

resource "cloudflare_access_policy" "admin_panel_policy" {
  application_id = cloudflare_access_application.admin_panel.id
  zone_id        = var.cloudflare_zone_id
  name           = "Admin Access Policy"
  precedence     = 1
  decision       = "allow"

  include {
    email = ["admin@${var.domain_name}"]
  }
}

# Workers for Edge Computing - temporarily commented out
# Requires KV namespace which needs account_id
# resource "cloudflare_worker_script" "api_proxy" {
#   name    = "docassembler-api-proxy"
#   content = file("${path.module}/../cloudflare/workers/api-proxy.js")
#
#   kv_namespace_binding {
#     name         = "API_CACHE"
#     namespace_id = cloudflare_workers_kv_namespace.api_cache.id
#   }
#
#   secret_text_binding {
#     name = "API_KEY"
#     text = var.jwt_secret
#   }
# }

# Temporarily commented out - requires account_id
# resource "cloudflare_workers_kv_namespace" "api_cache" {
#   title = "docassembler-api-cache-${var.environment}"
#   account_id = var.cloudflare_account_id
# }

# resource "cloudflare_worker_route" "api_proxy" {
#   zone_id     = var.cloudflare_zone_id
#   pattern     = "api.${var.domain_name}/api/*"
#   script_name = cloudflare_worker_script.api_proxy.name
# }

# Analytics and Performance
resource "cloudflare_logpull_retention" "analytics" {
  zone_id = var.cloudflare_zone_id
  enabled = true
}

# Custom SSL Certificate (Let's Encrypt integration)
resource "cloudflare_origin_ca_certificate" "cert" {
  csr                = tls_cert_request.origin.cert_request_pem
  hostnames          = [
    var.domain_name,
    "*.${var.domain_name}"
  ]
  request_type       = "origin-rsa"
  requested_validity = 365
}

resource "tls_private_key" "origin" {
  algorithm = "RSA"
  rsa_bits  = 2048
}

resource "tls_cert_request" "origin" {
  private_key_pem = tls_private_key.origin.private_key_pem

  subject {
    common_name  = var.domain_name
    organization = "DocAssembler"
  }

  dns_names = [
    var.domain_name,
    "*.${var.domain_name}"
  ]
}

# R2 Object Storage Integration - temporarily commented out
# Requires account_id and valid location
# resource "cloudflare_r2_bucket" "documents" {
#   account_id = var.cloudflare_account_id
#   name       = "docassembler-${var.environment}-documents"
#   location   = "WNAM"  # Valid location
# }

# resource "cloudflare_r2_bucket" "backups" {
#   account_id = var.cloudflare_account_id
#   name       = "docassembler-${var.environment}-backups"
#   location   = "WNAM"  # Valid location
# }


