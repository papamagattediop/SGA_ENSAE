# ============================================================
#  SGA ENSAE — auth.py
#  Authentification et gestion des rôles
#  Python 3.11 · SQLAlchemy 2.0.30
# ============================================================

import hashlib
from database import SessionLocal
from models import User, RoleEnum, Filiere, Classe
from models import ResponsableFiliere, ResponsableClasse


# ════════════════════════════════════════════════════════════
#  PASSWORDS
# ════════════════════════════════════════════════════════════

def hash_password(password: str) -> str:
    """Hash SHA-256 du mot de passe."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Vérifie un mot de passe contre son hash."""
    return hash_password(password) == hashed


# ════════════════════════════════════════════════════════════
#  LOGIN / LOGOUT
# ════════════════════════════════════════════════════════════

def login(email: str, password: str):
    """
    Retourne l'utilisateur si credentials valides et compte actif.
    Retourne None sinon.
    """
    if not email or not password:
        return None
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.email == email,
            User.is_active == True
        ).first()
        if user and verify_password(password, user.password_hash):
            return {
                "user_id"  : user.id,
                "nom"      : user.nom,
                "prenom"   : user.prenom,
                "email"    : user.email,
                "role"     : user.role.value,
                "is_active": user.is_active
            }
        return None
    finally:
        db.close()


# ════════════════════════════════════════════════════════════
#  RÉCUPÉRATION UTILISATEUR
# ════════════════════════════════════════════════════════════

def get_user_by_id(user_id: int):
    """Retourne un dict utilisateur depuis son ID."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        return {
            "user_id"  : user.id,
            "nom"      : user.nom,
            "prenom"   : user.prenom,
            "email"    : user.email,
            "role"     : user.role.value,
            "is_active": user.is_active
        }
    finally:
        db.close()


# ════════════════════════════════════════════════════════════
#  VÉRIFICATION DES RÔLES
# ════════════════════════════════════════════════════════════

def is_admin(session: dict) -> bool:
    return session.get("role") == RoleEnum.admin.value

def is_resp_filiere(session: dict) -> bool:
    return session.get("role") == RoleEnum.resp_filiere.value

def is_resp_classe(session: dict) -> bool:
    return session.get("role") == RoleEnum.resp_classe.value

def is_eleve(session: dict) -> bool:
    return session.get("role") == RoleEnum.eleve.value

def is_authenticated(session: dict) -> bool:
    """Vérifie qu'un utilisateur est connecté."""
    return bool(session and session.get("user_id"))

def can_manage_classe(session: dict, classe_id: int) -> bool:
    """
    Vérifie si l'utilisateur peut gérer une classe donnée.
    Admin → tout
    Resp. filière → toutes les classes de sa filière
    Resp. classe → uniquement sa classe
    """
    if not is_authenticated(session):
        return False
    if is_admin(session):
        return True

    db = SessionLocal()
    try:
        user_id = session.get("user_id")

        if is_resp_filiere(session):
            # Vérifier que la classe appartient à sa filière
            resp = db.query(ResponsableFiliere).filter(
                ResponsableFiliere.user_id == user_id
            ).first()
            if resp:
                classe = db.query(Classe).filter(
                    Classe.id == classe_id,
                    Classe.filiere_id == resp.filiere_id
                ).first()
                return classe is not None

        if is_resp_classe(session):
            resp = db.query(ResponsableClasse).filter(
                ResponsableClasse.user_id == user_id,
                ResponsableClasse.classe_id == classe_id
            ).first()
            return resp is not None

        return False
    finally:
        db.close()


# ════════════════════════════════════════════════════════════
#  CRÉATION COMPTE ADMIN (initialisation)
# ════════════════════════════════════════════════════════════

def create_admin(nom: str, prenom: str, email: str, password: str):
    """
    Crée le compte administrateur initial.
    À appeler une seule fois au démarrage si aucun admin n'existe.
    """
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"[INFO] Admin {email} existe déjà.")
            return None

        admin = User(
            nom=nom,
            prenom=prenom,
            email=email,
            password_hash=hash_password(password),
            role=RoleEnum.admin,
            is_active=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"[OK] Compte admin créé : {email}")
        return admin
    except Exception as e:
        db.rollback()
        print(f"[ERREUR] Création admin : {e}")
        return None
    finally:
        db.close()


# ════════════════════════════════════════════════════════════
#  GUARD — Redirection si non connecté
# ════════════════════════════════════════════════════════════

def require_auth(session: dict, required_roles: list = None):
    """
    Vérifie l'authentification et le rôle.
    Retourne (True, None) si OK.
    Retourne (False, redirect_path) sinon.

    Utilisation dans les callbacks Dash :
        ok, redirect = require_auth(session, ["admin", "resp_filiere"])
        if not ok:
            return redirect
    """
    if not is_authenticated(session):
        return False, "/login"

    if required_roles:
        if session.get("role") not in required_roles:
            return False, "/dashboard"

    return True, None