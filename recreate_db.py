# ============================================================
#  SGA ENSAE — recreate_db.py
#  Supprime et recrée la base de données complète
#  À exécuter depuis la racine du projet : python recreate_db.py
#
#  v2 — Mis à jour :
#    · Module.email_enseignant inclus via models.py
#    · Durées corrigées : ISE = 3 ans, ISEP = 2 ans
# ============================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import shutil
from datetime import date
from database import engine, SessionLocal, DB_PATH
from models import Base
from auth import hash_password
from models import User, RoleEnum, Filiere, Classe, Periode

print("=" * 60)
print("  SGA ENSAE — Recréation de la base de données  v2")
print("=" * 60)

# ── 1. Sauvegarde + suppression de l'ancienne BDD SQLite ──
if os.path.exists(DB_PATH):
    backup = DB_PATH + ".backup"
    shutil.copy2(DB_PATH, backup)
    print(f"[OK] Sauvegarde créée       : {backup}")
    os.remove(DB_PATH)
    print(f"[OK] Ancienne BDD supprimée : {DB_PATH}")
else:
    print("[INFO] Aucune BDD existante — création from scratch.")

# ── 2. Recréer toutes les tables (inclut email_enseignant) ─
Base.metadata.create_all(bind=engine)
print("[OK] Tables recréées avec succès (colonne email_enseignant incluse).")

# ── 3. Insérer les données de base ─────────────────────────
db = SessionLocal()
try:
    annee = "2025-2026"

    # ── Compte admin par défaut ─────────────────────────────
    admin = User(
        nom           = "ADMIN",
        prenom        = "SGA",
        email         = "admin@ensae.sn",
        password_hash = hash_password("admin123"),
        role          = RoleEnum.admin,
        is_active     = True,
    )
    db.add(admin)

    # ── Filières officielles ENSAE ──────────────────────────
    # Durées corrigées : ISEP=2 ans · ISE=3 ans · AS=3 ans · MASTERS=1 an
    filieres = [
        Filiere(code="ISEP",    libelle="Ingenieur Statisticien Economiste Preparatoire", duree_ans=2),
        Filiere(code="ISE",     libelle="Ingenieur Statisticien Economiste",              duree_ans=3),
        Filiere(code="AS",      libelle="Analyste Statisticien",                          duree_ans=3),
        Filiere(code="MASTERS", libelle="Masters Specialises",                            duree_ans=1),
    ]
    for f in filieres:
        db.add(f)
    db.flush()

    # ── Classes par filière ─────────────────────────────────
    # (nom, code_filiere, niveau, is_commune)
    classes_data = [
        ("ISEP 1",          "ISEP",    1, False),
        ("ISEP 2",          "ISEP",    2, False),
        ("ISE 1 CL",        "ISE",     1, True ),   # classe commune 1ère année
        ("ISE Math 1",      "ISE",     1, False),
        ("ISE Eco 1",       "ISE",     1, False),
        ("ISE 2",           "ISE",     2, True ),   # classe commune 2ème année
        ("ISE 3",           "ISE",     3, False),
        ("AS 1",            "AS",      1, False),
        ("AS 2",            "AS",      2, False),
        ("AS 3",            "AS",      3, False),
        ("MASTER ADEPP",    "MASTERS", 1, False),
        ("MASTER AGRICOLE", "MASTERS", 1, False),
    ]

    fil_map        = {f.code: f.id for f in filieres}
    classes_objets = []

    for nom_cls, fil_code, niveau, is_commune in classes_data:
        c = Classe(
            nom            = nom_cls,
            filiere_id     = fil_map[fil_code],
            niveau         = niveau,
            is_commune     = is_commune,
            annee_scolaire = annee,
        )
        db.add(c)
        classes_objets.append(c)

    db.flush()  # génère les IDs avant d'insérer les périodes

    # ── Périodes : Semestre 1 et Semestre 2 pour chaque classe ─
    #
    #  IMPORTANT : periodes.classe_id est obligatoire.
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

    print(f"[OK] Admin créé            : admin@ensae.sn  /  admin123")
    print(f"[OK] Filières insérées     : {len(filieres)}")
    print(f"     ISEP=2 ans · ISE=3 ans · AS=3 ans · MASTERS=1 an")
    print(f"[OK] Classes insérées      : {len(classes_objets)}")
    print(f"[OK] Périodes insérées     : {nb_periodes}"
          f"  ({len(periodes_data)} × {len(classes_objets)} classes)")

except Exception as e:
    db.rollback()
    print(f"[ERREUR] {e}")
    raise
finally:
    db.close()

print()
print("=" * 60)
print("  Base de données prête !")
print()
print("  → Configurez .env (MAIL_ADDRESS + MAIL_PASSWORD)")
print("  → Lancez      : python app.py")
print("  → Ouvrez      : http://127.0.0.1:8050")
print()
print("  Compte admin : admin@ensae.sn  /  admin123")
print("  ⚠  Changez ce mot de passe dès la première connexion !")
print("=" * 60)