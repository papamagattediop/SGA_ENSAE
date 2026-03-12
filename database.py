# ============================================================
#  SGA ENSAE — database.py
#  Connexion SQLite (dev) ou PostgreSQL (prod) via .env
# ============================================================

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/sga_ensae.db")
DB_PATH = DATABASE_URL.replace("sqlite:///", "") if DATABASE_URL.startswith("sqlite") else None
# Arguments spécifiques à SQLite uniquement
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

def init_db():
    if DATABASE_URL.startswith("sqlite"):
        import os as _os
        _os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print("[OK] Base de données initialisée —", len(Base.metadata.tables), "tables")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connexion():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[OK] Connexion réussie")
        return True
    except Exception as e:
        print(f"[ERREUR] {e}")
        return False