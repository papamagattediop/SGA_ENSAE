"""
SGA ENSAE — seed_data.py
Script de peuplement complet de la base de données avec données fictives.
Couvre : UE, Modules, Séances, Présences, Notes, Bulletins, Plannings
À placer à la racine du projet et exécuter : python seed_data.py
IMPORTANT : Lancer APRÈS recreate_db.py + migration Excel (étudiants/classes/users)
"""

import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, time, datetime, timedelta
from database import SessionLocal
from models import (
    Classe, Etudiant, User, Periode,
    UE, UEClasse, Module,
    Seance, Presence,
    Note, TypeEvalEnum,
    Bulletin,
    Planning, PlanningClasse, PlanningSeance, StatutPlanningEnum,
    RoleEnum,
)

random.seed(42)
db = SessionLocal()

print("=" * 60)
print("  SGA ENSAE — Peuplement données fictives")
print("=" * 60)

# ── helpers ──────────────────────────────────────────────────
def note_realiste(moyenne_cible=12, ecart=3):
    n = random.gauss(moyenne_cible, ecart)
    return round(max(0, min(20, n)), 2)

def lundi_semaine(d):
    return d - timedelta(days=d.weekday())

# ── Récupération des objets existants ────────────────────────
classes   = {c.nom: c for c in db.query(Classe).all()}
etudiants = {e.matricule: e for e in db.query(Etudiant).all()}
periodes  = db.query(Periode).all()
admin_user = db.query(User).filter(User.role == RoleEnum.admin).first()
admin_id   = admin_user.id if admin_user else 1

print(f"[INFO] Classes trouvées   : {len(classes)}")
print(f"[INFO] Étudiants trouvés  : {len(etudiants)}")
print(f"[INFO] Périodes trouvées  : {len(periodes)}")

# Index périodes par (classe_id, libelle)
periode_map = {(p.classe_id, p.libelle): p for p in periodes}

# ════════════════════════════════════════════════════════════
#  CATALOGUE PÉDAGOGIQUE PAR FILIÈRE
#  Structure : { "Nom_Classe": [ (UE_code, UE_libelle, coef_ue, periode_lib,
#                                 [(mod_code, mod_libelle, coef, enseignant, email, vh)]) ] }
# ════════════════════════════════════════════════════════════

ENSEIGNANTS = {
    "stat":   ("Dr. Ibrahima DIALLO",     "ibrahima.diallo@ensae.sn"),
    "maths":  ("Pr. Fatou SECK",          "fatou.seck@ensae.sn"),
    "info":   ("Dr. Moussa FALL",         "moussa.fall@ensae.sn"),
    "eco":    ("Dr. Aminata NDIAYE",      "aminata.ndiaye@ensae.sn"),
    "demo":   ("Pr. Cheikh SARR",         "cheikh.sarr@ensae.sn"),
    "compta": ("Dr. Rokhaya DEME",        "rokhaya.deme@ensae.sn"),
    "sondage":("Dr. Pape DIOP",           "pape.diop@ensae.sn"),
    "macro":  ("Pr. Oumar GUEYE",         "oumar.gueye@ensae.sn"),
    "prog":   ("Dr. Ndèye TOURE",         "ndeye.toure@ensae.sn"),
    "ml":     ("Dr. Alioune KANE",        "alioune.kane@ensae.sn"),
    "dataviz":("Dr. Mariama BALDE",       "mariama.balde@ensae.sn"),
    "sgbd":   ("Dr. Thierno CAMARA",      "thierno.camara@ensae.sn"),
}

