# =============================================================================
# Makefile für Terraform OpenStack Deployment
# =============================================================================

.PHONY: help init plan apply destroy clean list-resources ssh

# Standardziel
help:
	@echo "=========================================="
	@echo "OpenStack Terraform Deployment"
	@echo "=========================================="
	@echo ""
	@echo "Verfügbare Befehle:"
	@echo "  make init            - Terraform initialisieren"
	@echo "  make plan            - Änderungen vorschauen"
	@echo "  make apply           - Änderungen anwenden (Server erstellen)"
	@echo "  make destroy         - Alle Ressourcen löschen"
	@echo "  make clean           - Terraform State und Cache löschen"
	@echo "  make list-resources  - Verfügbare OpenStack Ressourcen anzeigen"
	@echo "  make ssh             - SSH-Verbindung zum Server herstellen"
	@echo "  make output          - Server-Informationen anzeigen"
	@echo ""

# Terraform initialisieren
init:
	@echo "Initialisiere Terraform..."
	terraform init

# Plan anzeigen
plan: init
	@echo "Zeige geplante Änderungen..."
	terraform plan

# Änderungen anwenden
apply: init
	@echo "Erstelle Server..."
	terraform apply -auto-approve
	@echo ""
	@echo "Server-Informationen:"
	terraform output

# Alles zerstören
destroy:
	@echo "WARNUNG: Alle Ressourcen werden gelöscht!"
	@read -p "Fortfahren? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	terraform destroy -auto-approve

# Aufräumen
clean:
	@echo "Lösche Terraform State und Cache..."
	rm -rf .terraform
	rm -rf .terraform.lock.hcl
	rm -rf terraform.tfstate*
	rm -rf keys/

# OpenStack Ressourcen auflisten
list-resources:
	@echo "Verfügbare OpenStack Ressourcen:"
	@echo ""
	@echo "=== Server ==="
	openstack --os-cloud openstack server list 2>/dev/null || echo "Keine Server gefunden"
	@echo ""
	@echo "=== Images ==="
	openstack --os-cloud openstack image list 2>/dev/null || echo "Keine Images gefunden"
	@echo ""
	@echo "=== Flavors ==="
	openstack --os-cloud openstack flavor list 2>/dev/null || echo "Keine Flavors gefunden"
	@echo ""
	@echo "=== Networks ==="
	openstack --os-cloud openstack network list 2>/dev/null || echo "Keine Netzwerke gefunden"

# SSH zum Server
ssh:
	@if [ -f keys/geospatial-key.pem ]; then \
		IP=$$(terraform output -raw server_floating_ip 2>/dev/null); \
		echo "Verbinde zu $$IP..."; \
		ssh -i keys/geospatial-key.pem -o StrictHostKeyChecking=no ubuntu@$$IP; \
	else \
		echo "SSH Key nicht gefunden. Führe zuerst 'make apply' aus."; \
	fi

# Output anzeigen
output:
	terraform output

