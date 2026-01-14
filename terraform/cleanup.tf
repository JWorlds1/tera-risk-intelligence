# =============================================================================
# Cleanup-Skript zum Löschen aller existierenden Instanzen
# =============================================================================
# 
# ACHTUNG: Dieses Modul ist auskommentiert und dient als Referenz.
# Zum Löschen aller Instanzen nutze:
#   1. OpenStack CLI: openstack server delete <server_id>
#   2. Python Script: python backend/openstack/delete_server.py
#   3. terraform destroy (löscht nur von Terraform verwaltete Ressourcen)
#
# =============================================================================

# Null Resource für manuelle Cleanup-Operationen
# Kann bei Bedarf aktiviert werden

# resource "null_resource" "cleanup_existing_servers" {
#   provisioner "local-exec" {
#     command = <<-EOT
#       echo "Lösche alle existierenden Server..."
#       openstack --os-cloud openstack server list -f value -c ID | while read id; do
#         echo "Lösche Server: $id"
#         openstack --os-cloud openstack server delete "$id" --wait
#       done
#       echo "Cleanup abgeschlossen"
#     EOT
#   }
# }