CATALOGUE = {
    "ISEP 1": [
        ("UE-MATH1", "Mathématiques 1", 3, "Semestre 1", [
            ("MOD-ALG1",  "Algèbre Linéaire",       2, *ENSEIGNANTS["maths"], 30),
            ("MOD-ANAL1", "Analyse Mathématique",   2, *ENSEIGNANTS["maths"], 30),
            ("MOD-PROBA", "Probabilités",           2, *ENSEIGNANTS["stat"],  25),
        ]),
        ("UE-INFO1", "Informatique 1", 2, "Semestre 1", [
            ("MOD-ALGO1", "Algorithmique",          2, *ENSEIGNANTS["info"],  25),
            ("MOD-PY1",   "Python Initiation",     2, *ENSEIGNANTS["prog"],  25),
        ]),
        ("UE-ECO1",  "Économie Générale", 2, "Semestre 1", [
            ("MOD-MICRO1","Microéconomie",          2, *ENSEIGNANTS["eco"],   25),
            ("MOD-MACRO1","Macroéconomie",          1, *ENSEIGNANTS["macro"], 20),
        ]),
        ("UE-STAT1", "Statistiques Descriptives", 3, "Semestre 2", [
            ("MOD-STAT1", "Stat Desc Univariée",    2, *ENSEIGNANTS["stat"],  25),
            ("MOD-STAT2", "Stat Desc Bivariée",     2, *ENSEIGNANTS["stat"],  25),
            ("MOD-SOND1", "Introduction Sondages",  1, *ENSEIGNANTS["sondage"],20),
        ]),
        ("UE-MATH2", "Mathématiques 2", 2, "Semestre 2", [
            ("MOD-ALG2",  "Algèbre II",             2, *ENSEIGNANTS["maths"], 25),
            ("MOD-OPTIM", "Optimisation",           1, *ENSEIGNANTS["maths"], 20),
        ]),
    ],
    "ISEP 2": [
        ("UE-STAT3", "Inférence Statistique", 3, "Semestre 1", [
            ("MOD-INFER1","Estimation",              2, *ENSEIGNANTS["stat"],  30),
            ("MOD-INFER2","Tests d'Hypothèses",     2, *ENSEIGNANTS["stat"],  30),
        ]),
        ("UE-REGR1", "Modèles de Régression", 3, "Semestre 1", [
            ("MOD-REG1",  "Régression Linéaire Simple", 2, *ENSEIGNANTS["stat"], 25),
            ("MOD-REG2",  "Régression Multiple",     2, *ENSEIGNANTS["stat"],  25),
        ]),
        ("UE-INFO2", "Informatique 2", 2, "Semestre 1", [
            ("MOD-PY2",   "Python Avancé",          2, *ENSEIGNANTS["prog"],  25),
            ("MOD-BD1",   "Bases de Données SQL",   2, *ENSEIGNANTS["sgbd"],  25),
        ]),
        ("UE-DEMO1", "Démographie", 2, "Semestre 2", [
            ("MOD-DEM1",  "Démographie Générale",   2, *ENSEIGNANTS["demo"],  25),
            ("MOD-DEM2",  "Tables de Mortalité",    1, *ENSEIGNANTS["demo"],  20),
        ]),
        ("UE-MACRO2","Macroéconomie Avancée", 2, "Semestre 2", [
            ("MOD-MAC2",  "Comptabilité Nationale", 2, *ENSEIGNANTS["macro"], 25),
            ("MOD-MAC3",  "Politique Économique",   1, *ENSEIGNANTS["eco"],   20),
        ]),
    ],
    "ISE 1 CL": [
        ("UE-ANAL2", "Analyse Avancée", 3, "Semestre 1", [
            ("MOD-ANAL2", "Séries Numériques",       2, *ENSEIGNANTS["maths"], 30),
            ("MOD-ANAL3", "Intégration Lebesgue",   2, *ENSEIGNANTS["maths"], 30),
        ]),
        ("UE-PROBA2","Probabilités Avancées", 3, "Semestre 1", [
            ("MOD-PRB2",  "Variables Aléatoires",   2, *ENSEIGNANTS["stat"],  30),
            ("MOD-PRB3",  "Processus Stochastiques",2, *ENSEIGNANTS["stat"],  25),
        ]),
        ("UE-ECO2",  "Économétrie I", 3, "Semestre 2", [
            ("MOD-ECO2",  "Économétrie des MCC",    2, *ENSEIGNANTS["eco"],   30),
            ("MOD-ECO3",  "MCO et Propriétés",      2, *ENSEIGNANTS["eco"],   30),
        ]),
        ("UE-INFO3", "Programmation Stat", 2, "Semestre 2", [
            ("MOD-R1",    "Langage R",              2, *ENSEIGNANTS["prog"],  25),
            ("MOD-SAS1",  "SAS Initiation",         2, *ENSEIGNANTS["info"],  25),
        ]),
    ],
    "ISE 2": [
        ("UE-ECO4",  "Économétrie II", 3, "Semestre 1", [
            ("MOD-TSERIES","Séries Temporelles",    3, *ENSEIGNANTS["eco"],   35),
            ("MOD-PANEL",  "Données de Panel",      2, *ENSEIGNANTS["eco"],   30),
        ]),
        ("UE-SOND2", "Théorie des Sondages", 3, "Semestre 1", [
            ("MOD-SOND2", "Sondage Aléatoire Simple",2, *ENSEIGNANTS["sondage"],25),
            ("MOD-SOND3", "Sondage Stratifié",      2, *ENSEIGNANTS["sondage"],25),
        ]),
        ("UE-ML1",   "Machine Learning I", 3, "Semestre 2", [
            ("MOD-ML1",   "Supervision — Classif.", 2, *ENSEIGNANTS["ml"],    30),
            ("MOD-ML2",   "Supervision — Régress.", 2, *ENSEIGNANTS["ml"],    30),
        ]),
        ("UE-VIZ1",  "Data Visualisation", 2, "Semestre 2", [
            ("MOD-VIZ1",  "Plotly & Dash",          2, *ENSEIGNANTS["dataviz"],25),
            ("MOD-VIZ2",  "Tableaux de Bord",       1, *ENSEIGNANTS["dataviz"],20),
        ]),
    ],
    "ISE 3": [
        ("UE-ML2",   "Machine Learning II", 3, "Semestre 1", [
            ("MOD-ML3",   "Forêts Aléatoires",      2, *ENSEIGNANTS["ml"],    30),
            ("MOD-ML4",   "Réseaux de Neurones",    2, *ENSEIGNANTS["ml"],    30),
        ]),
        ("UE-MEMOIREISE","Mémoire & Stage", 4, "Semestre 2", [
            ("MOD-MEM1",  "Méthodologie Recherche", 1, *ENSEIGNANTS["stat"],  15),
            ("MOD-STAGE1","Stage Professionnel",    3, *ENSEIGNANTS["eco"],   40),
        ]),
        ("UE-SOND3", "Méthodes d'Enquête", 3, "Semestre 1", [
            ("MOD-ENQUETE","Conception d'Enquêtes", 2, *ENSEIGNANTS["sondage"],25),
            ("MOD-TRAITEMENT","Traitement & Analyse",2,*ENSEIGNANTS["stat"],  25),
        ]),
    ],
    "AS 1": [
        ("UE-MATH-AS1","Mathématiques AS 1", 3, "Semestre 1", [
            ("MOD-MATAS1","Algèbre & Analyse",      2, *ENSEIGNANTS["maths"], 30),
            ("MOD-PROBAS1","Probabilités AS",       2, *ENSEIGNANTS["stat"],  25),
        ]),
        ("UE-STAT-AS1","Statistiques AS 1", 3, "Semestre 1", [
            ("MOD-STAS1", "Statistiques Desc.",     2, *ENSEIGNANTS["stat"],  25),
            ("MOD-STAS2", "Tableaux Croisés",       1, *ENSEIGNANTS["stat"],  20),
        ]),
        ("UE-INFO-AS1","Informatique AS 1", 2, "Semestre 2", [
            ("MOD-INFAS1","Excel Avancé",           1, *ENSEIGNANTS["info"],  20),
            ("MOD-INFAS2","Python pour Stat",       2, *ENSEIGNANTS["prog"],  25),
        ]),
    ],
    "AS 2": [
        ("UE-ECO-AS2","Économétrie AS", 3, "Semestre 1", [
            ("MOD-ECOAS1","Régression Appliquée",   2, *ENSEIGNANTS["eco"],   30),
            ("MOD-ECOAS2","Analyse de Variance",    1, *ENSEIGNANTS["stat"],  20),
        ]),
        ("UE-DEMO-AS2","Démographie AS", 2, "Semestre 1", [
            ("MOD-DEMAS1","Pop. & Développement",  2, *ENSEIGNANTS["demo"],  25),
        ]),
        ("UE-COMPTA1","Comptabilité", 2, "Semestre 2", [
            ("MOD-CPT1",  "Comptabilité Générale", 2, *ENSEIGNANTS["compta"],25),
            ("MOD-CPT2",  "Analyse Financière",    1, *ENSEIGNANTS["compta"],20),
        ]),
    ],
    "AS 3": [
        ("UE-SOND-AS3","Sondages Appliqués", 3, "Semestre 1", [
            ("MOD-SNDAS1","Techniques de Sondage", 2, *ENSEIGNANTS["sondage"],30),
            ("MOD-SNDAS2","Calage & Redressement", 2, *ENSEIGNANTS["sondage"],25),
        ]),
        ("UE-MEM-AS3","Mémoire AS", 4, "Semestre 2", [
            ("MOD-MEMAS3","Stage & Mémoire",       4, *ENSEIGNANTS["stat"],  40),
        ]),
    ],
    "MASTER ADEPP": [
        ("UE-ADEPP1","Politiques Publiques", 4, "Semestre 1", [
            ("MOD-PP1",   "Évaluation Politiques", 2, *ENSEIGNANTS["eco"],   30),
            ("MOD-PP2",   "Méthodes d'Impact",     2, *ENSEIGNANTS["stat"],  30),
            ("MOD-PP3",   "Économie du Dvpt",      2, *ENSEIGNANTS["macro"], 25),
        ]),
        ("UE-ADEPP2","Outils Quantitatifs", 3, "Semestre 1", [
            ("MOD-QT1",   "Modèles Multi-niveaux", 2, *ENSEIGNANTS["stat"],  25),
            ("MOD-QT2",   "Méthodes Mixtes",       2, *ENSEIGNANTS["eco"],   25),
        ]),
        ("UE-ADEPP3","Mémoire ADEPP", 5, "Semestre 2", [
            ("MOD-MADP1", "Stage & Mémoire",       5, *ENSEIGNANTS["eco"],   50),
        ]),
    ],
    "MASTER AGRICOLE": [
        ("UE-AGRI1","Économie Agricole", 4, "Semestre 1", [
            ("MOD-AG1",   "Marchés Agricoles",     2, *ENSEIGNANTS["eco"],   30),
            ("MOD-AG2",   "Politiques Agricoles",  2, *ENSEIGNANTS["macro"], 30),
            ("MOD-AG3",   "Stat Agricoles",        2, *ENSEIGNANTS["stat"],  25),
        ]),
        ("UE-AGRI2","Outils d'Analyse", 3, "Semestre 1", [
            ("MOD-AGRA1", "SIG & Cartographie",    2, *ENSEIGNANTS["info"],  25),
            ("MOD-AGRA2", "Analyse de Données",    2, *ENSEIGNANTS["dataviz"],25),
        ]),
        ("UE-AGRI3","Mémoire Agricole", 5, "Semestre 2", [
            ("MOD-MAGRI1","Stage & Mémoire",       5, *ENSEIGNANTS["eco"],   50),
        ]),
    ],
}

