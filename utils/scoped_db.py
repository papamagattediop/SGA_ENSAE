# ============================================================
#  SGA ENSAE — utils/scoped_db.py
#  Requêtes DB scopées par rôle/utilisateur
#  Utilisé par : dashboard.py, statistiques.py
# ============================================================

from database import SessionLocal
from models import (
    Classe, Filiere, Etudiant, Module, Seance, Note,
    Presence, Planning, StatutPlanningEnum,
    ResponsableClasse, ResponsableFiliere, PlanningClasse
)


# ─────────────────────────────────────────────────────────────
#  PÉRIMÈTRE DE CLASSES PAR RÔLE
# ─────────────────────────────────────────────────────────────

def get_classe_ids_for_user(role: str, user_id: int, db) -> list[int] | None:
    """
    Retourne la liste des classe_id accessibles selon le rôle.
      None  → admin (aucun filtre, tout voir)
      [...]  → liste restreinte
      []     → aucune classe (rôle inconnu)
    """
    if role == "admin":
        return None

    if role == "resp_filiere":
        rf_list = db.query(ResponsableFiliere).filter(
            ResponsableFiliere.user_id == user_id
        ).all()
        filiere_ids = [r.filiere_id for r in rf_list]
        classes = db.query(Classe).filter(
            Classe.filiere_id.in_(filiere_ids)
        ).all()
        return [c.id for c in classes]

    if role == "resp_classe":
        rc_list = db.query(ResponsableClasse).filter(
            ResponsableClasse.user_id == user_id
        ).all()
        return [r.classe_id for r in rc_list]

    return []


def _scope(q, attr, ids):
    """
    Applique le filtre classe_id sur une requête.
    ids=None → pas de filtre (admin).
    ids=[]   → retourne None (aucun résultat possible).
    """
    if ids is None:
        return q
    if not ids:
        return None
    return q.filter(attr.in_(ids))


# ─────────────────────────────────────────────────────────────
#  KPIs DASHBOARD — scopés par rôle
# ─────────────────────────────────────────────────────────────

def get_kpis_for_user(role: str, user_id: int) -> dict:
    """
    Retourne les KPIs du dashboard adaptés au rôle :
      admin        → chiffres globaux de l'école
      resp_filiere → chiffres de sa filière uniquement
      resp_classe  → chiffres de sa/ses classe(s) uniquement
    """
    db = SessionLocal()
    try:
        ids = get_classe_ids_for_user(role, user_id, db)

        # Étudiants
        q = _scope(db.query(Etudiant), Etudiant.classe_id, ids)
        nb_etudiants = q.count() if q is not None else 0

        # Modules
        q = _scope(db.query(Module), Module.classe_id, ids)
        nb_modules = q.count() if q is not None else 0

        # Séances (via modules)
        if ids is None:
            nb_seances = db.query(Seance).count()
        elif not ids:
            nb_seances = 0
        else:
            mod_ids = [m.id for m in db.query(Module).filter(
                Module.classe_id.in_(ids)
            ).all()]
            nb_seances = db.query(Seance).filter(
                Seance.module_id.in_(mod_ids)
            ).count() if mod_ids else 0

        # Classes
        nb_classes = db.query(Classe).count() if ids is None else len(ids)

        # Filières
        if ids is None:
            nb_filieres = db.query(Filiere).count()
        elif not ids:
            nb_filieres = 0
        else:
            filiere_ids = set(
                c.filiere_id for c in db.query(Classe).filter(
                    Classe.id.in_(ids)
                ).all()
            )
            nb_filieres = len(filiere_ids)

        # Plannings soumis en attente
        q_plan = db.query(Planning).filter(
            Planning.statut == StatutPlanningEnum.soumis
        )
        if ids is None:
            nb_plannings = q_plan.count()
        elif not ids:
            nb_plannings = 0
        else:
            nb_plannings = q_plan.join(PlanningClasse).filter(
                PlanningClasse.classe_id.in_(ids)
            ).distinct().count()

        return {
            "nb_etudiants" : nb_etudiants,
            "nb_modules"   : nb_modules,
            "nb_seances"   : nb_seances,
            "nb_classes"   : nb_classes,
            "nb_filieres"  : nb_filieres,
            "nb_plannings" : nb_plannings,
        }
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────
#  SCOPE COMBINÉ : rôle + filtre dropdown
# ─────────────────────────────────────────────────────────────

def resolve_scope(role: str, user_id: int, classe_id_filtre: int | None) -> list[int] | None:
    """
    Combine le périmètre du rôle avec le filtre classe choisi dans l'UI.

      admin sans filtre → None (tout voir)
      admin avec filtre → [classe_id_filtre]
      resp_filiere/resp_classe sans filtre → toutes leurs classes
      resp_filiere/resp_classe avec filtre → [classe_id_filtre] si dans leur périmètre
    """
    db = SessionLocal()
    try:
        scope = get_classe_ids_for_user(role, user_id, db)
        if classe_id_filtre is not None:
            if scope is None:
                return [classe_id_filtre]           # admin, filtre libre
            return [classe_id_filtre] if classe_id_filtre in scope else []
        return scope
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────
#  DONNÉES STATISTIQUES SCOPÉES
# ─────────────────────────────────────────────────────────────

