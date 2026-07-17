#!/usr/bin/env bash
# Sets up a Wine prefix with the .NET Desktop Runtime Sims4Studio needs, and
# downloads the Sims4Studio installer. Meant to run on a Linux CI runner
# (Ubuntu) with Wine already installed (see .github/workflows/ci.yml).
#
# KNOWN GAP: this prepares the environment; it does not install/run
# Sims4Studio's GUI for you. See packages/casp_template/README.md for why
# the actual UI-automation step (automate_casp.py) is a documented
# NotImplementedError rather than guessed click coordinates.
set -euo pipefail

WINEPREFIX="${WINEPREFIX:-$HOME/.wine_sims4studio}"
export WINEPREFIX
SIMS4STUDIO_URL="${SIMS4STUDIO_URL:-}"

echo "==> Wine prefix: $WINEPREFIX"
wineboot --init

if ! command -v winetricks >/dev/null 2>&1; then
  echo "winetricks nao encontrado -- instale winetricks antes de continuar." >&2
  exit 1
fi

echo "==> Instalando .NET Desktop Runtime 6 via winetricks"
winetricks -q dotnetdesktop6

if [ -z "$SIMS4STUDIO_URL" ]; then
  echo "AVISO: SIMS4STUDIO_URL nao definido -- pulando download do instalador." >&2
  echo "Defina SIMS4STUDIO_URL com o link atual de download em https://sims4studio.com" >&2
  echo "(nao fixamos aqui um link de instalador de terceiros sem confirmar que" >&2
  echo "ainda resolve -- confirme a URL vigente antes de automatizar)." >&2
  exit 0
fi

mkdir -p "$(dirname "$0")/downloads"
INSTALLER_PATH="$(dirname "$0")/downloads/Sims4Studio_setup.exe"
echo "==> Baixando Sims4Studio de $SIMS4STUDIO_URL"
curl -fsSL "$SIMS4STUDIO_URL" -o "$INSTALLER_PATH"

echo "==> Instalando Sims4Studio (silent install, se suportado pelo instalador)"
wine "$INSTALLER_PATH" /VERYSILENT /SUPPRESSMSGBOXES || \
  echo "Instalador pode nao suportar silent install -- verifique manualmente." >&2

echo "==> Setup concluido. Proximo passo: build/wine_casp/automate_casp.py"