# Pour ISE Math 1 et ISE Eco 1 — clone simplifié d'ISE 1 CL
CATALOGUE["ISE Math 1"] = CATALOGUE["ISE 1 CL"]
CATALOGUE["ISE Eco 1"]  = CATALOGUE["ISE 1 CL"]

# ════════════════════════════════════════════════════════════
#  CRÉATION UE + MODULES
# ════════════════════════════════════════════════════════════
print("\n[1/6] Création des UE et Modules...")

ue_map     = {}   # (classe_nom, ue_code) → UE
module_map = {}   # (classe_nom, mod_code) → Module

for classe_nom, ues_data in CATALOGUE.items():
    cls = classes.get(classe_nom)
    if not cls:
        print(f"  [WARN] Classe introuvable : {classe_nom}")
        continue

    for ue_code, ue_lib, coef_ue, periode_lib, modules_data in ues_data:
        periode = periode_map.get((cls.id, periode_lib))
        if not periode:
            print(f"  [WARN] Période '{periode_lib}' introuvable pour {classe_nom}")
            continue

        # Éviter doublons UE (code unique par période)
        existing_ue = db.query(UE).filter(
            UE.code == ue_code, UE.periode_id == periode.id
        ).first()
        if existing_ue:
            ue = existing_ue
        else:
            ue = UE(code=ue_code, libelle=ue_lib, coefficient=coef_ue, periode_id=periode.id)
            db.add(ue)
            db.flush()

        ue_map[(classe_nom, ue_code)] = ue

        # Liaison UE ↔ Classe
        from sqlalchemy.exc import IntegrityError
        try:
            ue_cls = UEClasse(ue_id=ue.id, classe_id=cls.id)
            db.add(ue_cls)
            db.flush()
        except Exception:
            db.rollback()

        # Modules
        for mod_code, mod_lib, coef_mod, ens_nom, ens_email, vol_h in modules_data:
            existing_mod = db.query(Module).filter(
                Module.code == mod_code, Module.classe_id == cls.id
            ).first()
            if existing_mod:
                module_map[(classe_nom, mod_code)] = existing_mod
                continue
            mod = Module(
                code             = mod_code,
                libelle          = mod_lib,
                coefficient      = coef_mod,
                enseignant       = ens_nom,
                email_enseignant = ens_email,
                volume_horaire   = vol_h,
                ue_id            = ue.id,
                classe_id        = cls.id,
            )
            db.add(mod)
            db.flush()
            module_map[(classe_nom, mod_code)] = mod

