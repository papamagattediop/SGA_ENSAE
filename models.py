# ============================================================
#  SGA ENSAE — models.py
#  Modèles SQLAlchemy · 16 tables
#  Python 3.11 · SQLAlchemy 2.0.30
# ============================================================

import enum
from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    Date, DateTime, Time, Text, ForeignKey,
    UniqueConstraint, Enum as SAEnum
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


# ════════════════════════════════════════════════════════════
#  ENUMS
# ════════════════════════════════════════════════════════════

class RoleEnum(str, enum.Enum):
    admin        = "admin"
    resp_filiere = "resp_filiere"
    resp_classe  = "resp_classe"
    eleve        = "eleve"

class StatutPlanningEnum(str, enum.Enum):
    brouillon = "brouillon"
    soumis    = "soumis"
    modifie   = "modifie"
    valide    = "valide"
    rejete    = "rejete"

class TypeEvalEnum(str, enum.Enum):
    devoir = "Devoir"
    examen = "Examen"

class StatutMigrationEnum(str, enum.Enum):
    succes = "succes"
    erreur = "erreur"


# ════════════════════════════════════════════════════════════
#  GROUPE 1 — Structure de l'école
# ════════════════════════════════════════════════════════════

class Filiere(Base):
    """
    Filières de l'ENSAE :
    ISEP (2 ans), ISE (3 ans), AS (3 ans), Masters (1 an)
    """
    __tablename__ = "filieres"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    code      = Column(String(20), unique=True, nullable=False)
    libelle   = Column(String(100), nullable=False)
    duree_ans = Column(Integer, nullable=False)

    classes      = relationship("Classe", back_populates="filiere")
    responsables = relationship("ResponsableFiliere", back_populates="filiere")

    def __repr__(self):
        return f"<Filiere {self.code}>"


class Classe(Base):
    """
    Classes de l'école (12 au total).
    is_commune=True pour ISE 2 et ISE 3.
    """
    __tablename__ = "classes"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    nom            = Column(String(50), nullable=False)
    filiere_id     = Column(Integer, ForeignKey("filieres.id"), nullable=False)
    niveau         = Column(Integer, nullable=False)
    is_commune     = Column(Boolean, default=False)
    annee_scolaire = Column(String(9), nullable=False)            # ex: 2024-2025

    filiere          = relationship("Filiere", back_populates="classes")
    etudiants        = relationship("Etudiant", back_populates="classe")
    modules          = relationship("Module", back_populates="classe")
    responsables     = relationship("ResponsableClasse", back_populates="classe")
    ue_classes       = relationship("UEClasse", back_populates="classe")
    periodes         = relationship("Periode", back_populates="classe")
    planning_classes = relationship("PlanningClasse", back_populates="classe")

    def __repr__(self):
        return f"<Classe {self.nom}>"


# ════════════════════════════════════════════════════════════
#  GROUPE 2 — Utilisateurs & Rôles
# ════════════════════════════════════════════════════════════

class User(Base):
    """
    Tous les utilisateurs de l'application.
    role : admin | resp_filiere | resp_classe | eleve
    """
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    nom           = Column(String(50), nullable=False)
    prenom        = Column(String(50), nullable=False)
    email         = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role          = Column(SAEnum(RoleEnum), nullable=False)
    is_active     = Column(Boolean, default=True)

    etudiant          = relationship("Etudiant", back_populates="user", uselist=False)
    resp_filieres     = relationship("ResponsableFiliere", back_populates="user")
    resp_classes      = relationship("ResponsableClasse", back_populates="user")
    seances_creees    = relationship("Seance", back_populates="created_by_user")
    plannings_crees   = relationship("Planning", back_populates="created_by_user")
    bulletins_valides = relationship("Bulletin", back_populates="valide_par_user")

    def __repr__(self):
        return f"<User {self.email} [{self.role}]>"


