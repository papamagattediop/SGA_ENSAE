# ============================================================
#  SGA ENSAE — recreate_db.py
#  Supprime et recrée la base de données complète
#  A exécuter depuis la racine sga_ensae/
#  python recreate_db.py
# ============================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import shutil
from datetime import date
from database import engine, SessionLocal, DB_PATH
from models import Base
from auth import hash_password
from models import User, RoleEnum, Filiere, Classe, Periode

print("=" * 55)
print("  SGA ENSAE — Recréation de la base de données")
print("=" * 55)

# ── 1. Supprimer l'ancien fichier SQLite ──────────────────
if os.path.exists(DB_PATH):
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
    annee = "2025-2026"

    # ── Compte admin par défaut ───────────────────────────
    admin = User(
        nom           = "ADMIN",
        prenom        = "SGA",
        email         = "admin@ensae.sn",
        password_hash = hash_password("admin123"),
        role          = RoleEnum.admin,
        is_active     = True,
    )
    db.add(admin)

    # ── Filières officielles ENSAE ────────────────────────
    filieres = [
        Filiere(code="ISEP",    libelle="Ingenieur Statisticien Economiste Preparatoire", duree_ans=2),
        Filiere(code="ISE",     libelle="Ingenieur Statisticien Economiste",              duree_ans=3),
        Filiere(code="AS",      libelle="Analyste Statisticien",                          duree_ans=3),
        Filiere(code="MASTERS", libelle="Masters Specialises",                            duree_ans=1),
    ]
    for f in filieres:
        db.add(f)
    db.flush()

    # ── Classes par filière ───────────────────────────────
    classes_data = [
        ("ISEP 1",         "ISEP",    1, False),
        ("ISEP 2",         "ISEP",    2, False),
        ("ISE 1 CL",       "ISE",     1, True ),
        ("ISE Math 1",     "ISE",     1, False),
        ("ISE Eco 1",      "ISE",     1, False),
        ("ISE 2",          "ISE",     2, True ),
        ("ISE 3",          "ISE",     3, False),
        ("AS 1",           "AS",      1, False),
        ("AS 2",           "AS",      2, False),
        ("AS 3",           "AS",      3, False),
        ("MASTER ADEPP",   "MASTERS", 1, False),
        ("MASTER AGRICOLE","MASTERS", 1, False),
    ]

    fil_map = {f.code: f.id for f in filieres}
    classes_objets = []
    for nom, fil_code, niveau, is_commune in classes_data:
        c = Classe(
            nom            = nom,
            filiere_id     = fil_map[fil_code],
            niveau         = niveau,
            is_commune     = is_commune,
            annee_scolaire = annee,
        )
        db.add(c)
        classes_objets.append(c)

    db.flush()  # génère les IDs des classes avant d'insérer les périodes

    # ── Périodes : Semestre 1 et Semestre 2 pour chaque classe ──
    #
    #  IMPORTANT : la table `periodes` a un champ classe_id obligatoire.
    #  Sans ces entrées, l'import Excel UE/Modules échoue avec
    #  "Periode introuvable".
    #
    periodes_data = [
        ("Semestre 1", date(2025, 10,  1), date(2026,  2, 28)),
        ("Semestre 2", date(2026,  3,  1), date(2026,  7, 31)),
    ]

    nb_periodes = 0
    for classe in classes_objets:
        for libelle, debut, fin in periodes_data:
            db.add(Periode(
                libelle        = libelle,
                classe_id      = classe.id,
                date_debut     = debut,
                date_fin       = fin,
                est_cloturee   = False,
                annee_scolaire = annee,
            ))
            nb_periodes += 1

    db.commit()

    print(f"[OK] Compte admin créé   : admin@ensae.sn / admin123")
    print(f"[OK] {len(filieres)} filières insérées.")
    print(f"[OK] {len(classes_objets)} classes insérées.")
    print(f"[OK] {nb_periodes} périodes insérées "
          f"({len(periodes_data)} par classe × {len(classes_objets)} classes).")

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