db.commit()
nb_ue  = db.query(UE).count()
nb_mod = db.query(Module).count()
print(f"  [OK] UE créées    : {nb_ue}")
print(f"  [OK] Modules créés : {nb_mod}")

# ════════════════════════════════════════════════════════════
#  SÉANCES (cahier de texte)
# ════════════════════════════════════════════════════════════
print("\n[2/6] Création des Séances...")

THEMES = {
    "MOD-ALG1":   ["Introduction aux espaces vectoriels","Matrices et déterminants","Diagonalisation","Formes quadratiques"],
    "MOD-STAT1":  ["Séries statistiques","Mesures de tendance centrale","Mesures de dispersion","Boîtes à moustaches"],
    "MOD-PY1":    ["Variables et types","Structures de contrôle","Fonctions et modules","Pandas introduction"],
    "MOD-ECO2":   ["Hypothèses MCO","Estimation OLS","Tests de Student","Multicolinéarité"],
    "MOD-TSERIES":["Processus ARMA","Test de Dickey-Fuller","Modèle ARIMA","Prévision"],
    "MOD-ML1":    ["KNN","Régression Logistique","SVM","Évaluation — matrice confusion"],
    "default":    ["Introduction au cours","Rappels et prérequis","Cours — partie 1","Cours — partie 2",
                   "Exercices d'application","Correction TD","Révisions","Évaluation formative"],
}

