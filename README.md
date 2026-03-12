<div align="center">

# SGA ENSAE
### Système de Gestion Académique

**Application web de gestion scolaire pour l'ENSAE Dakar**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Dash](https://img.shields.io/badge/Dash-2.17.0-00B4D8?style=flat-square&logo=plotly&logoColor=white)](https://dash.plotly.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat-square)](https://sqlalchemy.org)
[![SQLite](https://img.shields.io/badge/SQLite-dev-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-prod-336791?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Licence](https://img.shields.io/badge/Licence-Académique-006B3F?style=flat-square)](LICENSE)

---

*Projet académique — Analyste Statisticien · Data Science · 2025-2026*

</div>

---

## 📑 Table des matières

- [Présentation](#-présentation)
- [Fonctionnalités](#-fonctionnalités)
- [Stack technique](#-stack-technique)
- [Architecture du projet](#-architecture-du-projet)
- [Installation](#-installation)
- [Démarrage rapide](#-démarrage-rapide)
- [Peuplement des données fictives](#-peuplement-des-données-fictives)
- [Migration Excel → SQL](#-migration-excel--sql)
- [Rôles et accès](#-rôles-et-accès)
- [Modules applicatifs](#-modules-applicatifs)
- [Base de données](#-base-de-données)
- [Variables d'environnement](#-variables-denvironnement)
- [Commandes utiles](#-commandes-utiles)
- [Workflow planning](#-workflow-planning)
- [Sécurité](#-sécurité)
- [Auteurs](#-auteurs)

---

## 🧭 Présentation

Le **SGA ENSAE** remplace la gestion académique par fichiers Excel par une application web centralisée, robuste et multi-rôles, développée avec Python et Dash Plotly.

> **Contexte :** Projet de fin de formation — transformation d'un prototype Excel en application web full-stack avec base de données SQL, authentification sécurisée et génération automatique de bulletins PDF.

L'application couvre l'ensemble du cycle académique : de l'inscription des étudiants jusqu'à la génération des bulletins de notes, en passant par la planification des séances, l'appel numérique et le suivi pédagogique.

---

## ✨ Fonctionnalités

| Catégorie | Fonctionnalité |
|-----------|----------------|
| **Authentification** | Connexion multi-rôles avec sessions sécurisées |
| **Pédagogie** | Gestion CRUD des UE, modules, séances et présences |
| **Planning** | Calendrier interactif avec workflow de validation par e-mail |
| **Étudiants** | Fiches individuelles, taux d'assiduité, moyenne générale |
| **Notes** | Import/export Excel, calcul automatique des moyennes et rangs |
| **Bulletins** | Génération PDF par étudiant ou par classe entière |
| **Statistiques** | Graphiques Plotly — distribution des notes, absentéisme |
| **Administration** | Migration Excel → SQL, gestion utilisateurs, explorateur BDD |
| **Notifications** | E-mails automatiques pour le workflow planning |

---

## 🛠️ Stack technique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Langage | Python | 3.11+ |
| Framework web | Dash Plotly | 2.17.0 |
| Composants UI | Dash Bootstrap Components | 1.6.0 |
| ORM | SQLAlchemy | 2.0.30 |
| BDD développement | SQLite | intégré |
| BDD production | PostgreSQL | 15+ |
| Hachage mots de passe | bcrypt | — |
| Export PDF | ReportLab / FPDF2 | — |
| Excel I/O | openpyxl + pandas | — |
| Emails | smtplib | — |
| Variables d'env. | python-dotenv | — |

---

## 🗂️ Architecture du projet

```
sga_ensae/
│
├── app.py                    # Point d'entrée — init BDD, routing, navbar
├── models.py                 # Modèles SQLAlchemy (14 tables)
├── database.py               # SessionLocal, engine, DB_PATH
├── auth.py                   # hash_password, verify_password, require_auth
├── recreate_db.py            # Recréation BDD + données de base
├── seed_data.py              # Peuplement données fictives complètes
├── fix_doublons.py           # Nettoyage doublons classes/filières
├── requirements.txt
├── .env                      # ⚠️ Ne pas commiter
│
├── assets/
│   ├── navbar.css            # Menus déroulants CSS pur
│   └── img/
│       └── logo_ensae.png
│
├── components/
│   └── navbar.py             # Navbar multi-rôles dynamique
│
├── pages/
│   ├── login.py              # Authentification
│   ├── dashboard.py          # Tableau de bord + KPIs
│   ├── cours.py              # Gestion UE & Modules
│   ├── seances.py            # Cahier de texte + appel numérique
│   ├── etudiants.py          # Fiches étudiants + notes
│   ├── planning.py           # Calendrier interactif
│   ├── bulletins.py          # Génération bulletins PDF
│   ├── statistiques.py       # Graphiques analytiques
│   ├── admin.py              # Administration & migration
│   └── db.py                 # Explorateur BDD (admin)
│
└── utils/
    ├── migration.py          # Import Excel → SQL (7 feuilles)
    ├── mailer.py             # Notifications e-mail
    └── pdf_generator.py      # Génération bulletins PDF
```

---

## ⚙️ Installation

### Prérequis

- Python 3.11+
- pip
- Git

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/<votre-username>/sga_ensae.git
cd sga_ensae

# 2. Créer l'environnement virtuel
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt
```

### `requirements.txt`

```
dash>=2.17.0
dash-bootstrap-components>=1.6.0
sqlalchemy>=2.0.0
bcrypt
pandas
openpyxl
reportlab
fpdf2
python-dotenv
```

---

## 🚀 Démarrage rapide

```bash
# 1. Recréer la base de données (tables + admin + filières + classes + périodes)
python recreate_db.py

# 2. Lancer l'application
python app.py

# 3. Ouvrir dans le navigateur
# → http://127.0.0.1:8050
```

**Compte administrateur par défaut :**

| Rôle | E-mail | Mot de passe |
|------|--------|--------------|
| `admin` | `admin@ensae.sn` | `admin123` |

> ⚠️ **Changer ce mot de passe dès le premier démarrage** via la page Administration.

---

## 🌱 Peuplement des données fictives

Pour simuler l'application complète avec des données réalistes sur toutes les tables :

```bash
# 1. Recréer la base propre
python recreate_db.py

# 2. Importer étudiants, classes, responsables via Excel
python utils/migration.py --import migration_sga_ensae_complet.xlsx

# 3. Peupler toutes les autres tables
python seed_data.py

# 4. Lancer l'application
python app.py
```

Le script `seed_data.py` génère automatiquement :

| Table | Volume | Détail |
|-------|--------|--------|
| UE | ~43 | Unités d'enseignement par filière et semestre |
| Modules | ~86 | Avec enseignants et volumes horaires |
| Séances | ~1 050 | Datées avec thèmes pédagogiques |
| Présences | ~4 500 | Profil assiduité réaliste par étudiant (82–100 %) |
| Notes | ~2 000 | Devoir + Examen, distribution gaussienne |
| Bulletins | S1 & S2 | Moyenne, rang, appréciation automatique |
| Plannings | ~96 | 8 semaines × 12 classes (validé / soumis / brouillon) |

---

## 📥 Migration Excel → SQL

### Générer le template vierge

```bash
python utils/migration.py --template
# → crée template_migration_ensae.xlsx
```

### Structure du template (7 feuilles)

| Feuille | Colonnes principales | Couleur |
|---------|---------------------|---------|
| `Filieres` | Code · Libelle · Duree_ans | 🔵 Bleu |
| `Classes` | Nom · Code_Filiere · Niveau · Is_Commune · Annee_Scolaire | 🟢 Vert |
| `Etudiants` | Matricule · Nom · Prenom · Email · Date_Naissance · Nom_Classe · Filiere_Origine · Mot_de_passe | 🟠 Orange |
| `Resp_Filieres` | Nom · Prenom · Email · Mot_de_passe · Code_Filiere | 🩵 Cyan |
| `Resp_Classes` | Nom · Prenom · Email · Mot_de_passe · Nom_Classe · Type | 🟡 Ambre |
| `Delegues` | Nom_Classe · Matricule_Titulaire · Matricule_Suppleant | 🟣 Violet |
| `⚠️ Instructions` | Guide complet d'utilisation | 🔴 Rouge |

### Règles importantes

- **Ordre recommandé :** `Filieres` → `Classes` → `Etudiants` → `Resp_Filieres` → `Resp_Classes` → `Delegues`
- Mot de passe étudiant par défaut = **Matricule** (si laissé vide)
- `Type` dans `Resp_Classes` : `titulaire` ou `suppleant`
- Si l'e-mail d'un utilisateur existe déjà → **promotion automatique** sans doublon
- Dates au format `JJ/MM/AAAA` ou `AAAA-MM-JJ`

### Import via l'interface

1. Se connecter en tant qu'`admin`
2. Aller dans **Admin › Migration de données**
3. Glisser-déposer le fichier Excel
4. Vérifier le rapport : importés ✅ · avertissements 🟡 · erreurs 🔴

### Import en ligne de commande

```bash
python utils/migration.py --import migration_sga_ensae_complet.xlsx
```

---

## 👥 Rôles et accès

| Rôle | Description | Accès |
|------|-------------|-------|
| `admin` | Administrateur système | Tout — utilisateurs, BDD, migration, statistiques |
| `resp_filiere` | Responsable pédagogique | Cours, séances, étudiants, notes, bulletins, stats |
| `resp_classe` | Délégué titulaire ou suppléant | Séances de sa classe, absences, bulletins |
| `eleve` | Étudiant inscrit | Son bulletin, son planning, ses notes |

Chaque classe dispose de :
- 1 délégué **titulaire** (`est_titulaire = True`)
- 1 délégué **suppléant** (`est_titulaire = False`)

---

## 📦 Modules applicatifs

### `pages/login.py` — Authentification
Page de connexion. Crée la session `dcc.Store` avec `user_id`, `rôle`, `nom`, `prénom`.

### `pages/dashboard.py` — Tableau de bord
KPIs dynamiques (étudiants, cours, séances) et raccourcis adaptés au rôle connecté.

### `pages/cours.py` — Cours & UE
CRUD complet des Unités d'Enseignement et modules. Suivi de progression horaire en temps réel (heures effectuées / volume total prévu).

### `pages/seances.py` — Séances & Présences
Création de séance avec thème pédagogique. Appel numérique via checklist dynamique (coché = absent). Historique filtrable par date ou par cours.

### `pages/etudiants.py` — Gestion étudiants
Fiche individuelle : informations personnelles, taux d'assiduité, moyenne générale.
Workflow notes : **télécharger template → saisir → uploader → mise à jour automatique**.

### `pages/planning.py` — Planning hebdomadaire
Calendrier interactif des séances. Workflow de validation avec notifications e-mail automatiques.

### `pages/bulletins.py` — Bulletins PDF
Génération PDF par étudiant ou par classe entière. Inclut notes, coefficients, moyenne pondérée, rang et appréciations.

### `pages/statistiques.py` — Analyse & DataViz
Graphiques Plotly interactifs : distribution des notes (histogramme), évolution des moyennes, taux d'absentéisme par classe.

### `pages/admin.py` — Administration
Gestion des utilisateurs et rôles. Import Excel multi-feuilles avec rapport détaillé. Gestion des filières et classes. Désignation des délégués.

### `pages/db.py` — Explorateur BDD *(admin uniquement)*
Liste des 14 tables avec compteur d'enregistrements. Tableau paginé avec recherche textuelle, édition et suppression directe via modal.

---

## 🗄️ Base de données

### Schéma relationnel (14 tables)

```
users ──────────┬──► etudiants ──────┬──► presences ◄── seances ◄── modules
                ├──► resp_classes     └──► notes     ◄──────────────── modules
                ├──► resp_filieres
                ├──► seances (created_by)
                ├──► plannings (created_by)
                └──► bulletins (valide_par)

filieres ───────┬──► classes ─────────┬──► etudiants
                └──► resp_filieres    ├──► resp_classes
                                      ├──► planning_classes
                                      └──► periodes ──► ue ──► modules
                                                              └──► ue_classes

migration_logs  (standalone — historique imports)
```

### Filières ENSAE

| Code | Libellé | Durée |
|------|---------|-------|
| `ISEP` | Ingénieur Statisticien Économiste Préparatoire | 2 ans |
| `ISE` | Ingénieur Statisticien Économiste | 3 ans |
| `AS` | Analyste Statisticien | 3 ans |
| `MASTERS` | Masters Spécialisés | 1 an |

### Classes (12)

`ISEP 1` · `ISEP 2` · `ISE 1 CL` · `ISE Math 1` · `ISE ECO 1` · `ISE 2` · `ISE 3` · `AS 1` · `AS 2` · `AS 3` · `Master ADEPP` · `Master Agricole`

---

## 🌿 Variables d'environnement

Créer un fichier `.env` à la racine (**⚠️ ne jamais commiter**) :

```env
# Notifications e-mail
MAIL_ADDRESS=votre@gmail.com
MAIL_PASSWORD=votre_app_password_gmail
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587

# Base de données production (laisser vide pour SQLite en dev)
DATABASE_URL=
# Exemple PostgreSQL :
# DATABASE_URL=postgresql://user:password@localhost:5432/sga_ensae
```

> 💡 Pour Gmail, utiliser un [App Password](https://support.google.com/accounts/answer/185833) et non le mot de passe principal du compte.

---

## 💻 Commandes utiles

```bash
# Base de données
python recreate_db.py                              # Recréer la BDD complète ⚠️
python fix_doublons.py                             # Nettoyer les doublons

# Migration & données
python utils/migration.py --template               # Générer le template Excel
python utils/migration.py --import fichier.xlsx    # Importer depuis Excel
python seed_data.py                                # Peupler les données fictives

# Tests & débogage
python utils/mailer.py                             # Tester l'envoi d'e-mail
python utils/pdf_generator.py                      # Générer un bulletin PDF test
```

---

## 🗓️ Workflow planning

```
Resp. Classe
    │
    ├─ Crée un planning (brouillon)
    └─ Soumet le planning
              │
              ▼
    E-mail automatique ──► Resp. Filière
              │
              ▼
    Resp. Filière examine
              │
        ┌─────┴──────┐
        ▼            ▼
    ✅ Valide    ❌ Rejette / Modifie
        │            │
        ▼            ▼
    E-mail ──► Resp. Classe
        │
        ▼
    Séances confirmées dans le calendrier
    E-mails ──► Enseignants concernés
```

---

## 🔒 Sécurité

- Mots de passe hachés avec **bcrypt** — jamais stockés en clair
- Sessions client-side via `dcc.Store` — pas de cookie serveur
- Vérification du rôle à chaque callback via `require_auth()`
- Page `/db` accessible uniquement au rôle `admin`
- Validation des données à l'entrée (e-mails, matricules, doublons)
- Logs de toutes les opérations de migration dans `migration_logs`
- Fichier `.env` exclu du dépôt via `.gitignore`

---

## ✍️ Auteurs

<table>
  <tr>
    <td align="center">
      <strong>Papa Magatte Diop</strong><br>
      <sub>Analyste Statisticien · Data Science</sub><br>
      <sub>ENSAE Dakar · Promotion 2025-2026</sub>
    </td>
    <td align="center">
      <strong>Ndeye Khary Sall</strong><br>
      <sub>Analyste Statisticien · Data Science</sub><br>
      <sub>ENSAE Dakar · Promotion 2025-2026</sub>
    </td>
  </tr>
</table>

---

<div align="center">

**École Nationale de la Statistique et de l'Analyse Économique — Dakar**

*Projet académique · Data Visualisation · 2025-2026*

</div>
