# ============================================================
#  SGA ENSAE — utils/migration.py
#  Import initial depuis Excel vers la base SQL
#  Python 3.11 · SQLAlchemy 2.0.30
# ============================================================

import sys
import os

# Ajouter le dossier racine du projet au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import io
import base64
from datetime import datetime
from database import SessionLocal
from models import (
    Filiere, Classe, User, Etudiant, RoleEnum,
    MigrationLog, StatutMigrationEnum
)
from auth import hash_password


# ============================================================
#  UTILITAIRES
# ============================================================

def log_migration(fichier: str, statut: str, details: str):
    """Enregistre un log de migration dans la base."""
    db = SessionLocal()
    try:
        db.add(MigrationLog(
            fichier     = fichier,
            date_import = datetime.now(),
            statut      = StatutMigrationEnum.succes if statut == "succes" else StatutMigrationEnum.erreur,
            details     = details
        ))
        db.commit()
    finally:
        db.close()


def parse_excel(contents: str) -> pd.ExcelFile:
    """Decode un fichier Excel base64 en ExcelFile pandas."""
    _, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    return pd.ExcelFile(io.BytesIO(decoded))


# ============================================================
#  MIGRATION FILIERES
# ============================================================

def migrate_filieres(df: pd.DataFrame) -> tuple[int, list]:
    """
    Colonnes attendues :
    Code, Libelle, Duree_ans
    """
    db  = SessionLocal()
    nb  = 0
    err = []
    try:
        for _, row in df.iterrows():
            try:
                code = str(row["Code"]).strip()
                if db.query(Filiere).filter(Filiere.code == code).first():
                    err.append(f"Filiere '{code}' existe deja — ignoree.")
                    continue
                db.add(Filiere(
                    code      = code,
                    libelle   = str(row["Libelle"]).strip(),
                    duree_ans = int(row["Duree_ans"])
                ))
                nb += 1
            except Exception as e:
                err.append(f"Filiere ligne {_ + 2} : {str(e)}")
        db.commit()
    except Exception as e:
        db.rollback()
        err.append(f"Erreur globale filieres : {str(e)}")
    finally:
        db.close()
    return nb, err


# ============================================================
#  MIGRATION CLASSES
# ============================================================

def migrate_classes(df: pd.DataFrame) -> tuple[int, list]:
    """
    Colonnes attendues :
    Nom, Code_Filiere, Niveau, Is_Commune (0/1), Annee_Scolaire
    """
    db  = SessionLocal()
    nb  = 0
    err = []
    try:
        for _, row in df.iterrows():
            try:
                nom = str(row["Nom"]).strip()
                filiere = db.query(Filiere).filter(
                    Filiere.code == str(row["Code_Filiere"]).strip()
                ).first()
                if not filiere:
                    err.append(f"Filiere '{row['Code_Filiere']}' introuvable pour classe '{nom}'.")
                    continue
                if db.query(Classe).filter(
                    Classe.nom == nom,
                    Classe.annee_scolaire == str(row["Annee_Scolaire"]).strip()
                ).first():
                    err.append(f"Classe '{nom}' existe deja — ignoree.")
                    continue
                db.add(Classe(
                    nom            = nom,
                    filiere_id     = filiere.id,
                    niveau         = int(row["Niveau"]),
                    is_commune     = bool(int(row.get("Is_Commune", 0))),
                    annee_scolaire = str(row["Annee_Scolaire"]).strip()
                ))
                nb += 1
            except Exception as e:
                err.append(f"Classe ligne {_ + 2} : {str(e)}")
        db.commit()
    except Exception as e:
        db.rollback()
        err.append(f"Erreur globale classes : {str(e)}")
    finally:
        db.close()
    return nb, err


# ============================================================
#  MIGRATION ETUDIANTS
# ============================================================