class Etudiant(Base):
    """
    Informations académiques des étudiants.
    filiere_origine : utile pour les ISE avant fusion en ISE 2.
    """
    __tablename__ = "etudiants"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    matricule       = Column(String(20), unique=True, nullable=False)
    date_naissance  = Column(Date)
    classe_id       = Column(Integer, ForeignKey("classes.id"), nullable=False)
    filiere_origine = Column(String(30))
    annee_scolaire  = Column(String(9), nullable=False)

    user      = relationship("User", back_populates="etudiant")
    classe    = relationship("Classe", back_populates="etudiants")
    presences = relationship("Presence", back_populates="etudiant")
    notes     = relationship("Note", back_populates="etudiant")
    bulletins = relationship("Bulletin", back_populates="etudiant")

    def __repr__(self):
        return f"<Etudiant {self.matricule}>"


class ResponsableFiliere(Base):
    """
    Liaison User ↔ Filière pour les responsables de filière.
    """
    __tablename__ = "resp_filieres"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    filiere_id = Column(Integer, ForeignKey("filieres.id"), nullable=False)

    user    = relationship("User", back_populates="resp_filieres")
    filiere = relationship("Filiere", back_populates="responsables")

    def __repr__(self):
        return f"<RespFiliere user={self.user_id} filiere={self.filiere_id}>"


class ResponsableClasse(Base):
    """
    Liaison User ↔ Classe pour les responsables de classe.
    """
    __tablename__ = "resp_classes"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    classe_id     = Column(Integer, ForeignKey("classes.id"), nullable=False)
    est_titulaire = Column(Boolean, default=True, nullable=False)
    # True  = Delegue titulaire
    # False = Delegue suppleant

    user   = relationship("User", back_populates="resp_classes")
    classe = relationship("Classe", back_populates="responsables")

    def __repr__(self):
        role = "Titulaire" if self.est_titulaire else "Suppleant"
        return f"<RespClasse user={self.user_id} classe={self.classe_id} [{role}]>"


# ════════════════════════════════════════════════════════════
#  GROUPE 3 — Pédagogie
# ════════════════════════════════════════════════════════════

class Periode(Base):
    """
    Périodes d'évaluation : Semestre 1, Partiel 1, Annuel...
    est_cloturee=True verrouille les notes.
    """
    __tablename__ = "periodes"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    libelle        = Column(String(50), nullable=False)           # ex: Semestre 1
    classe_id      = Column(Integer, ForeignKey("classes.id"), nullable=False)
    date_debut     = Column(Date)
    date_fin       = Column(Date)
    est_cloturee   = Column(Boolean, default=False)
    annee_scolaire = Column(String(9), nullable=False)

    classe    = relationship("Classe", back_populates="periodes")
    ues       = relationship("UE", back_populates="periode")
    bulletins = relationship("Bulletin", back_populates="periode")

    def __repr__(self):
        return f"<Periode {self.libelle}>"


class UE(Base):
    """
    Unités d'Enseignement.
    Une UE peut être partagée entre plusieurs classes (UEClasse).
    """
    __tablename__ = "ue"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    code        = Column(String(20), nullable=False)              # ex: UE-STAT
    libelle     = Column(String(100), nullable=False)             # ex: Statistiques
    coefficient = Column(Float, nullable=False, default=1.0)
    periode_id  = Column(Integer, ForeignKey("periodes.id"), nullable=False)

    periode    = relationship("Periode", back_populates="ues")
    modules    = relationship("Module", back_populates="ue")
    ue_classes = relationship("UEClasse", back_populates="ue")

    def __repr__(self):
        return f"<UE {self.code}>"


class UEClasse(Base):
    """
    Table de liaison UE ↔ Classes.
    Permet à une UE d'être partagée (ex: ISE 2 commune).
    """
    __tablename__ = "ue_classes"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    ue_id     = Column(Integer, ForeignKey("ue.id"), nullable=False)
    classe_id = Column(Integer, ForeignKey("classes.id"), nullable=False)

    __table_args__ = (UniqueConstraint("ue_id", "classe_id"),)

    ue     = relationship("UE", back_populates="ue_classes")
    classe = relationship("Classe", back_populates="ue_classes")

    def __repr__(self):
        return f"<UEClasse ue={self.ue_id} classe={self.classe_id}>"


