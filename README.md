# SGA ENSAE — Système de Gestion Académique

> Application web de gestion scolaire pour l'ENSAE (École Nationale de la Statistique et de l'Analyse Économique) de Dakar — Python · Dash Plotly · SQLAlchemy · SQLite/PostgreSQL

---

## Table des matières

- [SGA ENSAE — Système de Gestion Académique](#sga-ensae--système-de-gestion-académique)
  - [Table des matières](#table-des-matières)
  - [Présentation](#présentation)
  - [Stack technique](#stack-technique)
  - [Structure du projet](#structure-du-projet)
  - [Installation](#installation)
    - [requirements.txt minimal](#requirementstxt-minimal)
  - [Démarrage rapide](#démarrage-rapide)
  - [Migration des données Excel](#migration-des-données-excel)
    - [Générer le template](#générer-le-template)
    - [Feuilles du template](#feuilles-du-template)
    - [Règles importantes](#règles-importantes)
    - [Import via l'interface](#import-via-linterface)
    - [Import en ligne de commande](#import-en-ligne-de-commande)
  - [Rôles et accès](#rôles-et-accès)
  - [Modules applicatifs](#modules-applicatifs)
    - [`pages/login.py`](#pagesloginpy)
    - [`pages/dashboard.py`](#pagesdashboardpy)
    - [`pages/cours.py`](#pagescourspy)
    - [`pages/seances.py`](#pagesseancespy)
    - [`pages/etudiants.py`](#pagesetudiantspy)
    - [`pages/bulletins.py`](#pagesbulletinspy)
    - [`pages/planning.py`](#pagesplanningpy)
    - [`pages/statistiques.py`](#pagesstatistiquespy)
    - [`pages/admin.py`](#pagesadminpy)
    - [`pages/db.py` *(admin uniquement)*](#pagesdbpy-admin-uniquement)
  - [Navbar et navigation](#navbar-et-navigation)
  - [Base de données](#base-de-données)
    - [Tables (14)](#tables-14)
    - [Filières ENSAE (par défaut)](#filières-ensae-par-défaut)
    - [Scripts BDD](#scripts-bdd)
  - [Commandes utiles](#commandes-utiles)
  - [Variables d'environnement](#variables-denvironnement)
  - [Workflow planning](#workflow-planning)
  - [Sécurité](#sécurité)
  - [Licence](#licence)

---

## Présentation

Le SGA ENSAE remplace la gestion académique par fichiers Excel par une application web centralisée avec :

- **Authentification multi-rôles** (Admin, Resp. Filière, Délégué, Étudiant)
- **Gestion des cours, séances et présences** avec appel numérique
- **Suivi des notes** via import/export Excel avec calcul automatique des moyennes
- **Génération de bulletins PDF** par étudiant ou par classe entière
- **Migration Excel → SQL** intelligente avec gestion des doublons
- **Explorateur de base de données** avec CRUD visuel pour l'administrateur
- **Navbar dynamique** avec menus déroulants CSS par catégorie selon le rôle

---

## Stack technique

| Composant       | Technologie               | Version  |
|-----------------|---------------------------|----------|
| Langage         | Python                    | 3.11+    |
| Framework web   | Dash Plotly               | 2.17.0   |
| Composants UI   | Dash Bootstrap Components | 1.6.0    |
| ORM             | SQLAlchemy                | 2.0.30   |
| BDD dev         | SQLite                    | intégré  |
| BDD prod        | PostgreSQL                | 15+      |
| Auth            | bcrypt                    | —        |
| Export PDF      | ReportLab / FPDF2         | —        |
| Excel I/O       | openpyxl + pandas         | —        |
| Emails          | smtplib                   | —        |

---

## Structure du projet

```
sga_ensae/
├── app.py                        # Point d'entrée Dash, init BDD, callback navbar
├── models.py                     # Modèles SQLAlchemy (toutes les tables)
├── database.py                   # SessionLocal, engine, DB_PATH
├── auth.py                       # hash_password, verify_password, require_auth
├── recreate_db.py                # Script recréation BDD + données de base
├── fix_doublons.py               # Script nettoyage doublons classes/filières
├── requirements.txt              # Dépendances Python
├── .env                          # Config email (ne pas commiter)
│
├── assets/
│   ├── navbar.css                # Styles navbar (menus déroulants CSS pur)
│   └── img/
│       └── logo_ensae.png        # Logo ENSAE
│
├── components/
│   └── navbar.py                 # Navbar multi-rôles avec dropdowns CSS
│
├── pages/
│   ├── login.py                  # Authentification
│   ├── dashboard.py              # Tableau de bord accueil
│   ├── cours.py                  # Gestion Cours & UE
│   ├── seances.py                # Séances + appel numérique + historique
│   ├── etudiants.py              # Fiches étudiants + notes + absentéisme
│   ├── planning.py               # Calendrier interactif des séances
│   ├── bulletins.py              # Génération bulletins PDF
│   ├── statistiques.py           # Graphiques et analyses
│   ├── admin.py                  # Administration utilisateurs, migration, filières
│   └── db.py                     # Explorateur base de données (admin uniquement)
│
└── utils/
    ├── migration.py              # Import Excel → SQL (multi-feuilles, 7 feuilles)
    ├── mailer.py                 # Notifications email automatiques
    └── pdf_generator.py          # Génération bulletins PDF
```

---

## Installation

```bash
# 1. Cloner le dépôt
git clone <url-repo>
cd sga_ensae

# 2. Créer l'environnement virtuel
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / Mac
source .venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt
```

### requirements.txt minimal

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

## Démarrage rapide

```bash
# 1. Initialiser la base de données (tables + compte admin + filières + classes)
python recreate_db.py

# 2. Lancer l'application
python app.py

# 3. Ouvrir dans le navigateur
# http://127.0.0.1:8050
```

**Compte admin par défaut :**

| Rôle  | Email              | Mot de passe |
|-------|--------------------|--------------|
| Admin | admin@ensae.sn     | admin123     |

> ⚠️ Changer le mot de passe admin après le premier démarrage via la page Administration.

---

## Migration des données Excel

### Générer le template

```bash
python utils/migration.py --template
# → crée template_migration_ensae.xlsx
```

### Feuilles du template

| Feuille          | Colonnes principales                                        | Couleur   |
|------------------|-------------------------------------------------------------|-----------|
| `Filieres`       | Code, Libelle, Duree_ans                                    | 🔵 Bleu   |
| `Classes`        | Nom, Code_Filiere, Niveau, Is_Commune, Annee_Scolaire       | 🟢 Vert   |
| `Etudiants`      | Matricule, Nom, Prenom, Email, Date_Naissance, Nom_Classe…  | 🟠 Orange |
| `Resp_Filieres`  | Nom, Prenom, Email, Mot_de_passe, Code_Filiere              | 🩵 Cyan   |
| `Resp_Classes`   | Nom, Prenom, Email, Mot_de_passe, Nom_Classe, Type          | 🟡 Ambre  |
| `Delegues`       | Nom_Classe, Matricule_Titulaire, Matricule_Suppleant        | 🟣 Violet |
| `⚠ Instructions` | Guide complet d'utilisation                                 | 🔴 Rouge  |

### Règles importantes

- Les lignes grisées commençant par `#` sont des **exemples** → supprimer avant import
- Ne jamais modifier les noms des colonnes (ligne 1)
- **Ordre recommandé** : Filieres → Classes → Etudiants → Resp_Filieres → Resp_Classes → Delegues
- Mot de passe par défaut pour les étudiants = **matricule** (modifiable après connexion)
- Si l'email d'un responsable existe déjà en base → **promotion automatique** sans doublon
- `Type` dans Resp_Classes : `titulaire` ou `suppleant`
- Dates : format `JJ/MM/AAAA` ou `AAAA-MM-JJ` (les deux acceptés)

### Import via l'interface

1. Se connecter en tant qu'admin
2. Aller dans **Administration > Migration de données**
3. Glisser-déposer le fichier Excel
4. Vérifier le rapport : lignes importées ✅ · avertissements 🟡 · erreurs 🔴

### Import en ligne de commande

```bash
python utils/migration.py --import mon_fichier.xlsx
```

---

## Rôles et accès

| Rôle            | Description                     | Accès                                              |
|-----------------|---------------------------------|----------------------------------------------------|
| `admin`         | Administrateur système          | Tout — utilisateurs, BDD, migration, stats         |
| `resp_filiere`  | Responsable pédagogique         | Cours, séances, étudiants, notes, bulletins, stats |
| `resp_classe`   | Délégué titulaire ou suppléant  | Séances de sa classe, absences, bulletins          |
| `eleve`         | Étudiant inscrit                | Son bulletin, son planning, ses notes              |

**Délégués par classe :**
- 1 délégué **titulaire** (`est_titulaire = True`)
- 1 délégué **suppléant** (`est_titulaire = False`)

---

## Modules applicatifs

### `pages/login.py`
Authentification. Crée la session `dcc.Store` avec user_id, rôle, nom, prénom.

### `pages/dashboard.py`
Tableau de bord accueil avec KPIs (étudiants, cours, séances) et accès rapides adaptés au rôle.

### `pages/cours.py`
CRUD complet des cours et UE. Suivi de progression horaire (heures effectuées / volume total prévu).

### `pages/seances.py`
Création de séance avec thème pédagogique. Appel numérique via checklist dynamique (coché = absent). Historique filtrable par date ou par cours.

### `pages/etudiants.py`
Fiche individuelle : informations personnelles, taux d'absentéisme, moyenne générale. Workflow notes : télécharger template → saisir → uploader → mise à jour automatique.

### `pages/bulletins.py`
Génération PDF par étudiant ou par classe. Inclut notes, coefficients, moyenne, rang, appréciations.

### `pages/planning.py`
Calendrier interactif. Workflow de validation : Resp. Classe propose → Resp. Filière valide/rejette avec notification email.

### `pages/statistiques.py`
Graphiques Plotly interactifs : distribution des notes, évolution des moyennes, absentéisme par classe.

### `pages/admin.py`
Gestion des utilisateurs et rôles. Import Excel multi-feuilles avec rapport détaillé. Gestion des filières et classes. Désignation des délégués (titulaire/suppléant).

### `pages/db.py` *(admin uniquement)*
Explorateur base de données : liste des 14 tables avec compteur, tableau paginé avec recherche textuelle, édition et suppression directe via modal.

---

## Navbar et navigation

Menus déroulants **CSS pur** (sans callbacks Dash) — styles dans `assets/navbar.css`.

| Menu            | Contenu                                  | Visible pour      |
|-----------------|------------------------------------------|-------------------|
| Accueil         | Dashboard                                | Tous              |
| Pédagogie ▾     | Cours & UE · Séances · Planning          | Admin, RF, RC     |
| Étudiants ▾     | Gestion · Bulletins                      | Admin, RF, RC     |
| Statistiques    | Graphiques analytiques                   | Admin, RF         |
| Admin ▾         | Utilisateurs · Base de données · Migration · Filières | Admin |
| Avatar ▾        | Nom · Rôle · Déconnexion                 | Tous              |

---

## Base de données

### Tables (14)

```
users            → etudiants, resp_classes, resp_filieres
filieres         → classes, resp_filieres
classes          → etudiants, resp_classes, plannings
modules          → seances, notes, plannings
seances          → presences
etudiants        → presences, notes
periodes         → modules
ue               → modules
migration_logs   (standalone — historique imports)
```

### Filières ENSAE (par défaut)

| Code    | Libellé                                          | Durée |
|---------|--------------------------------------------------|-------|
| ISEP    | Ingénieur Statisticien Économiste Préparatoire   | 2 ans |
| ISE     | Ingénieur Statisticien Économiste                | 3 ans |
| AS      | Analyste Statisticien                            | 3 ans |
| MASTERS | Masters Spécialisés                              | 1 an  |

### Scripts BDD

```bash
# Recréer la BDD complète (⚠ supprime toutes les données)
python recreate_db.py

# Nettoyer les doublons classes/filières
python fix_doublons.py
```

---

## Commandes utiles

```bash
# Générer le template de migration Excel
python utils/migration.py --template

# Importer des données depuis Excel (CLI)
python utils/migration.py --import fichier.xlsx

# Recréer la BDD avec données de base
python recreate_db.py

# Nettoyer les doublons en base
python fix_doublons.py

# Tester l'envoi d'email
python utils/mailer.py

# Générer un bulletin PDF (test)
python utils/pdf_generator.py
```

---

## Variables d'environnement

Créer un fichier `.env` à la racine (**ne jamais commiter**) :

```env
# Email (notifications automatiques)
MAIL_ADDRESS=votre@gmail.com
MAIL_PASSWORD=votre_app_password
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587

# Base de données production PostgreSQL (laisser vide pour SQLite en dev)
DATABASE_URL=
# Exemple PostgreSQL : postgresql://user:password@localhost/sga_ensae
```

---

## Workflow planning

```
Resp. Classe   →  Crée / propose une séance
                          ↓
               Email automatique au Resp. Filière
                          ↓
Resp. Filière  →  Valide ✅  ou  Rejette ❌
                          ↓
               Email automatique au Resp. Classe
                          ↓
            Séance confirmée dans le calendrier
```

---

## Sécurité

- Mots de passe hachés avec **bcrypt** (jamais stockés en clair)
- Sessions client-side via `dcc.Store` (pas de cookie serveur)
- Vérification du rôle à chaque callback via `require_auth()`
- Page `/db` accessible uniquement au rôle `admin`
- Validation des données à l'entrée (emails, matricules, doublons)
- Logs de toutes les opérations de migration dans `migration_logs`

---

## Licence

Projet académique — ENSAE Dakar · 2025-2026   
Auteurs :   
-   Papa Magatte Diop   
-   Ndeye Khary Sall    
Analyste Statisticien option Data Science