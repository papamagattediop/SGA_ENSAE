# ============================================================
#  SGA ENSAE — database.py
#  Connexion et initialisation de la base de données
#  Python 3.11 · SQLAlchemy 2.0.30
# ============================================================

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base
import os

# ── Configuration ─────────────────────────────────────────────
DATABASE_URL = "sqlite:///data/sga_ensae.db"
DB_PATH      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sga_ensae.db")
# Pour PostgreSQL (production) :
# DATABASE_URL = "postgresql://user:password@localhost/sga_ensae"

# ── Moteur SQLAlchemy ─────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    echo=False,                  # True pour voir les requêtes SQL en debug
    connect_args={"check_same_thread": False}  # Requis pour SQLite + Dash
)

# ── Session ───────────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

# ── Initialisation ────────────────────────────────────────────
def init_db():
    """
    Crée toutes les tables si elles n'existent pas.
    Appelé au démarrage de app.py.
    """
    import os
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print("[OK] Base de données initialisée —", len(Base.metadata.tables), "tables")

# ── Session context ───────────────────────────────────────────
def get_db():
    """
    Générateur de session SQLAlchemy.
    Utilisation :
        db = next(get_db())
        try:
            # requêtes
        finally:
            db.close()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── Test de connexion ─────────────────────────────────────────
def test_connexion():
    """Vérifie que la base est accessible."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[OK] Connexion base de données réussie")
        return True
    except Exception as e:
        print(f"[ERREUR] Connexion échouée : {e}")
        return False