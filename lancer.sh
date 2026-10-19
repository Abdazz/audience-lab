#!/usr/bin/env bash
# Lance Audience Lab en local, en une seule commande : ./lancer.sh
#
# Au premier lancement, le script crée l'environnement virtuel .venv et installe
# les dépendances de requirements.txt. Les lancements suivants démarrent
# directement l'application.
#
# Les dépendances exigent Python 3.12 ou plus récent. Si la machine n'en dispose
# pas, le script utilise uv (https://docs.astral.sh/uv/) pour obtenir Python 3.12
# sans droits administrateur ; uv est installé dans ~/.local/bin s'il est absent.
set -euo pipefail

cd "$(dirname "$0")"

VERSION_MIN="3.12"
PORT="${PORT:-8501}"

# Renvoie 0 si l'interpréteur donné existe et est au moins en version 3.12.
python_compatible() {
    command -v "$1" >/dev/null 2>&1 &&
        "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' 2>/dev/null
}

# Cherche un Python 3.12+ déjà installé sur la machine.
trouver_python() {
    for candidat in python3.14 python3.13 python3.12 python3; do
        if python_compatible "$candidat"; then
            echo "$candidat"
            return 0
        fi
    done
    return 1
}

creer_environnement() {
    local python
    if python="$(trouver_python)"; then
        echo "Python compatible trouvé : $("$python" --version)"
        if ! "$python" -m venv .venv 2>/dev/null; then
            echo "Le module venv est absent. Sous Debian ou Ubuntu : sudo apt install python3-venv" >&2
            echo "Tentative avec uv à la place..." >&2
            rm -rf .venv
            creer_avec_uv
            return
        fi
        .venv/bin/python -m pip install --quiet --upgrade pip
        .venv/bin/python -m pip install --quiet -r requirements.txt
    else
        echo "Aucun Python $VERSION_MIN ou plus récent n'a été trouvé sur cette machine."
        creer_avec_uv
    fi
}

creer_avec_uv() {
    if ! command -v uv >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/uv" ]; then
        echo "Installation de uv dans ~/.local/bin (sans droits administrateur)..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
    local uv_bin
    uv_bin="$(command -v uv || echo "$HOME/.local/bin/uv")"
    "$uv_bin" venv --python "$VERSION_MIN" .venv
    "$uv_bin" pip install --python .venv/bin/python -r requirements.txt
}

if [ ! -x .venv/bin/streamlit ]; then
    echo "Premier lancement : préparation de l'environnement (quelques minutes)..."
    rm -rf .venv
    creer_environnement
    echo "Environnement prêt."
fi

echo "Démarrage d'Audience Lab sur http://localhost:$PORT (Ctrl+C pour arrêter)"
# headless false : ouvre automatiquement le navigateur (la configuration du
# dépôt est en mode headless pour le déploiement en ligne).
exec .venv/bin/streamlit run app.py --server.port "$PORT" --server.headless false
