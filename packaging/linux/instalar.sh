#!/bin/sh
# Instala o HaradaER só para o seu usuário (sem sudo): o programa vai para ~/.local/bin e o
# atalho com ícone para o menu de aplicativos. Para desinstalar: ./instalar.sh --remover
set -eu

ID=io.github.pedroharada.haradaer
AQUI=$(cd "$(dirname "$0")" && pwd)
DADOS=${XDG_DATA_HOME:-$HOME/.local/share}
BIN=$HOME/.local/bin
ATALHO=$DADOS/applications/$ID.desktop
ICONE=$DADOS/icons/hicolor/scalable/apps/$ID.svg

atualizar_menu() {
    command -v update-desktop-database >/dev/null 2>&1 &&
        update-desktop-database "$DADOS/applications" 2>/dev/null || true
    command -v gtk-update-icon-cache >/dev/null 2>&1 &&
        gtk-update-icon-cache -q -t "$DADOS/icons/hicolor" 2>/dev/null || true
}

if [ "${1:-}" = "--remover" ]; then
    rm -f "$BIN/HaradaER" "$ATALHO" "$ICONE"
    atualizar_menu
    echo "HaradaER removido. Suas preferências ficam em ~/.config/HaradaER."
    exit 0
fi

mkdir -p "$BIN" "$(dirname "$ATALHO")" "$(dirname "$ICONE")"
install -m 755 "$AQUI/HaradaER" "$BIN/HaradaER"
install -m 644 "$AQUI/haradaer.svg" "$ICONE"
# o caminho completo no Exec: funciona mesmo se ~/.local/bin não estiver no PATH
sed "s|^Exec=HaradaER|Exec=\"$BIN/HaradaER\"|" "$AQUI/$ID.desktop" > "$ATALHO"
chmod 644 "$ATALHO"
atualizar_menu

echo "HaradaER instalado. Procure por \"HaradaER\" no menu de aplicativos."
case ":$PATH:" in
    *":$BIN:"*) echo "No terminal: HaradaER [modelo.xml]" ;;
    *) echo "Para abrir pelo terminal só com \"HaradaER\", ponha $BIN no PATH." ;;
esac