def migrate_etudiants(df: pd.DataFrame) -> tuple[int, list]:
    """
    Colonnes attendues :
    Matricule, Nom, Prenom, Email, Date_Naissance (JJ/MM/AAAA),
    Nom_Classe, Annee_Scolaire, Filiere_Origine
    """
    db  = SessionLocal()
    nb  = 0
    err = []
    try:
        for _, row in df.iterrows():
            try:
                email     = str(row["Email"]).strip().lower()
                matricule = str(row["Matricule"]).strip()

                if db.query(User).filter(User.email == email).first():
                    err.append(f"Email '{email}' deja utilise — ignore.")
                    continue
                if db.query(Etudiant).filter(Etudiant.matricule == matricule).first():
                    err.append(f"Matricule '{matricule}' deja utilise — ignore.")
                    continue

                classe = db.query(Classe).filter(
                    Classe.nom == str(row["Nom_Classe"]).strip(),
                    Classe.annee_scolaire == str(row["Annee_Scolaire"]).strip()
                ).first()
                if not classe:
                    err.append(f"Classe '{row['Nom_Classe']}' introuvable pour etudiant '{matricule}'.")
                    continue

                # Date naissance
                date_naissance = None
                if pd.notna(row.get("Date_Naissance")):
                    try:
                        date_naissance = datetime.strptime(
                            str(row["Date_Naissance"]).strip(), "%d/%m/%Y"
                        ).date()
                    except Exception:
                        err.append(f"Date invalide pour '{matricule}' — ignoree.")

                # Mot de passe par defaut = matricule
                user = User(
                    nom           = str(row["Nom"]).strip().upper(),
                    prenom        = str(row["Prenom"]).strip(),
                    email         = email,
                    password_hash = hash_password(matricule),
                    role          = RoleEnum.eleve,
                    is_active     = True
                )
                db.add(user)
                db.flush()

                etudiant = Etudiant(
                    user_id         = user.id,
                    matricule       = matricule,
                    date_naissance  = date_naissance,
                    classe_id       = classe.id,
                    filiere_origine = str(row.get("Filiere_Origine", "")).strip(),
                    annee_scolaire  = str(row["Annee_Scolaire"]).strip()
                )
                db.add(etudiant)
                nb += 1

            except Exception as e:
                err.append(f"Etudiant ligne {_ + 2} : {str(e)}")

        db.commit()
    except Exception as e:
        db.rollback()
        err.append(f"Erreur globale etudiants : {str(e)}")
    finally:
        db.close()
    return nb, err


# ============================================================
#  MIGRATION COMPLETE DEPUIS UN FICHIER EXCEL
# ============================================================

def migrate_from_excel(contents: str, filename: str) -> dict:
    """
    Import complet depuis un fichier Excel multi-feuilles.

    Feuilles supportees :
    - Filieres  : Code, Libelle, Duree_ans
    - Classes   : Nom, Code_Filiere, Niveau, Is_Commune, Annee_Scolaire
    - Etudiants : Matricule, Nom, Prenom, Email, Date_Naissance,
                  Nom_Classe, Annee_Scolaire, Filiere_Origine

    Retourne un dict avec les resultats par feuille.
    """
    resultats = {}
    toutes_erreurs = []

    try:
        xl = parse_excel(contents)

        if "Filieres" in xl.sheet_names:
            df = xl.parse("Filieres")
            nb, err = migrate_filieres(df)
            resultats["Filieres"] = {"nb": nb, "erreurs": err}
            toutes_erreurs.extend(err)

        if "Classes" in xl.sheet_names:
            df = xl.parse("Classes")
            nb, err = migrate_classes(df)
            resultats["Classes"] = {"nb": nb, "erreurs": err}
            toutes_erreurs.extend(err)

        if "Etudiants" in xl.sheet_names:
            df = xl.parse("Etudiants")
            nb, err = migrate_etudiants(df)
            resultats["Etudiants"] = {"nb": nb, "erreurs": err}
            toutes_erreurs.extend(err)

        statut  = "succes" if not toutes_erreurs else "erreur"
        details = f"{len(toutes_erreurs)} avertissement(s). " + " | ".join(toutes_erreurs[:5])
        log_migration(filename, statut, details)

    except Exception as e:
        log_migration(filename, "erreur", str(e))
        resultats["global"] = {"nb": 0, "erreurs": [f"Erreur fatale : {str(e)}"]}

    return resultats


