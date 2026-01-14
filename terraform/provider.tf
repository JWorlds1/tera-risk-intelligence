# OpenStack Provider Konfiguration für H-DA Cloud
# Basierend auf den OpenRC Application Credentials

provider "openstack" {
  auth_url                      = var.auth_url
  application_credential_id     = var.application_credential_id
  application_credential_secret = var.application_credential_secret
  region                        = var.region
}

