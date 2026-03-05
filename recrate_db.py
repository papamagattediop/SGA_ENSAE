# ============================================================
#  SGA ENSAE — recreate_db.py
#  Supprime et recrée la base de données complète
#  A exécuter depuis la racine sga_ensae/
#  python recreate_db.py
# ============================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import shutil
from database import engine, SessionLocal, DB_PATH
from models import Base
from auth import hash_password
from models import User, RoleEnum, Filiere, Classe

print("=" * 55)
print("  SGA ENSAE — Recréation de la base de données")
print("=" * 55)

# ── 1. Supprimer l'ancien fichier SQLite ──────────────────
if os.path.exists(DB_PATH):
    # Sauvegarde avant suppression
    backup = DB_PATH + ".backup"
    shutil.copy2(DB_PATH, backup)
    print(f"[OK] Sauvegarde : {backup}")
    os.remove(DB_PATH)
    print(f"[OK] Ancienne BDD supprimée : {DB_PATH}")

# ── 2. Recréer toutes les tables ─────────────────────────
Base.metadata.create_all(bind=engine)
print("[OK] Tables recréées avec succès.")

# ── 3. Insérer les données de base ────────────────────────
db = SessionLocal()
try:
    # Compte admin par défaut
    admin = User(
        nom           = "ADMIN",
        prenom        = "SGA",
        email         = "admin@ensae.sn",
        password_hash = hash_password("admin123"),
        role          = RoleEnum.admin,
        is_active     = True,
    )
    db.add(admin)

    # Filières officielles ENSAE
    filieres = [
        Filiere(code="ISEP",    libelle="Ingenieur Statisticien Economiste Preparatoire", duree_ans=3),
        Filiere(code="ISE",     libelle="Ingenieur Statisticien Economiste",              duree_ans=3),
        Filiere(code="AS",      libelle="Analyste Statisticien",                          duree_ans=3),
        Filiere(code="MASTERS", libelle="Masters Specialises",                            duree_ans=1),
    ]
    for f in filieres:
        db.add(f)
    db.flush()

    # Classes par filière
    annee = "2025-2026"
    classes_data = [
        # ISEP (2 ans prépa) — ISEP3 n'existe pas, ISE1 CL = 1ère année commune
        ("ISEP 1",      "ISEP", 1, False),
        ("ISEP 2",      "ISEP", 2, False),
        # ISE (5 ans) — ISE1 CL = classe commune ISEP3 + ISE directs
        ("ISE 1 CL",    "ISE",  1, True ),   # Classe commune (ex-ISEP 3)
        ("ISE Math 1",  "ISE",  1, False),
        ("ISE Eco 1",   "ISE",  1, False),
        ("ISE 2",       "ISE",  2, True ),   # Classe commune (fusion Math+Eco)
        ("ISE 3",       "ISE",  3, False),
     
        # AS (3 ans)
        ("AS 1",         "AS",   1, False),
        ("AS 2",         "AS",   2, False),
        ("AS 3",         "AS",   3, False),
        # MASTERS
        ("MASTER ADEPP", "MASTERS", 1, False),
        ("MASTER AGRICOLE", "MASTERS", 1, False),
    ]

    fil_map = {f.code: f.id for f in filieres}
    for nom, fil_code, niveau, is_commune in classes_data:
        db.add(Classe(
            nom            = nom,
            filiere_id     = fil_map[fil_code],
            niveau         = niveau,
            is_commune     = is_commune,
            annee_scolaire = annee,
        ))

    db.commit()
    print("[OK] Compte admin créé  : admin@ensae.sn / admin123")
    print(f"[OK] {len(filieres)} filières insérées.")
    print(f"[OK] {len(classes_data)} classes insérées.")

except Exception as e:
    db.rollback()
    print(f"[ERREUR] {e}")
    raise
finally:
    db.close()

print("=" * 55)
print("  Base de données prête !")
print("  Lancez : python app.py")
print("=" * 55)