# ============================================================
#  GENERATION TEMPLATE MIGRATION EXCEL
# ============================================================

def generate_migration_template() -> bytes:
    """
    Genere un template Excel complet pour la migration initiale.
    Feuilles : Filieres, Classes, Etudiants
    """
    from openpyxl.styles import PatternFill, Font, Alignment
    import openpyxl

    wb = openpyxl.Workbook()

    sheets = {
        "Filieres": {
            "columns" : ["Code", "Libelle", "Duree_ans"],
            "exemple" : [
                ["ISEP",    "Ingenieur Statisticien Economiste et Planificateur", 3],
                ["ISE",     "Ingenieur Statisticien Economiste",                  5],
                ["AS",      "Adjoint Statisticien",                               3],
                ["MASTERS", "Masters specialises",                                1],
            ],
            "couleur" : "003580"
        },
        "Classes": {
            "columns" : ["Nom", "Code_Filiere", "Niveau", "Is_Commune", "Annee_Scolaire"],
            "exemple" : [
                ["ISEP 1",      "ISEP",    1, 0, "2024-2025"],
                ["ISE Math 1",  "ISE",     1, 0, "2024-2025"],
                ["ISE 2",       "ISE",     2, 1, "2024-2025"],
                ["AS 1",        "AS",      1, 0, "2024-2025"],
            ],
            "couleur" : "006B3F"
        },
        "Etudiants": {
            "columns" : [
                "Matricule", "Nom", "Prenom", "Email",
                "Date_Naissance", "Nom_Classe", "Annee_Scolaire", "Filiere_Origine"
            ],
            "exemple" : [
                ["ENSAE-2024-001", "DIALLO",  "Amadou", "adiallo@ensae.sn",
                 "15/09/2002", "ISE Math 1", "2024-2025", "ISE Math"],
                ["ENSAE-2024-002", "NDIAYE",  "Fatou",  "fndiaye@ensae.sn",
                 "20/03/2001", "ISEP 1",     "2024-2025", "ISEP"],
            ],
            "couleur" : "F5A623"
        }
    }

    # Supprimer la feuille par defaut
    wb.remove(wb.active)

    for sheet_name, cfg in sheets.items():
        ws = wb.create_sheet(sheet_name)

        # En-tetes
        for col_idx, col_name in enumerate(cfg["columns"], 1):
            cell       = ws.cell(row=1, column=col_idx, value=col_name)
            cell.fill  = PatternFill("solid", fgColor=cfg["couleur"])
            cell.font  = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal="center")

        # Exemples
        for row_idx, row_data in enumerate(cfg["exemple"], 2):
            for col_idx, val in enumerate(row_data, 1):
                ws.cell(row=row_idx, column=col_idx, value=val)

        # Largeur colonnes
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = 22

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.read()


# ============================================================
#  SCRIPT STANDALONE
# ============================================================

if __name__ == "__main__":
    """
    Utilisation en ligne de commande :
    python utils/migration.py --template
    python utils/migration.py --import fichier.xlsx
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage : python migration.py --template | --import <fichier.xlsx>")
        sys.exit(1)

    if sys.argv[1] == "--template":
        data = generate_migration_template()
        with open("template_migration_ensae.xlsx", "wb") as f:
            f.write(data)
        print("[OK] Template genere : template_migration_ensae.xlsx")

    elif sys.argv[1] == "--import" and len(sys.argv) >= 3:
        filepath = sys.argv[2]
        print(f"[...] Import depuis {filepath}")
        with open(filepath, "rb") as f:
            raw = f.read()
        b64 = "data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64," + \
              base64.b64encode(raw).decode()
        resultats = migrate_from_excel(b64, filepath)
        for feuille, res in resultats.items():
            print(f"  {feuille} : {res['nb']} importe(s)")
            for e in res["erreurs"]:
                print(f"    [!] {e}")
        print("[OK] Migration terminee.")