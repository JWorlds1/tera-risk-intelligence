# =============================================================================
# Terraform Outputs - Server Informationen
# =============================================================================

output "server_id" {
  description = "ID des erstellten Servers"
  value       = openstack_compute_instance_v2.server.id
}

output "server_name" {
  description = "Name des Servers"
  value       = openstack_compute_instance_v2.server.name
}

output "server_private_ip" {
  description = "Private IP-Adresse des Servers"
  value       = openstack_compute_instance_v2.server.access_ip_v4
}

output "server_floating_ip" {
  description = "Floating (öffentliche) IP-Adresse des Servers"
  value       = var.assign_floating_ip ? openstack_networking_floatingip_v2.floating_ip[0].address : "Keine Floating IP zugewiesen"
}

output "ssh_command" {
  description = "SSH Befehl zum Verbinden mit dem Server"
  value       = var.assign_floating_ip ? "ssh -i ${path.module}/keys/${var.ssh_key_name}.pem ubuntu@${openstack_networking_floatingip_v2.floating_ip[0].address}" : "ssh -i ${path.module}/keys/${var.ssh_key_name}.pem ubuntu@${openstack_compute_instance_v2.server.access_ip_v4}"
}

output "ssh_key_path" {
  description = "Pfad zum SSH Private Key"
  value       = var.generate_ssh_key ? "${path.module}/keys/${var.ssh_key_name}.pem" : var.existing_public_key
}

output "image_used" {
  description = "Verwendetes OS Image"
  value       = data.openstack_images_image_v2.ubuntu.name
}

output "flavor_used" {
  description = "Verwendeter Flavor"
  value = {
    name  = data.openstack_compute_flavor_v2.server_flavor.name
    vcpus = data.openstack_compute_flavor_v2.server_flavor.vcpus
    ram   = "${data.openstack_compute_flavor_v2.server_flavor.ram} MB"
    disk  = "${data.openstack_compute_flavor_v2.server_flavor.disk} GB"
  }
}

output "security_groups" {
  description = "Zugewiesene Security Groups"
  value       = openstack_compute_instance_v2.server.security_groups
}

# Zusammenfassung für einfachen Zugriff
output "connection_info" {
  description = "Alle wichtigen Verbindungsinformationen"
  value = {
    server_name  = openstack_compute_instance_v2.server.name
    public_ip    = var.assign_floating_ip ? openstack_networking_floatingip_v2.floating_ip[0].address : openstack_compute_instance_v2.server.access_ip_v4
    ssh_user     = "ubuntu"
    ssh_key_file = var.generate_ssh_key ? "${path.module}/keys/${var.ssh_key_name}.pem" : var.existing_public_key
    ssh_command  = var.assign_floating_ip ? "ssh -i keys/${var.ssh_key_name}.pem ubuntu@${openstack_networking_floatingip_v2.floating_ip[0].address}" : "ssh -i keys/${var.ssh_key_name}.pem ubuntu@${openstack_compute_instance_v2.server.access_ip_v4}"
  }
}