class Module(Base):
    """
    Modules pédagogiques rattachés à une UE.
    Chaque module peut avoir 1 ou 2 notes par étudiant.

    email_enseignant : email direct du prof → utilisé pour les notifications
                       planning à la validation (plus fiable qu'une recherche par nom).
    """
    __tablename__ = "modules"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    code             = Column(String(20), nullable=False)         # ex: MOD-STAT1
    libelle          = Column(String(100), nullable=False)
    coefficient      = Column(Float, nullable=False, default=1.0)
    enseignant       = Column(String(100))                        # nom affiché dans l'UI
    email_enseignant = Column(String(150))                        # ← NOUVEAU : email pour notifs planning
    volume_horaire   = Column(Integer)                            # heures prévues

    ue_id     = Column(Integer, ForeignKey("ue.id"), nullable=False)
    classe_id = Column(Integer, ForeignKey("classes.id"), nullable=False)

    ue               = relationship("UE", back_populates="modules")
    classe           = relationship("Classe", back_populates="modules")
    seances          = relationship("Seance", back_populates="module")
    notes            = relationship("Note", back_populates="module")
    planning_seances = relationship("PlanningSeance", back_populates="module")

    def __repr__(self):
        return f"<Module {self.code}>"


class Seance(Base):
    """
    Séances de cours enregistrées dans le cahier de texte.
    """
    __tablename__ = "seances"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    module_id   = Column(Integer, ForeignKey("modules.id"), nullable=False)
    date        = Column(Date, nullable=False)
    heure_debut = Column(Time)
    heure_fin   = Column(Time)
    theme       = Column(Text)
    created_by  = Column(Integer, ForeignKey("users.id"), nullable=False)

    module          = relationship("Module", back_populates="seances")
    created_by_user = relationship("User", back_populates="seances_creees")
    presences       = relationship("Presence", back_populates="seance")

    def __repr__(self):
        return f"<Seance module={self.module_id} date={self.date}>"


class Presence(Base):
    """
    Appel numérique : présence par séance et par étudiant.
    UNIQUE(seance_id, etudiant_id) — évite les doublons.
    """
    __tablename__ = "presences"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    seance_id   = Column(Integer, ForeignKey("seances.id"), nullable=False)
    etudiant_id = Column(Integer, ForeignKey("etudiants.id"), nullable=False)
    present     = Column(Boolean, default=True, nullable=False)

    __table_args__ = (UniqueConstraint("seance_id", "etudiant_id"),)

    seance   = relationship("Seance", back_populates="presences")
    etudiant = relationship("Etudiant", back_populates="presences")

    def __repr__(self):
        return f"<Presence seance={self.seance_id} etudiant={self.etudiant_id}>"


class Note(Base):
    """
    Notes des étudiants par module.
    numero : 1 (Devoir) ou 2 (Examen).
    Si 1 seule note → moyenne module = cette note.
    Si 2 notes → moyenne module = (note1 + note2) / 2.
    UNIQUE(etudiant_id, module_id, numero) — évite les doublons.
    """
    __tablename__ = "notes"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    etudiant_id = Column(Integer, ForeignKey("etudiants.id"), nullable=False)
    module_id   = Column(Integer, ForeignKey("modules.id"), nullable=False)
    note        = Column(Float, nullable=False)                   # /20
    type_eval   = Column(SAEnum(TypeEvalEnum), nullable=False)    # Devoir / Examen
    numero      = Column(Integer, nullable=False)                 # 1 ou 2

    __table_args__ = (UniqueConstraint("etudiant_id", "module_id", "numero"),)

    etudiant = relationship("Etudiant", back_populates="notes")
    module   = relationship("Module", back_populates="notes")

    def __repr__(self):
        return f"<Note etudiant={self.etudiant_id} module={self.module_id} n={self.numero}>"


# ════════════════════════════════════════════════════════════
#  GROUPE 4 — Bulletins
# ════════════════════════════════════════════════════════════

