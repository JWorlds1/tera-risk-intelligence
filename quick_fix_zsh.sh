#!/bin/bash
# Quick Fix für zsh Terminal-Fehler

echo "=========================================="
echo "zsh Terminal-Fehler Behebung"
echo "=========================================="
echo ""

# Backup erstellen
echo "1. Erstelle Backup..."
cp ~/.zshrc ~/.zshrc.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "  Keine .zshrc gefunden"

# Prüfe auf defekte Zeilen
echo ""
echo "2. Prüfe auf defekte Cursor-Hooks..."
if grep -q "cursor_snap_ENV_VARS\|dump_zsh_state" ~/.zshrc 2>/dev/null; then
    echo "  ⚠ Defekte Zeilen gefunden!"
    echo ""
    echo "  Gefundene Zeilen:"
    grep -n "cursor_snap_ENV_VARS\|dump_zsh_state" ~/.zshrc
    echo ""
    echo "  Möchten Sie diese Zeilen auskommentieren? (j/n)"
    read -r response
    if [[ "$response" =~ ^[Jj]$ ]]; then
        # Kommentiere defekte Zeilen aus
        sed -i.bak 's/^\(.*cursor_snap_ENV_VARS.*\)$/# \1/' ~/.zshrc
        sed -i.bak 's/^\(.*dump_zsh_state.*\)$/# \1/' ~/.zshrc
        echo "  ✓ Zeilen auskommentiert"
        echo "  ✓ Backup erstellt: ~/.zshrc.bak"
    fi
else
    echo "  ✓ Keine defekten Zeilen gefunden"
fi

echo ""
echo "3. Zeige letzte 10 Zeilen der .zshrc:"
echo "----------------------------------------"
tail -10 ~/.zshrc 2>/dev/null || echo "  Keine .zshrc gefunden"

echo ""
echo "=========================================="
echo "Fertig!"
echo ""
echo "Nächste Schritte:"
echo "  1. Öffnen Sie ein neues Terminal"
echo "  2. Oder führen Sie aus: source ~/.zshrc"
echo "  3. Testen Sie: echo 'Test'"
echo ""
echo "Falls das Problem weiterhin besteht:"
echo "  - Verwenden Sie bash: bash"
echo "  - Oder prüfen Sie ~/.zshenv und ~/.zprofile"
echo "=========================================="

