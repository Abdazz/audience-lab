#!/usr/bin/env bash
# Imprime un document HTML en PDF A4 avec Chromium sans interface.
#
# Usage : scripts/generer_pdf.sh <entrée.html> <sortie.pdf>
#
# Les numéros de page du pied viennent du CSS (@page). Si le document contient une
# table des matières à numéroter (attributs data-cible), le script fait deux passages :
# le premier sert à repérer la page de chaque section (scripts/numeroter_sommaire.py,
# qui utilise pdftotext), le second imprime la version numérotée.
# Le navigateur peut être choisi avec la variable CHROMIUM.
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage : $0 <entrée.html> <sortie.pdf>" >&2
  exit 2
fi

if [ ! -f "$1" ]; then
  echo "Erreur : fichier d'entrée introuvable : $1" >&2
  exit 1
fi

entree="$(realpath "$1")"
sortie="$(realpath -m "$2")"
dossier_scripts="$(cd "$(dirname "$0")" && pwd)"
navigateur="${CHROMIUM:-$(command -v chromium || command -v chromium-browser || command -v google-chrome || true)}"
if [ -z "$navigateur" ] || [ ! -x "$navigateur" ]; then
  echo "Erreur : aucun navigateur Chromium trouvé (chromium, chromium-browser ou google-chrome)." >&2
  echo "Installez-en un ou indiquez son chemin dans la variable CHROMIUM, par exemple : CHROMIUM=/usr/bin/chromium $0 <entrée.html> <sortie.pdf>" >&2
  exit 1
fi

imprimer() {
  # Le budget de temps virtuel laisse aux polices web (Inter) et aux images le temps de charger.
  "$navigateur" --headless --disable-gpu --no-sandbox --no-pdf-header-footer \
    --run-all-compositor-stages-before-draw --virtual-time-budget=20000 \
    --print-to-pdf="$2" "file://$1" 2>/dev/null
}

if grep -q 'data-cible=' "$entree"; then
  temporaire_pdf="$(mktemp --suffix=.pdf)"
  # La copie numérotée reste à côté de l'original pour garder les chemins relatifs (figures, CSS).
  temporaire_html="$(dirname "$entree")/.sommaire_$$.html"
  trap 'rm -f "$temporaire_pdf" "$temporaire_html"' EXIT
  imprimer "$entree" "$temporaire_pdf"
  python3 "$dossier_scripts/numeroter_sommaire.py" "$entree" "$temporaire_pdf" "$temporaire_html"
  imprimer "$temporaire_html" "$sortie"
else
  imprimer "$entree" "$sortie"
fi

echo "PDF écrit : $sortie ($(pdfinfo "$sortie" 2>/dev/null | awk '/^Pages:/ {print $2}') pages)"