class Bulletin(Base):
    """
    Bulletin de notes généré par période.
    moyenne_gen, rang, taux_assiduite sont calculés
    par utils/calculs.py avant génération.
    """
    __tablename__ = "bulletins"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    etudiant_id     = Column(Integer, ForeignKey("etudiants.id"), nullable=False)
    periode_id      = Column(Integer, ForeignKey("periodes.id"), nullable=False)
    moyenne_gen     = Column(Float)
    rang            = Column(Integer)
    taux_assiduite  = Column(Float)                               # en %
    appreciation    = Column(Text)
    valide_par      = Column(Integer, ForeignKey("users.id"))
    pdf_path        = Column(String(255))
    genere_le       = Column(DateTime)
    envoye_par_mail = Column(Boolean, default=False)

    __table_args__ = (UniqueConstraint("etudiant_id", "periode_id"),)

    etudiant        = relationship("Etudiant", back_populates="bulletins")
    periode         = relationship("Periode", back_populates="bulletins")
    valide_par_user = relationship("User", back_populates="bulletins_valides")

    def __repr__(self):
        return f"<Bulletin etudiant={self.etudiant_id} periode={self.periode_id}>"


# ════════════════════════════════════════════════════════════
#  GROUPE 5 — Planning
# ════════════════════════════════════════════════════════════

class Planning(Base):
    """
    Proposition de planning semaine N+1 par le responsable de classe.
    semaine : date du lundi de la semaine concernée.
    Workflow : brouillon → soumis → modifie → valide / rejete
    """
    __tablename__ = "plannings"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    semaine     = Column(Date, nullable=False)                    # lundi de la semaine
    statut      = Column(SAEnum(StatutPlanningEnum), default=StatutPlanningEnum.brouillon)
    created_by  = Column(Integer, ForeignKey("users.id"), nullable=False)
    commentaire = Column(Text)                                    # du resp. filière
    created_at  = Column(DateTime)
    updated_at  = Column(DateTime)

    created_by_user  = relationship("User", back_populates="plannings_crees")
    planning_classes = relationship("PlanningClasse", back_populates="planning")
    planning_seances = relationship("PlanningSeance", back_populates="planning")

    def __repr__(self):
        return f"<Planning semaine={self.semaine} statut={self.statut}>"


class PlanningClasse(Base):
    """
    Table de liaison Planning ↔ Classes.
    Permet un planning multi-classes (ex: ISE 2 commune).
    """
    __tablename__ = "planning_classes"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    planning_id = Column(Integer, ForeignKey("plannings.id"), nullable=False)
    classe_id   = Column(Integer, ForeignKey("classes.id"), nullable=False)

    __table_args__ = (UniqueConstraint("planning_id", "classe_id"),)

    planning = relationship("Planning", back_populates="planning_classes")
    classe   = relationship("Classe", back_populates="planning_classes")

    def __repr__(self):
        return f"<PlanningClasse planning={self.planning_id} classe={self.classe_id}>"


class PlanningSeance(Base):
    """
    Détail des séances proposées dans un planning.
    """
    __tablename__ = "planning_seances"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    planning_id = Column(Integer, ForeignKey("plannings.id"), nullable=False)
    module_id   = Column(Integer, ForeignKey("modules.id"), nullable=False)
    date        = Column(Date, nullable=False)
    heure_debut = Column(Time, nullable=False)
    heure_fin   = Column(Time, nullable=False)

    planning = relationship("Planning", back_populates="planning_seances")
    module   = relationship("Module", back_populates="planning_seances")

    def __repr__(self):
        return f"<PlanningSeance module={self.module_id} date={self.date}>"


# ════════════════════════════════════════════════════════════
#  GROUPE 6 — Logs
# ════════════════════════════════════════════════════════════

class MigrationLog(Base):
    """
    Traçabilité des imports Excel vers la base SQL.
    """
    __tablename__ = "migration_logs"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    fichier     = Column(String(255))
    date_import = Column(DateTime)
    statut      = Column(SAEnum(StatutMigrationEnum))             # succes / erreur
    details     = Column(Text)

    def __repr__(self):
        return f"<MigrationLog {self.fichier} [{self.statut}]>"