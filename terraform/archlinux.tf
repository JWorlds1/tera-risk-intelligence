# =============================================================================
# Arch Linux Server mit 200 GB Volume
# =============================================================================

# -----------------------------------------------------------------------------
# Variablen für Arch Linux Server
# -----------------------------------------------------------------------------

variable "archlinux_enabled" {
  description = "Soll die Arch Linux Instanz erstellt werden?"
  type        = bool
  default     = false
}

variable "archlinux_server_name" {
  description = "Name der Arch Linux Instanz"
  type        = string
  default     = "archlinux-server"
}

variable "archlinux_flavor_name" {
  description = "Flavor für Arch Linux (m1.2xlarge = 32GB RAM parallel, m1.4xlarge = 64GB wenn allein)"
  type        = string
  default     = "m1.2xlarge"
}

variable "archlinux_volume_size" {
  description = "Größe des Daten-Volumes in GB"
  type        = number
  default     = 200
}

# -----------------------------------------------------------------------------
# Arch Linux Image
# -----------------------------------------------------------------------------

data "openstack_images_image_v2" "archlinux" {
  count       = var.archlinux_enabled ? 1 : 0
  name        = "Arch Linux Cloud Image"
  most_recent = true
}

data "openstack_compute_flavor_v2" "archlinux_flavor" {
  count = var.archlinux_enabled ? 1 : 0
  name  = var.archlinux_flavor_name
}

# -----------------------------------------------------------------------------
# 200 GB Daten-Volume für Arch Linux
# -----------------------------------------------------------------------------

resource "openstack_blockstorage_volume_v3" "archlinux_data" {
  count       = var.archlinux_enabled ? 1 : 0
  name        = "archlinux-data"
  description = "200 GB Daten-Volume für Arch Linux Server"
  size        = var.archlinux_volume_size
  
  metadata = {
    managed_by = "terraform"
    project    = "geospatial-intelligence"
    purpose    = "archlinux-data-storage"
  }
}

# -----------------------------------------------------------------------------
# Cloud-Init für Arch Linux
# -----------------------------------------------------------------------------

locals {
  archlinux_cloud_init = <<-EOF
    #cloud-config
    package_update: true
    
    packages:
      - python
      - python-pip
      - git
      - curl
      - wget
      - htop
      - vim
      - docker
      - docker-compose
    
    runcmd:
      - systemctl enable docker
      - systemctl start docker
      - echo "Arch Linux Server bereit am $(date)" > /var/log/cloud-init-done.log
    
    final_message: "Arch Linux Server ist bereit nach $UPTIME Sekunden"
  EOF
}

# -----------------------------------------------------------------------------
# Arch Linux Compute Instance
# -----------------------------------------------------------------------------

resource "openstack_compute_instance_v2" "archlinux" {
  count           = var.archlinux_enabled ? 1 : 0
  name            = var.archlinux_server_name
  image_id        = data.openstack_images_image_v2.archlinux[0].id
  flavor_id       = data.openstack_compute_flavor_v2.archlinux_flavor[0].id
  key_pair        = openstack_compute_keypair_v2.ssh_keypair.name
  security_groups = var.security_groups
  user_data       = local.archlinux_cloud_init

  network {
    uuid = data.openstack_networking_network_v2.network.id
  }

  metadata = {
    managed_by = "terraform"
    project    = "geospatial-intelligence"
    os         = "archlinux"
    created    = timestamp()
  }

  lifecycle {
    create_before_destroy = true
  }
}

# -----------------------------------------------------------------------------
# Volume Attachment
# -----------------------------------------------------------------------------

resource "openstack_compute_volume_attach_v2" "archlinux_data_attach" {
  count       = var.archlinux_enabled ? 1 : 0
  instance_id = openstack_compute_instance_v2.archlinux[0].id
  volume_id   = openstack_blockstorage_volume_v3.archlinux_data[0].id
}

# -----------------------------------------------------------------------------
# Floating IP für Arch Linux
# -----------------------------------------------------------------------------

resource "openstack_networking_floatingip_v2" "archlinux_floating_ip" {
  count = var.archlinux_enabled && var.assign_floating_ip ? 1 : 0
  pool  = var.floating_ip_pool
}

resource "openstack_networking_floatingip_associate_v2" "archlinux_floating_ip_assoc" {
  count       = var.archlinux_enabled && var.assign_floating_ip ? 1 : 0
  floating_ip = openstack_networking_floatingip_v2.archlinux_floating_ip[0].address
  port_id     = openstack_compute_instance_v2.archlinux[0].network[0].port
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "archlinux_server_ip" {
  description = "Private IP der Arch Linux Instanz"
  value       = var.archlinux_enabled ? openstack_compute_instance_v2.archlinux[0].network[0].fixed_ip_v4 : null
}

output "archlinux_floating_ip" {
  description = "Öffentliche IP der Arch Linux Instanz"
  value       = var.archlinux_enabled && var.assign_floating_ip ? openstack_networking_floatingip_v2.archlinux_floating_ip[0].address : null
}

output "archlinux_volume_id" {
  description = "ID des 200 GB Volumes"
  value       = var.archlinux_enabled ? openstack_blockstorage_volume_v3.archlinux_data[0].id : null
}
























