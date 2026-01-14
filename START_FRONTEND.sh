#!/bin/bash
# Start-Script für das Frontend

cd "$(dirname "$0")/backend"

echo "🌍 Climate Conflict Intelligence Dashboard"
echo "=========================================="
echo ""

# Prüfe ob Python verfügbar ist
if ! command -v python &> /dev/null; then
    echo "❌ Python nicht gefunden!"
    exit 1
fi

# Starte Server
python -c "
from web_app import app
import socket

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

port = find_free_port()
print(f'🚀 Starte Frontend auf Port {port}...')
print(f'')
print(f'📊 Öffne im Browser: http://localhost:{port}')
print(f'🔗 API-Endpoints:')
print(f'   - http://localhost:{port}/api/stats')
print(f'   - http://localhost:{port}/api/regional-data')
print(f'   - http://localhost:{port}/api/records')
print(f'')
print(f'⚠️  Server läuft. Drücke Ctrl+C zum Beenden.')
print(f'')

app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)
"