creneaux = [
    (time(8, 0),  time(10, 0)),
    (time(10, 0), time(12, 0)),
    (time(14, 0), time(16, 0)),
    (time(16, 0), time(18, 0)),
]

# Générer séances du 06/10/2025 au 28/02/2026 (Sem 1) + 02/03 au 30/05/2026 (Sem 2)
date_ranges = [
    (date(2025, 10, 6),  date(2026, 2, 27)),
    (date(2026, 3, 2),   date(2026, 5, 29)),
]

seance_map = {}  # module_id → [seance_id]

for classe_nom, cls in classes.items():
    if classe_nom not in CATALOGUE:
        continue
    etu_classe = [e for e in etudiants.values() if e.classe_id == cls.id]
    if not etu_classe:
        continue

    for ue_code, _, _, periode_lib, modules_data in CATALOGUE[classe_nom]:
        dr_idx = 0 if periode_lib == "Semestre 1" else 1
        d_start, d_end = date_ranges[dr_idx]

        for mod_code, mod_lib, *_ in modules_data:
            mod = module_map.get((classe_nom, mod_code))
            if not mod:
                continue

            # Générer 4 à 8 séances par module sur la période
            nb_seances = random.randint(4, 8)
            total_days  = (d_end - d_start).days
            jours_cours  = sorted(random.sample(range(0, total_days, 7), min(nb_seances, total_days // 7)))

            for j in jours_cours:
                d = d_start + timedelta(days=j)
                if d.weekday() >= 5:  # pas weekend
                    d += timedelta(days=2)
                creneau = random.choice(creneaux)
                themes  = THEMES.get(mod_code, THEMES["default"])
                theme   = random.choice(themes)

                s = Seance(
                    module_id   = mod.id,
                    date        = d,
                    heure_debut = creneau[0],
                    heure_fin   = creneau[1],
                    theme       = theme,
                    created_by  = admin_id,
                )
                db.add(s)
                db.flush()

                seance_map.setdefault(mod.id, []).append((s.id, etu_classe))

db.commit()
nb_seances = db.query(Seance).count()
print(f"  [OK] Séances créées : {nb_seances}")

# ════════════════════════════════════════════════════════════
#  PRÉSENCES
# ════════════════════════════════════════════════════════════
print("\n[3/6] Création des Présences...")

# Chaque étudiant a un "profil assiduité" : 0.85 à 1.0 de présence
profil_etu = {e.id: random.uniform(0.82, 1.0) for e in etudiants.values()}

presences_bulk = []
for mod_id, seances_list in seance_map.items():
    for seance_id, etu_liste in seances_list:
        for e in etu_liste:
            present = random.random() < profil_etu.get(e.id, 0.9)
            presences_bulk.append(Presence(
                seance_id   = seance_id,
                etudiant_id = e.id,
                present     = present,
            ))

db.bulk_save_objects(presences_bulk)
db.commit()
print(f"  [OK] Présences créées : {len(presences_bulk)}")

# ════════════════════════════════════════════════════════════
#  NOTES
# ════════════════════════════════════════════════════════════
print("\n[4/6] Création des Notes...")

# Profil notes par étudiant : niveau moyen + écart
profil_notes = {e.id: (random.uniform(8, 17), random.uniform(2, 4))
                for e in etudiants.values()}

notes_bulk = []
for classe_nom, cls in classes.items():
    if classe_nom not in CATALOGUE:
        continue
    etu_classe = [e for e in etudiants.values() if e.classe_id == cls.id]
    if not etu_classe:
        continue

    for ue_code, _, _, _, modules_data in CATALOGUE[classe_nom]:
        for mod_code, *_ in modules_data:
            mod = module_map.get((classe_nom, mod_code))
            if not mod:
                continue

            for e in etu_classe:
                moy_cible, ecart = profil_notes.get(e.id, (12, 3))
                # Devoir (note 1)
                notes_bulk.append(Note(
                    etudiant_id = e.id,
                    module_id   = mod.id,
                    note        = note_realiste(moy_cible, ecart),
                    type_eval   = TypeEvalEnum.devoir,
                    numero      = 1,
                ))
                # Examen (note 2) — pas pour les stages
                if "STAGE" not in mod_code and "MEM" not in mod_code:
                    notes_bulk.append(Note(
                        etudiant_id = e.id,
                        module_id   = mod.id,
                        note        = note_realiste(moy_cible, ecart),
                        type_eval   = TypeEvalEnum.examen,
                        numero      = 2,
                    ))

db.bulk_save_objects(notes_bulk)
db.commit()
print(f"  [OK] Notes créées : {len(notes_bulk)}")

# ════════════════════════════════════════════════════════════
#  BULLETINS
# ════════════════════════════════════════════════════════════
print("\n[5/6] Création des Bulletins...")

bulletins_bulk = []
for cls in classes.values():
    etu_classe = [e for e in etudiants.values() if e.classe_id == cls.id]
    if not etu_classe:
        continue

    for libelle_p in ["Semestre 1", "Semestre 2"]:
        periode = periode_map.get((cls.id, libelle_p))
        if not periode:
            continue

        # Calculer moyenne par étudiant pour ce semestre
        moyennes = []
        for e in etu_classe:
            # Récupérer modules de cette classe sur cette période
            ue_ids = [u.id for u in db.query(UE).filter(UE.periode_id == periode.id).all()]
            mod_ids = [m.id for m in db.query(Module).filter(
                Module.classe_id == cls.id, Module.ue_id.in_(ue_ids)
            ).all()] if ue_ids else []

            if not mod_ids:
                moy = round(random.uniform(8, 17), 2)
            else:
                notes_e = db.query(Note).filter(
                    Note.etudiant_id == e.id,
                    Note.module_id.in_(mod_ids)
                ).all()
                if notes_e:
                    moy = round(sum(n.note for n in notes_e) / len(notes_e), 2)
                else:
                    moy = round(random.uniform(8, 17), 2)
            moyennes.append((e.id, moy))

        # Trier pour rang
        moyennes_sorted = sorted(moyennes, key=lambda x: x[1], reverse=True)
        rang_map = {eid: i+1 for i, (eid, _) in enumerate(moyennes_sorted)}

        for e in etu_classe:
            moy = next((m for eid, m in moyennes if eid == e.id), 10.0)
            assiduite = round(profil_etu.get(e.id, 0.9) * 100, 1)

            if moy >= 16:   appre = "Excellent — félicitations"
            elif moy >= 14: appre = "Très bien — continuez vos efforts"
            elif moy >= 12: appre = "Bien — résultats satisfaisants"
            elif moy >= 10: appre = "Assez bien — peut mieux faire"
            else:           appre = "Insuffisant — des efforts sont nécessaires"

            bulletins_bulk.append(Bulletin(
                etudiant_id     = e.id,
                periode_id      = periode.id,
                moyenne_gen     = moy,
                rang            = rang_map.get(e.id, 1),
                taux_assiduite  = assiduite,
                appreciation    = appre,
                valide_par      = admin_id,
                genere_le       = datetime(2026, 1, 15) if libelle_p == "Semestre 1" else datetime(2026, 6, 20),
                envoye_par_mail = False,
            ))

db.bulk_save_objects(bulletins_bulk)
db.commit()
print(f"  [OK] Bulletins créés : {len(bulletins_bulk)}")

# ════════════════════════════════════════════════════════════
#  PLANNINGS HEBDOMADAIRES
# ════════════════════════════════════════════════════════════
print("\n[6/6] Création des Plannings...")

# Semaines du semestre 1
semaines_s1 = []
d = lundi_semaine(date(2025, 10, 6))
while d <= date(2026, 2, 23):
    semaines_s1.append(d)
    d += timedelta(weeks=1)

# On génère un planning pour chaque classe, chaque semaine (S1 uniquement pour ne pas surcharger)
nb_plannings = 0
for classe_nom, cls in classes.items():
    if classe_nom not in CATALOGUE:
        continue
    mods = [m for (cn, mc), m in module_map.items() if cn == classe_nom]
    if not mods:
        continue

    # Trouver le resp_classe titulaire
    from models import ResponsableClasse
    rc = db.query(ResponsableClasse).filter(
        ResponsableClasse.classe_id == cls.id,
        ResponsableClasse.est_titulaire == True
    ).first()
    createur_id = rc.user_id if rc else admin_id

    for semaine in semaines_s1[:8]:  # 8 semaines par classe
        statut_choice = random.choices(
            [StatutPlanningEnum.valide, StatutPlanningEnum.soumis, StatutPlanningEnum.brouillon],
            weights=[0.6, 0.25, 0.15]
        )[0]

        pl = Planning(
            semaine    = semaine,
            statut     = statut_choice,
            created_by = createur_id,
            commentaire= "Planning validé automatiquement" if statut_choice == StatutPlanningEnum.valide else None,
            created_at = datetime.combine(semaine - timedelta(days=3), time(10, 0)),
            updated_at = datetime.combine(semaine - timedelta(days=2), time(14, 0)),
        )
        db.add(pl)
        db.flush()

        db.add(PlanningClasse(planning_id=pl.id, classe_id=cls.id))

        # 3 à 5 séances dans la semaine
        mods_semaine = random.sample(mods, min(4, len(mods)))
        jours_dispo  = list(range(5))  # lun à ven
        random.shuffle(jours_dispo)
        creneaux_pl  = [(time(8,0), time(10,0)), (time(10,0), time(12,0)),
                        (time(14,0), time(16,0)), (time(16,0), time(18,0))]

        for i, mod in enumerate(mods_semaine):
            jour = jours_dispo[i % 5]
            date_seance = semaine + timedelta(days=jour)
            creneau = creneaux_pl[i % 4]
            db.add(PlanningSeance(
                planning_id = pl.id,
                module_id   = mod.id,
                date        = date_seance,
                heure_debut = creneau[0],
                heure_fin   = creneau[1],
            ))
        nb_plannings += 1

db.commit()
print(f"  [OK] Plannings créés  : {nb_plannings}")

# ════════════════════════════════════════════════════════════
#  RÉSUMÉ FINAL
# ════════════════════════════════════════════════════════════
print()
print("=" * 60)
print("  ✅ Peuplement terminé avec succès !")
print()
print(f"  UE              : {db.query(UE).count()}")
print(f"  Modules         : {db.query(Module).count()}")
print(f"  Séances         : {db.query(Seance).count()}")
print(f"  Présences       : {db.query(Presence).count()}")
print(f"  Notes           : {db.query(Note).count()}")
print(f"  Bulletins       : {db.query(Bulletin).count()}")
print(f"  Plannings       : {db.query(Planning).count()}")
print(f"  PlanningSeances : {db.query(PlanningSeance).count()}")
print()
print("  → Lancez : python app.py")
print("=" * 60)

db.close()