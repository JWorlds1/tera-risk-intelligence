# =============================================================================
# OpenStack Terraform Konfiguration für Geospatial Intelligence Server
# H-DA Cloud
# =============================================================================

# -----------------------------------------------------------------------------
# Data Sources - Existierende Ressourcen abfragen
# -----------------------------------------------------------------------------

# Verfügbare Images abfragen
data "openstack_images_image_v2" "ubuntu" {
  name        = var.image_name
  most_recent = true
}

# Verfügbare Flavors abfragen
data "openstack_compute_flavor_v2" "server_flavor" {
  name = var.flavor_name
}

# Netzwerk abfragen
data "openstack_networking_network_v2" "network" {
  name = var.network_name
}

# Floating IP Pool wird direkt über Variable konfiguriert

# -----------------------------------------------------------------------------
# SSH Key Pair
# -----------------------------------------------------------------------------

# Generiere neuen SSH Key wenn gewünscht
resource "tls_private_key" "ssh_key" {
  count     = var.generate_ssh_key ? 1 : 0
  algorithm = "RSA"
  rsa_bits  = 4096
}

# Speichere Private Key lokal
resource "local_file" "private_key" {
  count           = var.generate_ssh_key ? 1 : 0
  content         = tls_private_key.ssh_key[0].private_key_pem
  filename        = "${path.module}/keys/${var.ssh_key_name}.pem"
  file_permission = "0600"
}

# Speichere Public Key lokal
resource "local_file" "public_key" {
  count    = var.generate_ssh_key ? 1 : 0
  content  = tls_private_key.ssh_key[0].public_key_openssh
  filename = "${path.module}/keys/${var.ssh_key_name}.pub"
}

# OpenStack Key Pair erstellen
resource "openstack_compute_keypair_v2" "ssh_keypair" {
  name       = var.ssh_key_name
  public_key = var.generate_ssh_key ? tls_private_key.ssh_key[0].public_key_openssh : file(var.existing_public_key)
}

# -----------------------------------------------------------------------------
# Security Groups - Nutze existierende H-DA Cloud Security Groups
# -----------------------------------------------------------------------------
# Die H-DA Cloud hat bereits vordefinierte Security Groups:
# - default: Basis-Regeln
# - allow-ssh: SSH Zugang (Port 22)
# - allow-http: HTTP/HTTPS Zugang (Port 80/443)
# - allow-icmp: Ping (ICMP)
# - allow-ssh-hdaonly: SSH nur vom H-DA Campus
#
# Diese werden über die Variable security_groups referenziert

# -----------------------------------------------------------------------------
# Cloud-Init User Data
# -----------------------------------------------------------------------------

locals {
  cloud_init_script = <<-EOF
    #cloud-config
    package_update: true
    package_upgrade: true
    
    packages:
      - python3
      - python3-pip
      - python3-venv
      - git
      - curl
      - wget
      - htop
      - vim
      - docker.io
      - docker-compose
    
    runcmd:
      - systemctl enable docker
      - systemctl start docker
      - usermod -aG docker ubuntu
      - echo "Server erfolgreich konfiguriert am $(date)" > /var/log/cloud-init-done.log
    
    final_message: "Geospatial Intelligence Server ist bereit nach $UPTIME Sekunden"
  EOF

  user_data = var.user_data_enabled ? local.cloud_init_script : null
}

# -----------------------------------------------------------------------------
# Compute Instance (Server)
# -----------------------------------------------------------------------------

resource "openstack_compute_instance_v2" "server" {
  name            = var.server_name
  image_id        = data.openstack_images_image_v2.ubuntu.id
  flavor_id       = data.openstack_compute_flavor_v2.server_flavor.id
  key_pair        = openstack_compute_keypair_v2.ssh_keypair.name
  security_groups = var.security_groups
  user_data       = local.user_data

  network {
    uuid = data.openstack_networking_network_v2.network.id
  }

  metadata = {
    managed_by = "terraform"
    project    = "geospatial-intelligence"
    created    = timestamp()
  }

  lifecycle {
    create_before_destroy = true
  }
}

# -----------------------------------------------------------------------------
# Floating IP (Öffentliche IP für SSH Zugang)
# -----------------------------------------------------------------------------

resource "openstack_networking_floatingip_v2" "floating_ip" {
  count = var.assign_floating_ip ? 1 : 0
  pool  = var.floating_ip_pool
}

resource "openstack_networking_floatingip_associate_v2" "floating_ip_assoc" {
  count       = var.assign_floating_ip ? 1 : 0
  floating_ip = openstack_networking_floatingip_v2.floating_ip[0].address
  port_id     = openstack_compute_instance_v2.server.network[0].port
}

