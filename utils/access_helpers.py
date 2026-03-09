# ============================================================
#  SGA ENSAE — utils/access_helpers.py
#  Fonctions utilitaires de filtrage par rôle/utilisateur
#  À importer dans toutes les pages qui ont des dropdowns classes
# ============================================================

from database import SessionLocal
from models import (
    Classe, Filiere, ResponsableClasse, ResponsableFiliere, Etudiant
)


def get_classes_for_user(role: str, user_id: int) -> list[dict]:
    """
    Retourne les classes accessibles selon le rôle :
      - admin        → toutes les classes
      - resp_filiere → classes de sa/ses filière(s) uniquement
      - resp_classe  → sa/ses classe(s) uniquement
      - autre        → liste vide
    Résultat : [{"label": nom, "value": id}, ...]
    """
    db = SessionLocal()
    try:
        if role == "admin":
            classes = (
                db.query(Classe)
                .join(Filiere)
                .order_by(Filiere.code, Classe.niveau, Classe.nom)
                .all()
            )

        elif role == "resp_filiere":
            rf_list = (
                db.query(ResponsableFiliere)
                .filter(ResponsableFiliere.user_id == user_id)
                .all()
            )
            filiere_ids = [r.filiere_id for r in rf_list]
            classes = (
                db.query(Classe)
                .filter(Classe.filiere_id.in_(filiere_ids))
                .join(Filiere)
                .order_by(Filiere.code, Classe.niveau, Classe.nom)
                .all()
            )

        elif role == "resp_classe":
            rc_list = (
                db.query(ResponsableClasse)
                .filter(ResponsableClasse.user_id == user_id)
                .all()
            )
            classe_ids = [r.classe_id for r in rc_list]
            classes = (
                db.query(Classe)
                .filter(Classe.id.in_(classe_ids))
                .order_by(Classe.nom)
                .all()
            )

        else:
            classes = []

        return [{"label": c.nom, "value": c.id} for c in classes]
    finally:
        db.close()


def get_default_classe_id(role: str, user_id: int) -> int | None:
    """
    Retourne l'id de classe par défaut à pré-sélectionner :
      - resp_classe  → sa première classe
      - autres rôles → None (pas de pré-sélection)
    """
    if role != "resp_classe":
        return None
    db = SessionLocal()
    try:
        rc = (
            db.query(ResponsableClasse)
            .filter(ResponsableClasse.user_id == user_id)
            .order_by(ResponsableClasse.est_titulaire.desc())
            .first()
        )
        return rc.classe_id if rc else None
    finally:
        db.close()