def get_notes_data_scoped(ids: list[int] | None) -> list[float]:
    db = SessionLocal()
    try:
        q = db.query(Note).join(Etudiant, Note.etudiant_id == Etudiant.id)
        q = _scope(q, Etudiant.classe_id, ids)
        if q is None:
            return []
        return [n.note for n in q.all() if n.note is not None]
    finally:
        db.close()


def get_moyennes_etudiants_scoped(ids: list[int] | None) -> list[dict]:
    db = SessionLocal()
    try:
        q = _scope(db.query(Etudiant), Etudiant.classe_id, ids)
        if q is None:
            return []
        etudiants = q.all()
        moyennes = []
        for e in etudiants:
            notes = db.query(Note).filter(Note.etudiant_id == e.id).all()
            if notes:
                moy = round(sum(n.note for n in notes) / len(notes), 2)
                moyennes.append({
                    "nom"   : f"{e.user.prenom} {e.user.nom}" if e.user else "-",
                    "classe": e.classe.nom if e.classe else "-",
                    "moy"   : moy
                })
        return sorted(moyennes, key=lambda x: x["moy"], reverse=True)
    finally:
        db.close()


def get_assiduite_data_scoped(ids: list[int] | None) -> list[dict]:
    db = SessionLocal()
    try:
        q = _scope(db.query(Etudiant), Etudiant.classe_id, ids)
        if q is None:
            return []
        etudiants = q.all()
        result = []
        for e in etudiants:
            total    = db.query(Presence).filter(Presence.etudiant_id == e.id).count()
            presents = db.query(Presence).filter(
                Presence.etudiant_id == e.id,
                Presence.present     == True
            ).count()
            taux = round((presents / total) * 100) if total > 0 else 100
            result.append({
                "nom" : f"{e.user.prenom} {e.user.nom}" if e.user else "-",
                "taux": taux,
                "abs" : total - presents
            })
        return sorted(result, key=lambda x: x["taux"])
    finally:
        db.close()


def get_progression_modules_scoped(ids: list[int] | None) -> list[dict]:
    db = SessionLocal()
    try:
        q = _scope(db.query(Module), Module.classe_id, ids)
        if q is None:
            return []
        modules = q.all()
        result = []
        for m in modules:
            seances = db.query(Seance).filter(Seance.module_id == m.id).all()
            heures = sum(
                (s.heure_fin.hour * 60 + s.heure_fin.minute -
                 s.heure_debut.hour * 60 - s.heure_debut.minute) / 60
                for s in seances if s.heure_debut and s.heure_fin
            )
            pct = min(round((heures / m.volume_horaire) * 100)
                      if m.volume_horaire else 0, 100)
            result.append({
                "module" : m.code,
                "libelle": m.libelle,
                "fait"   : round(heures, 1),
                "total"  : m.volume_horaire or 0,
                "pct"    : pct
            })
        return sorted(result, key=lambda x: x["pct"])
    finally:
        db.close()


def get_notes_par_module_scoped(ids: list[int] | None) -> list[dict]:
    db = SessionLocal()
    try:
        q = _scope(db.query(Module), Module.classe_id, ids)
        if q is None:
            return []
        modules = q.all()
        result = []
        for m in modules:
            notes = db.query(Note).join(
                Etudiant, Note.etudiant_id == Etudiant.id
            ).filter(Note.module_id == m.id).all()
            vals = [n.note for n in notes if n.note is not None]
            if vals:
                result.append({
                    "module" : m.code,
                    "libelle": m.libelle,
                    "moy"    : round(sum(vals) / len(vals), 2),
                    "min"    : min(vals),
                    "max"    : max(vals),
                    "n"      : len(vals)
                })
        return sorted(result, key=lambda x: x["moy"], reverse=True)
    finally:
        db.close()


def get_seances_par_semaine_scoped(ids: list[int] | None) -> dict[str, int]:
    db = SessionLocal()
    try:
        q = db.query(Seance).filter(Seance.date != None)
        if ids is not None:
            if not ids:
                return {}
            mod_ids = [m.id for m in db.query(Module).filter(
                Module.classe_id.in_(ids)
            ).all()]
            if not mod_ids:
                return {}
            q = q.filter(Seance.module_id.in_(mod_ids))
        par_sem = {}
        for s in q.all():
            sem = s.date.strftime("%Y-S%W")
            par_sem[sem] = par_sem.get(sem, 0) + 1
        return dict(sorted(par_sem.items()))
    finally:
        db.close()