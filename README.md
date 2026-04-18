# veille-pqc — GitHub Automation Edition

Projet Python de veille sur :
- Post-Quantum Cryptography (PQC)
- crypto-agility
- migration / transition vers la cryptographie post-quantique
- normes, drafts, guidance et implémentations

Cette édition est pensée pour un usage **GitHub + cloud automation** :
- collecte quotidienne avec **GitHub Actions**,
- publication d'un **rapport HTML statique** sur **GitHub Pages**,
- stockage des sorties en **artifacts GitHub**,
- envoi optionnel d'un **e-mail automatique** via SMTP,
- exécution manuelle possible par secteur (`banque`, `santé`, `industrie`, `cloud`).

---

## Fonctionnalités

- Collecte multi-sources : RSS + pages web
- Déduplication et scoring
- Classement par catégorie : `standards`, `migration`, `implementation`, `research`
- Filtrage par secteurs : `banque`, `santé`, `industrie`, `cloud`
- Historique local SQLite
- Export Markdown + CSV + HTML
- Envoi e-mail via SMTP
- Dashboard Streamlit local
- GitHub Actions pour exécution planifiée
- GitHub Pages pour publication du rapport HTML
- Sources GitHub Releases (Atom)

---

## 1) Installation locale

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
```

---

## 2) Exécution locale

### Collecte simple

```bash
veille-pqc run
veille-pqc run --sector banque
```

### Export HTML statique

```bash
veille-pqc export-html
veille-pqc export-html --sector santé
```

### Bundle de publication

```bash
veille-pqc publish-bundle --bundle-dir dist_bundle
```

### Envoi e-mail

Configurer les variables SMTP :

```bash
export VEILLE_SMTP_HOST="smtp.gmail.com"
export VEILLE_SMTP_PORT="587"
export VEILLE_SMTP_USER="fal.abdoulahad@gmail.com"
export VEILLE_SMTP_PASSWORD="APP_PASSWORD"
export VEILLE_SMTP_FROM="fal.abdoulahad@gmail.com"
export VEILLE_SMTP_STARTTLS="true"
```

Puis :

```bash
veille-pqc send-mail --to fal.abdoulahad@gmail.com
veille-pqc send-mail --to fal.abdoulahad@gmail.com --sector banque
```

---

## 3) Dashboard Streamlit

```bash
streamlit run src/veille_pqc/dashboard/app.py
```

---

## 4) Structure des sorties

- `reports/veille_pqc.md` : rapport Markdown
- `reports/veille_pqc.csv` : export CSV
- `data/veille_pqc.db` : historique SQLite
- `site/index.html` : rapport HTML statique
- `dist_bundle/` : bundle de publication GitHub Pages / artifact

---

## 5) Déploiement GitHub sur `ccsArtifacts`

### Étape A — créer le dépôt

Sur ton compte GitHub `ccsArtifacts`, crée par exemple un dépôt nommé :

```text
veille-pqc
```

Puis pousse ce projet dedans.

### Étape B — activer GitHub Pages

Dans le dépôt :
- `Settings` → `Pages`
- Source : **GitHub Actions**

### Étape C — configurer les secrets GitHub Actions

Dans le dépôt :
- `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

Ajoute :

- `VEILLE_SMTP_HOST` = `smtp.gmail.com`
- `VEILLE_SMTP_PORT` = `587`
- `VEILLE_SMTP_USER` = `fal.abdoulahad@gmail.com`
- `VEILLE_SMTP_PASSWORD` = ton **App Password Google**
- `VEILLE_SMTP_FROM` = `fal.abdoulahad@gmail.com`
- `VEILLE_SMTP_STARTTLS` = `true`
- `VEILLE_MAIL_TO` = `fal.abdoulahad@gmail.com`

> Pour Gmail, utilise un **mot de passe d'application** et non ton mot de passe principal.

### Étape D — lancer le workflow

Le workflow principal est :

```text
.github/workflows/daily-veille.yml
```

Il exécute :
- la collecte,
- la génération du bundle HTML/CSV/Markdown/SQLite,
- l'upload des artifacts,
- le déploiement GitHub Pages,
- l'envoi d'e-mail si les secrets SMTP sont présents.

---

## 6) Planification GitHub Actions

Le workflow est planifié tous les jours à **08:00 Europe/Paris**.

Le fichier utilise :

```yaml
on:
  schedule:
    - cron: '0 8 * * *'
      timezone: 'Europe/Paris'
```

Tu peux aussi le lancer manuellement depuis l'onglet **Actions** avec un filtre de secteur.

---

## 7) URL attendues après déploiement

Si ton dépôt est `ccsArtifacts/veille-pqc`, la page sera typiquement publiée sur une URL de la forme :

```text
https://ccsartifacts.github.io/veille-pqc/
```

Le rapport HTML quotidien y sera visible après le premier run réussi.

---

## 8) Workflows inclus

### CI

```text
.github/workflows/ci.yml
```

Fait un smoke test de la CLI sur chaque push / pull request.

### Daily PQC Watch

```text
.github/workflows/daily-veille.yml
```

Fait l'exécution quotidienne en mode production cloud.

---

## 9) Secrets et sécurité

Bonnes pratiques minimales :
- ne jamais committer `.env`
- utiliser uniquement les **repository secrets** pour SMTP
- préférer un **compte e-mail dédié à la veille** si le projet devient partagé
- limiter les droits d'administration du dépôt
- garder le dépôt **privé** si les rapports deviennent sensibles

---

## 10) Sources surveillées

Le fichier `config/sources.yaml` inclut notamment :
- NIST PQC
- NSA / CNSA 2.0
- CISA
- ENISA
- ETSI
- IETF Datatracker
- PQCA
- arXiv
- GitHub Releases `liboqs`
- GitHub Releases `oqs-provider`

---

## 11) Commandes utiles

```bash
veille-pqc run
veille-pqc run --sector banque
veille-pqc export-html
veille-pqc publish-bundle --bundle-dir dist_bundle
veille-pqc send-mail --to fal.abdoulahad@gmail.com
```

---

## 12) Évolutions possibles

- Slack / Teams via webhook
- résumé plus fin par source
- enrichissement GitHub Releases / Issues / PRs
- scoring RSSI / COMEX
- tableaux de bord séparés par secteur
- génération d'un briefing exécutif hebdomadaire
# veillePQC
