# Déploiement

L'app Shiny Amen social calcule via OpenFisca-Tunisia avec une réforme
corrective intégrée (`app/reform.py`). La réforme doit tourner **dans le même
process** que l'app : le mode « moteur en direct » est donc le plus simple.

## Retenue : moteur en direct sur shinyapps.io (un seul service)

L'app importe `openfisca_tunisia`, applique la réforme et calcule **dans le même
process** (`OPENFISCA_MODE=local`). Rien d'autre à héberger. C'est l'approche des
simulateurs de paie et de pension. Voir
[`shinyapps/README.md`](shinyapps/README.md).

```bash
deploy/shinyapps/push.sh benjello simulateur-amen-social-tunisie
```

Le bundle inclut `reform.py` à côté de `openfisca_client.py` (le client importe
la réforme).

## Alternative : API OpenFisca hébergée séparément (deux services)

Héberger `openfisca serve -c openfisca_tunisia -r reform.amen_social_corrections`
(le module `reform` doit être sur le PYTHONPATH) et pointer l'app via
`OPENFISCA_API_URL=https://…` (mode `api`). Plus « pur » architecturalement, mais
deux services à maintenir et une API publique à exposer. Non outillé ici.

> Rappel : déploiement 100 % navigateur (GitHub Pages / WebAssembly) impossible
> tant qu'OpenFisca importe `pendulum`/`numexpr`/`psutil` (absents de Pyodide).
