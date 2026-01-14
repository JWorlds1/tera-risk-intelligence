# Server-Login-Problem lösen

## Problem
- Server wurde ohne SSH-Key erstellt
- Ubuntu Cloud Image erlaubt nur SSH-Key-Authentifizierung
- Kein Passwort-Login möglich

## Lösungen

### Option 1: Single-User-Modus (falls möglich)
1. In der Console: Server neu starten
2. Beim Boot: Grub-Menü öffnen (ESC oder Shift drücken)
3. Kernel-Optionen bearbeiten
4. Am Ende hinzufügen: `single` oder `init=/bin/bash`
5. Boot fortsetzen
6. Sie sind als root eingeloggt
7. Dann können Sie:
   ```bash
   # SSH-Key hinzufügen
   mkdir -p /home/ubuntu/.ssh
   chmod 700 /home/ubuntu/.ssh
   echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCsJKdHNYqOX5nl+9RtKK0fYOfwueyFmmQxtWWX/7p5EaNDz5vU0HnAI7uzSbW69KzQcGyZUZ66g+/mL55xZQ6N+4tv7hBOlRvZCoDFqxvYsvT18mOD4P5yEcBXXqpgrrsvc2stN8+xrkJAYc/W9aRlTUvw6jEm8iXaPqMDLsXo3XT9U6WbyJXKM7jPPOojvFncKaOGY3UJFVnpRZtXoNs+7exx9/E9j6+7KNooproz6C2ASF2iZ9bgOOAOtKpXZvCj19/fAsl+ot7iyi1A7daCI+Bne1TWzud7v9A9C9yrSvDyjndXixVt0U+H5xxmuXfpoo6zxTV6AmdCpYgIOtP3 Generated-by-Nova" > /home/ubuntu/.ssh/authorized_keys
   chmod 600 /home/ubuntu/.ssh/authorized_keys
   chown -R ubuntu:ubuntu /home/ubuntu/.ssh
   
   # Oder Passwort für ubuntu setzen
   passwd ubuntu
   # Dann: PasswordAuthentication in /etc/ssh/sshd_config aktivieren
   ```

### Option 2: Server neu erstellen (EMPFOHLEN)
Das Script `create_server_simple.py` wurde aktualisiert und verwendet jetzt automatisch den SSH-Key "hopp".

1. Server löschen (im Dashboard oder per API)
2. Server neu erstellen mit: `python3 backend/openstack/create_server_simple.py`
3. Danach funktioniert: `ssh ubuntu@10.193.17.102`

### Option 3: Passwort-Login aktivieren (falls Single-User-Modus funktioniert)
```bash
# Als root (im Single-User-Modus)
passwd ubuntu
# Passwort eingeben

# SSH Passwort-Authentifizierung aktivieren
sed -i 's/#PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
systemctl restart sshd
```

