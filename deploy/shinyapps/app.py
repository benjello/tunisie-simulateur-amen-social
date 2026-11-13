"""Point d'entrée pour le déploiement shinyapps.io.

Force le mode « moteur en direct » (OpenFisca calculé dans le process avec la
réforme corrective, sans API HTTP séparée) AVANT d'importer le code de l'app,
puis expose l'objet `app`.

Le dossier `app/` du dépôt est copié ici au déploiement (voir push.sh), de sorte
que ce fichier, `app_main.py`, `openfisca_client.py` et `reform.py` soient dans
le même répertoire.
"""

import os

os.environ.setdefault("OPENFISCA_MODE", "local")
os.environ.setdefault("MPLBACKEND", "Agg")  # matplotlib sans affichage (PDF/graphe)

# Les modules openfisca_client / reform sont copiés à côté de ce fichier.
from app_main import app  # noqa: E402,F401
