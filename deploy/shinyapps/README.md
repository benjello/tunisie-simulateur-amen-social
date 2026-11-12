# Déploiement sur shinyapps.io

Hébergement gratuit de l'app Shiny Amen social (compte shinyapps.io, sans carte
bancaire ; plan gratuit = 25 h actives/mois **partagées** avec les autres apps
du compte, 1 Go RAM). L'app calcule OpenFisca **en direct** dans le process
(`OPENFISCA_MODE=local`), réforme corrective intégrée : pas d'API HTTP séparée.

## Prérequis (une seule fois)

1. **Compte** sur https://www.shinyapps.io (Google/GitHub, sans carte).
2. **rsconnect-python** : déjà installé dans le venv du projet (`uv sync --group dev`).
3. **Autoriser le compte** — contient ton SECRET, à lancer dans TON terminal
   (depuis Account → Tokens sur shinyapps.io, bouton « Copy to clipboard »).
   Si le compte `benjello` est déjà enregistré (simulateurs de paie/pension),
   **cette étape est déjà faite** :

   ```bash
   .venv/bin/rsconnect add --account <compte> --name <compte> \
     --token <TOKEN> --secret <SECRET>
   ```

   > Le token/secret donnent accès à ton compte : ne les commite jamais. Tu peux
   > les révoquer/régénérer à tout moment depuis la page Tokens.

## Déployer (manuel)

```bash
deploy/shinyapps/push.sh <compte> [nom-app]
# ex :
deploy/shinyapps/push.sh benjello simulateur-amen-social-tunisie
```

Le script assemble un bundle propre (point d'entrée `app.py` qui force le mode
local + `app_main.py` + `openfisca_client.py` + `reform.py` + `requirements.txt`
+ cible Python 3.12) et lance `rsconnect deploy shiny`. L'URL publique s'affiche
à la fin. C'est une **application distincte** des simulateurs de paie et de
pension (même compte, nom différent), avec sa propre URL.

## Fichiers

- `app.py` — point d'entrée déploiement (force `OPENFISCA_MODE=local`).
- `requirements.txt` — dépendances (shiny, openfisca-tunisia, pandas, httpx).
- `push.sh` — assemble le bundle et déploie.

## Déploiement automatique (GitHub Actions)

Le workflow `.github/workflows/deploy.yml` déploie l'app à chaque push sur
`main` touchant `app/` ou `deploy/shinyapps/` (et manuellement via
*Actions → Deploy to shinyapps.io → Run workflow*).

**Configuration unique — définir 3 secrets GitHub** (Settings → Secrets and
variables → Actions → New repository secret) :

| Secret | Valeur |
|--------|--------|
| `SHINYAPPS_ACCOUNT` | ton compte, ex. `benjello` |
| `SHINYAPPS_TOKEN`   | le token (Account → Tokens sur shinyapps.io) |
| `SHINYAPPS_SECRET`  | le secret associé |

Ces valeurs sont chiffrées par GitHub et ne sont jamais exposées dans les logs.
Tant qu'elles ne sont pas définies, le job échoue proprement (rien n'est
déployé). Pour les changer : régénère le token sur shinyapps.io et mets à jour
le secret.

### Poser les secrets sans les ressaisir

`scripts/set_shinyapps_secrets.sh` lit les valeurs depuis `.env` (gitignoré) et
les pousse via `gh` :

```bash
cp .env.example .env && chmod 600 .env   # puis coller TOKEN/SECRET
scripts/set_shinyapps_secrets.sh benjello/tunisie-simulateur-amen-social
```

Le même token/secret shinyapps.io sert pour tous les simulateurs (compte unique
`benjello`) : le `.env` du simulateur de paie convient aussi, en lançant le
script depuis n'importe quel projet du groupe en ciblant ce repo.

## Limite du plan gratuit

25 h actives/mois (partagées entre toutes les apps du compte). Au-delà, l'app
est suspendue jusqu'au mois suivant. Pour un usage soutenu : plan payant
shinyapps.io, ou un VPS (voir `../README.md`).
