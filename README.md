# SGA ENSAE — Systeme de Gestion Academique

## Structure du projet

```
sga_ensae/
├── app.py                        # Point d'entree Dash
├── models.py                     # Modeles SQLAlchemy
├── database.py                   # Connexion BDD + init
├── auth.py                       # Authentification
├── requirements.txt              # Dependances Python
├── .env                          # Config email (ne pas commiter)
│
├── assets/
│   └── img/
│       └── logo_ensae.png        # Logo ENSAE
│
├── components/
│   └── navbar.py                 # Barre de navigation
│
├── pages/
│   ├── login.py                  # Connexion
│   ├── dashboard.py              # Tableau de bord
│   ├── cours.py                  # Gestion UE et modules
│   ├── seances.py                # Cahier de texte + presences
│   ├── etudiants.py              # Fiche etudiants + notes
│   ├── planning.py               # Planning hebdomadaire
│   ├── bulletins.py              # Bulletins de notes
│   ├── statistiques.py           # Graphiques et analyses
│   └── admin.py                  # Administration
│
└── utils/
    ├── migration.py              # Import Excel -> SQL
    ├── mailer.py                 # Notifications email
    └── pdf_generator.py          # Generation bulletins PDF
```

## Installation

```bash
# 1. Creer l'environnement virtuel
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac

# 2. Installer les dependances
pip install -r requirements.txt

# 3. Configurer le fichier .env
MAIL_ADDRESS=votre@gmail.com
MAIL_PASSWORD=votre_app_password

# 4. Lancer l'application
python app.py
```

## Comptes par defaut

| Role            | Email              | Mot de passe |
|-----------------|--------------------|--------------|
| Admin           | admin@ensae.sn     | admin123     |

## Commandes utiles

```bash
# Generer le template de migration
python utils/migration.py --template

# Importer des donnees depuis Excel
python utils/migration.py --import fichier.xlsx

# Tester l'envoi d'email
python utils/mailer.py

# Generer un bulletin PDF (test)
python utils/pdf_generator.py
```

## Workflow planning

```
Resp. Classe  →  Propose planning  →  Email au Resp. Filiere
Resp. Filiere →  Valide / Rejete   →  Email au Resp. Classe
```

## Roles utilisateurs

| Role           | Acces                                          |
|----------------|------------------------------------------------|
| admin          | Tout                                           |
| resp_filiere   | Valider plannings, stats, bulletins            |
| resp_classe    | Cours, seances, etudiants, planning, bulletins |
| eleve          | Notes, absences, bulletin personnel            |