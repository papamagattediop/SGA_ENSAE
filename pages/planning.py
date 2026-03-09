# ============================================================
#  SGA ENSAE — pages/planning.py
#  Module 6 : Planning hebdomadaire
#  Python 3.11 · Dash 2.17.0
# ============================================================

import dash
from dash import html, dcc, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc
from auth import require_auth
from database import SessionLocal
from models import (
    Planning, PlanningClasse, PlanningSeance,
    Classe, Module, User, ResponsableClasse,
    ResponsableFiliere, StatutPlanningEnum
)
from datetime import date, timedelta, datetime

dash.register_page(__name__, path="/planning", title="SGA ENSAE — Planning")

BLEU = "#003580"
VERT = "#006B3F"
OR   = "#F5A623"

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


# ============================================================
#  UTILITAIRES DB
# ============================================================

def get_classes_for_user(role: str, user_id: int) -> list:
    """
    Retourne les classes accessibles selon le rôle :
    - admin         → toutes les classes
    - resp_filiere  → classes de sa filière
    - resp_classe   → uniquement sa/ses classe(s)
    """
    db = SessionLocal()
    try:
        if role == "admin":
            classes = db.query(Classe).order_by(Classe.nom).all()

        elif role == "resp_filiere":
            rf = db.query(ResponsableFiliere).filter(
                ResponsableFiliere.user_id == user_id
            ).all()
            filiere_ids = [r.filiere_id for r in rf]
            classes = db.query(Classe).filter(
                Classe.filiere_id.in_(filiere_ids)
            ).order_by(Classe.nom).all()

        elif role == "resp_classe":
            rc = db.query(ResponsableClasse).filter(
                ResponsableClasse.user_id == user_id
            ).all()
            classe_ids = [r.classe_id for r in rc]
            classes = db.query(Classe).filter(
                Classe.id.in_(classe_ids)
            ).order_by(Classe.nom).all()

        else:
            classes = []

        return [{"label": c.nom, "value": c.id} for c in classes]
    finally:
        db.close()


def get_classes():
    """Toutes les classes — utilisé uniquement en admin."""
    db = SessionLocal()
    try:
        return [{"label": c.nom, "value": c.id} for c in db.query(Classe).all()]
    finally:
        db.close()


def get_modules_by_classe(classe_id):
    db = SessionLocal()
    try:
        return [
            {"label": f"{m.code} — {m.libelle}", "value": m.id}
            for m in db.query(Module).filter(Module.classe_id == classe_id).all()
        ]
    finally:
        db.close()


def get_plannings(role, user_id, filtre_statut=None):
    """
    Retourne les plannings filtrés selon le rôle :
    - admin         → tous les plannings
    - resp_filiere  → plannings des classes de sa filière
    - resp_classe   → plannings de ses classes uniquement
    """
    db = SessionLocal()
    try:
        q = db.query(Planning)

        if role == "resp_classe":
            # Récupérer les IDs de classes du resp. de classe
            rc_classes = db.query(ResponsableClasse).filter(
                ResponsableClasse.user_id == user_id
            ).all()
            classe_ids = [rc.classe_id for rc in rc_classes]
            # Plannings qui concernent au moins une de ses classes
            q = q.join(PlanningClasse).filter(
                PlanningClasse.classe_id.in_(classe_ids)
            )

        elif role == "resp_filiere":
            # Récupérer les IDs de filières du resp. de filière
            rf_list = db.query(ResponsableFiliere).filter(
                ResponsableFiliere.user_id == user_id
            ).all()
            filiere_ids = [rf.filiere_id for rf in rf_list]
            # Classes de ces filières
            classe_ids = [
                c.id for c in db.query(Classe).filter(
                    Classe.filiere_id.in_(filiere_ids)
                ).all()
            ]
            # Plannings qui concernent au moins une de ces classes
            q = q.join(PlanningClasse).filter(
                PlanningClasse.classe_id.in_(classe_ids)
            )

        if filtre_statut and filtre_statut != "tous":
            q = q.filter(Planning.statut == filtre_statut)

        plannings = q.order_by(Planning.semaine.desc()).distinct().all()
        result = []
        for p in plannings:
            classes = [pc.classe.nom for pc in p.planning_classes if pc.classe]
            seances = p.planning_seances
            result.append({
                "id"         : p.id,
                "semaine"    : p.semaine.strftime("%d/%m/%Y") if p.semaine else "-",
                "statut"     : p.statut.value if p.statut else "-",
                "classes"    : ", ".join(classes),
                "nb_seances" : len(seances),
                "commentaire": p.commentaire or "",
                "created_by" : p.created_by,
                "created_at" : p.created_at.strftime("%d/%m/%Y") if p.created_at else "-",
            })
        return result
    finally:
        db.close()


def get_planning_detail(planning_id):
    db = SessionLocal()
    try:
        p = db.query(Planning).filter(Planning.id == planning_id).first()
        if not p:
            return None
        seances = []
        for s in p.planning_seances:
            seances.append({
                "module"     : s.module.libelle if s.module else "-",
                "enseignant" : s.module.enseignant if s.module and s.module.enseignant else "",
                "code"       : s.module.code if s.module else "-",
                "date"       : s.date.strftime("%d/%m/%Y") if s.date else "-",
                "heure_debut": s.heure_debut.strftime("%H:%M") if s.heure_debut else "-",
                "heure_fin"  : s.heure_fin.strftime("%H:%M") if s.heure_fin else "-",
                "jour"       : JOURS[s.date.weekday()] if s.date else "-",
            })
        seances.sort(key=lambda x: x["date"])
        return {
            "id"         : p.id,
            "semaine"    : p.semaine.strftime("%d/%m/%Y") if p.semaine else "-",
            "statut"     : p.statut.value if p.statut else "-",
            "classes"    : [pc.classe.nom for pc in p.planning_classes if pc.classe],
            "seances"    : seances,
            "commentaire": p.commentaire or "",
            "created_at" : p.created_at.strftime("%d/%m/%Y %H:%M") if p.created_at else "-",
        }
    finally:
        db.close()


def get_resp_filiere_email(classe_id):
    """Retourne (email, nom) du responsable de filière d'une classe."""
    db = SessionLocal()
    try:
        classe = db.query(Classe).filter(Classe.id == classe_id).first()
        if not classe:
            return None, None
        resp = db.query(ResponsableFiliere).filter(
            ResponsableFiliere.filiere_id == classe.filiere_id
        ).first()
        if resp and resp.user:
            return resp.user.email, f"{resp.user.prenom} {resp.user.nom}"
        return None, None
    finally:
        db.close()


def get_resp_classe_emails(planning_id) -> list:
    """
    Retourne la liste de (email, nom) à notifier côté resp. de classe :
    - Le délégué titulaire de chaque classe liée au planning
    - Le créateur du planning (si rôle resp_classe et pas déjà dans la liste)
    Dédupliqué par email.
    """
    db = SessionLocal()
    try:
        p = db.query(Planning).filter(Planning.id == planning_id).first()
        if not p:
            return []

        destinataires = {}  # email -> nom

        # 1. Délégués titulaires des classes du planning
        for pc in p.planning_classes:
            if not pc.classe:
                continue
            resp = db.query(ResponsableClasse).filter(
                ResponsableClasse.classe_id     == pc.classe.id,
                ResponsableClasse.est_titulaire == True
            ).first()
            if resp and resp.user and resp.user.email:
                destinataires[resp.user.email] = f"{resp.user.prenom} {resp.user.nom}"

        # 2. Créateur du planning (si resp_classe et pas déjà présent)
        if p.created_by_user and p.created_by_user.role.value == "resp_classe":
            u = p.created_by_user
            if u.email not in destinataires:
                destinataires[u.email] = f"{u.prenom} {u.nom}"

        return list(destinataires.items())   # [(email, nom), ...]
    finally:
        db.close()


def get_resp_classe_email(planning_id):
    """Compatibilité : retourne (email, nom) du premier destinataire resp. de classe."""
    results = get_resp_classe_emails(planning_id)
    return results[0] if results else (None, None)


def prochain_lundi():
    """Retourne la date du prochain lundi."""
    today = date.today()
    jours = (7 - today.weekday()) % 7
    if jours == 0:
        jours = 7
    return today + timedelta(days=jours)


# ============================================================
#  HELPERS EMAIL
# ============================================================

def _get_seances_list(planning) -> list:
    """
    Construit la liste de dicts de séances depuis un objet Planning ORM.
    Doit être appelé pendant que la session est encore active.
    """
    seances = []
    for s in sorted(planning.planning_seances,
                    key=lambda x: (x.date, x.heure_debut)):
        seances.append({
            "module"     : s.module.libelle if s.module else "-",
            "enseignant" : s.module.enseignant if s.module and s.module.enseignant else "",
            "date"       : s.date.strftime("%d/%m/%Y") if s.date else "-",
            "jour"       : JOURS[s.date.weekday()] if s.date else "-",
            "heure_debut": s.heure_debut.strftime("%H:%M") if s.heure_debut else "-",
            "heure_fin"  : s.heure_fin.strftime("%H:%M") if s.heure_fin else "-",
        })
    return seances


def _notifier_professeurs(seances_list: list, classe_n: str, semaine: str) -> None:
    """
    Envoie un email individuel à chaque enseignant présent dans le planning.
    Reçoit directement la liste de dicts (déjà construite pendant la session ORM).
    """
    from utils.mailer import email_planning_prof

    # Regrouper par enseignant
    profs: dict[str, list] = {}
    for s in seances_list:
        nom_prof = (s.get("enseignant") or "").strip()
        if not nom_prof:
            continue
        profs.setdefault(nom_prof, []).append(s)

    if not profs:
        return

    # Chercher les emails dans la table users par correspondance nom/prénom
    db = SessionLocal()
    try:
        all_users = db.query(User).filter(User.is_active == True).all()
        user_email_map: dict[str, tuple[str, str]] = {}
        for u in all_users:
            full1 = f"{u.prenom} {u.nom}".strip().lower()
            full2 = f"{u.nom} {u.prenom}".strip().lower()
            display = f"{u.prenom} {u.nom}".strip()
            user_email_map[full1] = (u.email, display)
            user_email_map[full2] = (u.email, display)

        for nom_prof, seances_prof in profs.items():
            match = user_email_map.get(nom_prof.strip().lower())
            if match:
                email_prof, display = match
                try:
                    email_planning_prof(
                        to           = email_prof,
                        nom_prof     = display,
                        classe       = classe_n,
                        semaine      = semaine,
                        seances_prof = seances_prof,
                    )
                except Exception:
                    pass   # ne jamais bloquer le workflow pour un email raté
    finally:
        db.close()


# ============================================================
#  COMPOSANTS UI
# ============================================================

def statut_badge(statut: str) -> html.Span:
    configs = {
        "brouillon": ("#6b7280", "#f3f4f6", "Brouillon"),
        "soumis"   : (BLEU,     "#dbeafe",  "Soumis"),
        "modifie"  : ("#d97706", "#fef3c7", "Modifié"),
        "valide"   : (VERT,     "#d1fae5",  "Validé"),
        "rejete"   : ("#ef4444", "#fee2e2",  "Rejeté"),
    }
    color, bg, label = configs.get(statut, ("#6b7280", "#f3f4f6", statut))
    return html.Span(label, style={
        "background"  : bg, "color": color,
        "padding"     : "3px 10px", "borderRadius": "999px",
        "fontSize"    : "0.72rem", "fontWeight": "700",
        "fontFamily"  : "'Inter', sans-serif"
    })


def label_style():
    return {
        "fontWeight": "600", "fontSize": "0.82rem", "color": "#374151",
        "marginBottom": "6px", "display": "block", "fontFamily": "'Inter', sans-serif"
    }


def input_style():
    return {
        "borderRadius": "8px", "border": "1.5px solid #d1d5db",
        "fontSize": "0.875rem", "fontFamily": "'Inter', sans-serif"
    }


def field(label_text, component):
    return html.Div(style={"marginBottom": "14px"}, children=[
        html.Label(label_text, style=label_style()),
        component
    ])


def btn_primary(label, btn_id, color=BLEU):
    return html.Button(label, id=btn_id, n_clicks=0, style={
        "background": color, "color": "#ffffff", "border": "none",
        "borderRadius": "8px", "padding": "9px 18px",
        "fontFamily": "'Montserrat', sans-serif", "fontWeight": "600",
        "fontSize": "0.82rem", "cursor": "pointer"
    })


def btn_outline(label, btn_id, color="#6b7280"):
    return html.Button(label, id=btn_id, n_clicks=0, style={
        "background": "transparent", "color": color,
        "border": f"1px solid {color}", "borderRadius": "8px",
        "padding": "9px 18px", "fontFamily": "'Inter', sans-serif",
        "cursor": "pointer", "marginLeft": "8px"
    })


# ============================================================
#  LAYOUT
# ============================================================

layout = html.Div([
    dcc.Store(id="planning-selectionne"),
    dcc.Store(id="planning-refresh"),
    dcc.Store(id="planning-session"),
    # Store pour l'id du planning sélectionné — doit être dans le layout statique
    dcc.Store(id="planning-detail-id", data=None),

    # -- Retour + En-tête --
    html.Div(style={"marginBottom": "24px"}, children=[
        html.A(href="/dashboard", style={
            "textDecoration": "none", "display": "inline-flex",
            "alignItems": "center", "gap": "6px", "marginBottom": "12px",
            "color": "#6b7280", "fontFamily": "'Inter', sans-serif",
            "fontSize": "0.82rem", "fontWeight": "500"
        }, children=[
            html.Span("arrow_back", className="material-symbols-outlined",
                      style={"fontSize": "18px", "verticalAlign": "middle"}),
            "Retour au tableau de bord"
        ]),
        html.H4("Planning Hebdomadaire", style={
            "fontFamily": "'Montserrat', sans-serif",
            "fontWeight": "800", "color": BLEU, "margin": "0"
        }),
        html.P("Proposition, validation et suivi des plannings de cours", style={
            "color": "#6b7280", "fontFamily": "'Inter', sans-serif", "margin": "4px 0 0"
        })
    ]),

    # -- Barre filtres + actions --
    html.Div(style={
        "background": "#ffffff", "borderRadius": "12px",
        "padding": "16px 24px", "border": "1px solid #e5e7eb",
        "marginBottom": "20px", "display": "flex",
        "alignItems": "center", "gap": "12px", "flexWrap": "wrap"
    }, children=[
        html.Div(style={"flex": "1", "minWidth": "160px"}, children=[
            dcc.Dropdown(
                id="planning-filtre-statut",
                placeholder="Filtrer par statut...",
                options=[
                    {"label": "Tous",      "value": "tous"},
                    {"label": "Brouillon", "value": "brouillon"},
                    {"label": "Soumis",    "value": "soumis"},
                    {"label": "Validé",    "value": "valide"},
                    {"label": "Rejeté",    "value": "rejete"},
                    {"label": "Modifié",   "value": "modifie"},
                ],
                value="tous",
                style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
            )
        ]),
        html.Div(
            id="planning-btn-container",
            style={"display": "flex", "gap": "8px"}
        ),
    ]),

    # -- Contenu principal --
    dbc.Row([
        # Colonne liste
        dbc.Col(
            html.Div(style={
                "background": "#ffffff", "borderRadius": "12px",
                "padding": "20px", "border": "1px solid #e5e7eb",
                "height": "100%"
            }, children=[
                html.Div(style={
                    "display": "flex", "justifyContent": "space-between",
                    "alignItems": "center", "marginBottom": "14px"
                }, children=[
                    html.H6("Plannings", style={
                        "fontFamily": "'Montserrat', sans-serif",
                        "fontWeight": "700", "color": BLEU, "margin": "0"
                    }),
                    html.Span(id="planning-nb", style={
                        "background": f"{BLEU}15", "color": BLEU,
                        "padding": "2px 10px", "borderRadius": "999px",
                        "fontSize": "0.75rem", "fontWeight": "700"
                    }),
                ]),
                html.Div(id="planning-liste"),
            ]),
            md=4
        ),
        # Colonne détail
        dbc.Col(
            html.Div(style={
                "background": "#ffffff", "borderRadius": "12px",
                "padding": "20px", "border": "1px solid #e5e7eb",
                "height": "100%"
            }, children=[
                html.Div(id="planning-detail", children=[
                    html.P("Sélectionnez un planning pour voir le détail.", style={
                        "color": "#9ca3af", "fontFamily": "'Inter', sans-serif",
                        "fontSize": "0.875rem", "textAlign": "center", "padding": "40px 0"
                    })
                ]),
                # Zone boutons d'action (visible dynamiquement)
                html.Div(id="planning-actions-container", style={"display": "none"}, children=[
                    html.Button("Valider / Rejeter", id="btn-open-validation",    n_clicks=0),
                    html.Button("Soumettre",         id="btn-soumettre-planning", n_clicks=0),
                ]),
            ]),
            md=8
        ),
    ], className="g-3"),

    # -- Feedback --
    html.Div(id="planning-feedback", style={"marginTop": "12px"}),

    # -- Modal création planning --
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Proposer un planning")),
        dbc.ModalBody([
            field("Semaine (lundi)", dbc.Input(
                id="planning-semaine", type="date",
                value=prochain_lundi().strftime("%Y-%m-%d"),
                style=input_style()
            )),
            field("Classe(s)", dcc.Dropdown(
                id="planning-classes",
                placeholder="Sélectionner une ou plusieurs classes",
                multi=True,
                style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
            )),

            html.Hr(style={"borderColor": "#e5e7eb"}),
            html.H6("Séances de la semaine", style={
                "fontFamily": "'Montserrat', sans-serif",
                "fontWeight": "700", "color": BLEU, "marginBottom": "12px"
            }),

            # Lignes séances dynamiques
            html.Div(id="planning-seances-container"),

            html.Button(
                "+ Ajouter une séance",
                id="btn-add-seance-planning",
                n_clicks=0,
                style={
                    "background": "transparent", "color": BLEU,
                    "border": f"1.5px dashed {BLEU}", "borderRadius": "8px",
                    "padding": "8px 16px", "fontFamily": "'Inter', sans-serif",
                    "fontWeight": "600", "fontSize": "0.82rem",
                    "cursor": "pointer", "width": "100%", "marginTop": "8px"
                }
            ),
            dcc.Store(id="planning-nb-seances", data=1),
            html.Div(id="planning-modal-feedback",
                     style={"color": "#ef4444", "fontSize": "0.8rem", "marginTop": "8px"})
        ]),
        dbc.ModalFooter([
            btn_primary("Enregistrer comme brouillon", "btn-save-brouillon", "#6b7280"),
            btn_primary("Soumettre",                   "btn-save-soumis",    BLEU),
            btn_outline("Annuler",                     "btn-cancel-planning"),
        ])
    ], id="modal-planning", is_open=False, size="xl"),

    # -- Modal validation (resp filière) --
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Valider / Rejeter le planning")),
        dbc.ModalBody([
            html.Div(id="modal-validation-content"),
            html.Hr(style={"borderColor": "#e5e7eb"}),
            field("Commentaire (obligatoire si rejet ou modification)", dbc.Textarea(
                id="validation-commentaire",
                placeholder="Votre commentaire...",
                rows=3,
                style={**input_style(), "resize": "none"}
            )),
            html.Div(id="validation-feedback",
                     style={"color": "#ef4444", "fontSize": "0.8rem"})
        ]),
        dbc.ModalFooter([
            btn_primary("Valider",  "btn-valider",  VERT),
            btn_primary("Modifier", "btn-modifier", OR),
            btn_primary("Rejeter",  "btn-rejeter",  "#ef4444"),
            btn_outline("Annuler",  "btn-cancel-validation"),
        ])
    ], id="modal-validation", is_open=False, size="lg"),

    # Boutons d'action statiques (cachés par défaut, rendus visibles par callback)
    # Nécessaire car Dash exige que les Input/State existent dans le layout statique
    html.Div(id="planning-actions-container", style={"display": "none"}, children=[
        html.Button("Valider / Rejeter", id="btn-open-validation",    n_clicks=0),
        html.Button("Soumettre",         id="btn-soumettre-planning", n_clicks=0),
    ]),

    html.Div(id="planning-dummy", style={"display": "none"})
])


# ============================================================
#  CALLBACKS
# ============================================================

@callback(
    Output("planning-session",      "data"),
    Output("planning-btn-container", "children"),
    Input("session-store", "data")
)
def init_page(session):
    if not session:
        return None, html.Div()
    role = session.get("role", "")
    btns = []
    if role in ("resp_classe", "admin"):
        btns.append(btn_primary("+ Nouveau planning", "btn-open-planning", BLEU))
    return session, html.Div(btns, style={"display": "flex", "gap": "8px"})


@callback(
    Output("planning-classes", "options"),
    Input("session-store", "data")
)
def load_classes(session):
    if not session:
        return []
    role    = session.get("role", "")
    user_id = session.get("user_id")
    return get_classes_for_user(role, user_id)


@callback(
    Output("planning-seances-container", "children"),
    Input("planning-nb-seances",         "data"),
    Input("planning-classes",            "value"),
)
def render_seances_form(nb, classes):
    if not nb:
        nb = 1
    modules_opts = []
    if classes:
        db = SessionLocal()
        try:
            for cid in classes:
                modules_opts += get_modules_by_classe(cid)
        finally:
            db.close()

    rows = []
    for i in range(nb):
        rows.append(
            html.Div(style={
                "border": "1px solid #e5e7eb", "borderRadius": "8px",
                "padding": "12px", "marginBottom": "8px", "background": "#fafafa"
            }, children=[
                html.Div(style={
                    "display": "flex", "justifyContent": "space-between",
                    "alignItems": "center", "marginBottom": "8px"
                }, children=[
                    html.Span(f"Séance {i + 1}", style={
                        "fontWeight": "600", "fontSize": "0.82rem",
                        "color": BLEU, "fontFamily": "'Montserrat', sans-serif"
                    }),
                ]),
                dbc.Row([
                    dbc.Col(field("Module", dcc.Dropdown(
                        id={"type": "ps-module", "index": i},
                        options=modules_opts,
                        placeholder="Module...",
                        style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.82rem"}
                    )), md=4),
                    dbc.Col(field("Date", dbc.Input(
                        id={"type": "ps-date", "index": i},
                        type="date", style=input_style()
                    )), md=3),
                    dbc.Col(field("Début", dbc.Input(
                        id={"type": "ps-debut", "index": i},
                        type="time", style=input_style()
                    )), md=2),
                    dbc.Col(field("Fin", dbc.Input(
                        id={"type": "ps-fin", "index": i},
                        type="time", style=input_style()
                    )), md=3),
                ], className="g-2")
            ])
        )
    return rows


@callback(
    Output("planning-nb-seances", "data"),
    Input("btn-add-seance-planning", "n_clicks"),
    State("planning-nb-seances",     "data"),
    prevent_initial_call=True
)
def add_seance_row(n, nb):
    return (nb or 1) + 1


@callback(
    Output("planning-liste", "children"),
    Output("planning-nb",    "children"),
    Input("planning-filtre-statut", "value"),
    Input("planning-refresh",       "data"),
    Input("planning-session",       "data")
)
def afficher_plannings(filtre, _, session):
    if not session:
        return html.Div(), "0"
    role    = session.get("role", "")
    user_id = session.get("user_id")
    plannings = get_plannings(role, user_id, filtre)

    if not plannings:
        return html.P("Aucun planning trouvé.", style={
            "color": "#9ca3af", "fontFamily": "'Inter', sans-serif",
            "fontSize": "0.875rem", "textAlign": "center", "padding": "20px"
        }), "0"

    items = [
        html.Div(
            id={"type": "planning-item", "index": p["id"]},
            style={
                "padding": "12px 14px", "borderRadius": "8px",
                "border": "1px solid #e5e7eb", "marginBottom": "8px",
                "cursor": "pointer", "background": "#fafafa",
                "transition": "border-color 0.2s"
            },
            children=[
                html.Div(style={
                    "display": "flex", "justifyContent": "space-between",
                    "alignItems": "center", "marginBottom": "6px"
                }, children=[
                    html.Div([
                        html.Span("Semaine du ", style={
                            "color": "#9ca3af", "fontSize": "0.72rem",
                            "fontFamily": "'Inter', sans-serif"
                        }),
                        html.Span(p["semaine"], style={
                            "fontWeight": "700", "color": "#111827",
                            "fontSize": "0.875rem", "fontFamily": "'Montserrat', sans-serif"
                        }),
                    ]),
                    statut_badge(p["statut"])
                ]),
                html.Div(style={"display": "flex", "gap": "10px", "flexWrap": "wrap"}, children=[
                    html.Span(p["classes"] or "Aucune classe", style={
                        "background": f"{BLEU}10", "color": BLEU,
                        "padding": "1px 7px", "borderRadius": "4px",
                        "fontSize": "0.7rem", "fontFamily": "'Inter', sans-serif",
                        "fontWeight": "500"
                    }),
                    html.Span(f"{p['nb_seances']} séance(s)", style={
                        "color": "#6b7280", "fontSize": "0.7rem",
                        "fontFamily": "'Inter', sans-serif"
                    }),
                    html.Span(f"Créé le {p['created_at']}", style={
                        "color": "#9ca3af", "fontSize": "0.7rem",
                        "fontFamily": "'Inter', sans-serif"
                    }),
                ])
            ]
        )
        for p in plannings
    ]
    return html.Div(items), str(len(plannings))


@callback(
    Output("planning-detail",        "children"),
    Output("planning-detail-id",     "data"),
    Output("planning-actions-container", "style"),
    Output("btn-open-validation",    "style"),
    Output("btn-soumettre-planning", "style"),
    Input({"type": "planning-item", "index": dash.ALL}, "n_clicks"),
    State("planning-session", "data"),
    prevent_initial_call=True
)
def afficher_detail(n_clicks, session):
    if not any(n_clicks):
        return html.Div(), None, {"display": "none"}, {}, {}

    planning_id = ctx.triggered_id["index"]
    detail = get_planning_detail(planning_id)
    if not detail:
        return html.P("Planning introuvable."), None, {"display": "none"}, {}, {}

    role = session.get("role", "") if session else ""

    # Styles des boutons selon statut et rôle
    btn_style_base = {
        "border": "none", "borderRadius": "8px", "padding": "8px 16px",
        "fontFamily": "'Montserrat', sans-serif", "fontWeight": "600",
        "fontSize": "0.82rem", "cursor": "pointer", "color": "#fff"
    }
    show_valider   = role in ("resp_filiere", "admin") and detail["statut"] == "soumis"
    show_soumettre = role in ("resp_classe", "admin")  and detail["statut"] == "brouillon"

    style_valider   = {**btn_style_base, "background": BLEU,
                       "display": "inline-block" if show_valider else "none"}
    style_soumettre = {**btn_style_base, "background": VERT,
                       "display": "inline-block" if show_soumettre else "none"}
    style_container = {"display": "flex", "gap": "8px", "marginTop": "12px"} \
                      if (show_valider or show_soumettre) else {"display": "none"}

    contenu_detail = _render_detail_content(detail)
    return contenu_detail, planning_id, style_container, style_valider, style_soumettre


def _render_detail_content(detail: dict):
    """Rendu HTML du détail d'un planning (sans les boutons d'action)."""
    return html.Div([
        # Header détail
        html.Div(style={
            "background": f"{BLEU}08", "borderRadius": "8px",
            "padding": "14px 16px", "marginBottom": "16px",
            "display": "flex", "justifyContent": "space-between", "alignItems": "center"
        }, children=[
            html.Div([
                html.Span("Semaine du ", style={
                    "color": "#9ca3af", "fontSize": "0.75rem",
                    "fontFamily": "'Inter', sans-serif"
                }),
                html.Span(detail["semaine"], style={
                    "fontWeight": "800", "color": BLEU,
                    "fontFamily": "'Montserrat', sans-serif"
                }),
                html.Div(", ".join(detail["classes"]), style={
                    "color": "#6b7280", "fontSize": "0.78rem",
                    "fontFamily": "'Inter', sans-serif", "marginTop": "2px"
                }),
            ]),
            statut_badge(detail["statut"]),
        ]),

        # Commentaire si présent
        html.Div(style={
            "background": "#fffbeb", "border": "1px solid #fde68a",
            "borderRadius": "8px", "padding": "10px 14px", "marginBottom": "16px",
            "fontSize": "0.82rem", "color": "#92400e",
            "fontFamily": "'Inter', sans-serif",
            "display": "block" if detail["commentaire"] else "none"
        }, children=f"💬 {detail['commentaire']}"),

        # Tableau séances
        html.H6("Séances programmées", style={
            "fontFamily": "'Montserrat', sans-serif",
            "fontWeight": "700", "color": BLEU,
            "fontSize": "0.85rem", "marginBottom": "10px"
        }),

        html.Table(
            style={"width": "100%", "borderCollapse": "collapse",
                   "fontSize": "0.82rem", "fontFamily": "'Inter', sans-serif"},
            children=[
                html.Thead(html.Tr([
                    html.Th("Jour",       style={"padding": "8px 10px", "textAlign": "left",
                                                  "color": BLEU, "fontWeight": "700",
                                                  "fontSize": "0.72rem", "textTransform": "uppercase",
                                                  "borderBottom": "2px solid #e5e7eb"}),
                    html.Th("Date",       style={"padding": "8px 10px", "textAlign": "left",
                                                  "color": BLEU, "fontWeight": "700",
                                                  "fontSize": "0.72rem", "textTransform": "uppercase",
                                                  "borderBottom": "2px solid #e5e7eb"}),
                    html.Th("Module",     style={"padding": "8px 10px", "textAlign": "left",
                                                  "color": BLEU, "fontWeight": "700",
                                                  "fontSize": "0.72rem", "textTransform": "uppercase",
                                                  "borderBottom": "2px solid #e5e7eb"}),
                    html.Th("Enseignant", style={"padding": "8px 10px", "textAlign": "left",
                                                  "color": BLEU, "fontWeight": "700",
                                                  "fontSize": "0.72rem", "textTransform": "uppercase",
                                                  "borderBottom": "2px solid #e5e7eb"}),
                    html.Th("Horaire",    style={"padding": "8px 10px", "textAlign": "left",
                                                  "color": BLEU, "fontWeight": "700",
                                                  "fontSize": "0.72rem", "textTransform": "uppercase",
                                                  "borderBottom": "2px solid #e5e7eb"}),
                ])),
                html.Tbody([
                    html.Tr(
                        style={"borderBottom": "1px solid #f3f4f6",
                               "background": "#fafafa" if i % 2 == 0 else "#ffffff"},
                        children=[
                            html.Td(s["jour"],       style={"padding": "8px 10px", "color": "#6b7280"}),
                            html.Td(s["date"],       style={"padding": "8px 10px", "color": "#374151",
                                                             "whiteSpace": "nowrap"}),
                            html.Td(s["module"],     style={"padding": "8px 10px", "color": "#111827",
                                                             "fontWeight": "500"}),
                            html.Td(s.get("enseignant") or "—",
                                                     style={"padding": "8px 10px", "color": "#6b7280"}),
                            html.Td(f"{s['heure_debut']} – {s['heure_fin']}",
                                                     style={"padding": "8px 10px", "color": "#6b7280",
                                                             "whiteSpace": "nowrap"}),
                        ]
                    )
                    for i, s in enumerate(detail["seances"])
                ]) if detail["seances"] else html.Tbody(html.Tr(
                    html.Td("Aucune séance enregistrée.", colSpan=5,
                            style={"padding": "16px", "textAlign": "center",
                                   "color": "#9ca3af", "fontStyle": "italic"})
                ))
            ]
        ),
    ])


# -- Modals --
@callback(
    Output("modal-planning", "is_open"),
    Input("btn-open-planning",   "n_clicks"),
    Input("btn-cancel-planning", "n_clicks"),
    Input("btn-save-brouillon",  "n_clicks"),
    Input("btn-save-soumis",     "n_clicks"),
    prevent_initial_call=True
)
def toggle_modal_planning(o, c, b, s):
    return ctx.triggered_id == "btn-open-planning"


@callback(
    Output("modal-validation", "is_open"),
    Input("btn-open-validation",   "n_clicks"),
    Input("btn-cancel-validation", "n_clicks"),
    Input("btn-valider",           "n_clicks"),
    Input("btn-rejeter",           "n_clicks"),
    Input("btn-modifier",          "n_clicks"),
    prevent_initial_call=True
)
def toggle_modal_validation(o, c, v, r, m):
    return ctx.triggered_id == "btn-open-validation"


@callback(
    Output("planning-modal-feedback", "children"),
    Output("planning-refresh",        "data"),
    Output("modal-planning",          "is_open", allow_duplicate=True),
    Input("btn-save-brouillon",       "n_clicks"),
    Input("btn-save-soumis",          "n_clicks"),
    State("planning-semaine",         "value"),
    State("planning-classes",         "value"),
    State({"type": "ps-module", "index": dash.ALL}, "value"),
    State({"type": "ps-date",   "index": dash.ALL}, "value"),
    State({"type": "ps-debut",  "index": dash.ALL}, "value"),
    State({"type": "ps-fin",    "index": dash.ALL}, "value"),
    State("planning-session",         "data"),
    prevent_initial_call=True
)
def save_planning(nb, ns, semaine, classes, modules, dates, debuts, fins, session):
    if ctx.triggered_id not in ("btn-save-brouillon", "btn-save-soumis"):
        return "", None, False

    if not semaine or not classes:
        return "La semaine et au moins une classe sont obligatoires.", None, True

    db = SessionLocal()
    try:
        from datetime import time as dtime
        semaine_date = datetime.strptime(semaine, "%Y-%m-%d").date()
        statut = (StatutPlanningEnum.brouillon
                  if ctx.triggered_id == "btn-save-brouillon"
                  else StatutPlanningEnum.soumis)

        planning = Planning(
            semaine    = semaine_date,
            statut     = statut,
            created_by = session.get("user_id"),
            created_at = datetime.now(),
            updated_at = datetime.now()
        )
        db.add(planning)
        db.flush()

        # Classes
        for cid in classes:
            db.add(PlanningClasse(planning_id=planning.id, classe_id=cid))

        # Séances
        for mod, dat, deb, fin in zip(modules, dates, debuts, fins):
            if not all([mod, dat, deb, fin]):
                continue
            db.add(PlanningSeance(
                planning_id = planning.id,
                module_id   = mod,
                date        = datetime.strptime(dat, "%Y-%m-%d").date(),
                heure_debut = dtime(*map(int, deb.split(":"))),
                heure_fin   = dtime(*map(int, fin.split(":")))
            ))

        db.commit()

        # Envoyer emails si soumis
        if statut == StatutPlanningEnum.soumis and classes:
            try:
                from utils.mailer import email_planning_soumis, email_planning_confirmation_rc

                # Recharger le planning avec ses relations pour construire les séances
                db.refresh(planning)
                seances_list = _get_seances_list(planning)

                user     = db.query(User).filter(User.id == session.get("user_id")).first()
                nom_rc   = f"{user.prenom} {user.nom}" if user else "Responsable"
                classe_n = db.query(Classe).filter(Classe.id == classes[0]).first()
                nom_classe = classe_n.nom if classe_n else "-"
                semaine_str = semaine_date.strftime("%d/%m/%Y")

                # Email au resp. filière
                email_resp, nom_resp = get_resp_filiere_email(classes[0])
                if email_resp:
                    email_planning_soumis(
                        to               = email_resp,
                        nom_resp_filiere = nom_resp,
                        nom_resp_classe  = nom_rc,
                        classe           = nom_classe,
                        semaine          = semaine_str,
                        seances          = seances_list,
                        planning_id      = planning.id,
                    )

                # Email de confirmation au resp. de classe (créateur)
                if user and user.email:
                    email_planning_confirmation_rc(
                        to          = user.email,
                        nom_rc      = nom_rc,
                        classe      = nom_classe,
                        semaine     = semaine_str,
                        seances     = seances_list,
                    )
            except Exception:
                pass

        return "", True, False

    except Exception as e:
        db.rollback()
        return f"Erreur : {str(e)}", None, True
    finally:
        db.close()


@callback(
    Output("validation-feedback", "children"),
    Output("planning-refresh",    "data", allow_duplicate=True),
    Output("modal-validation",    "is_open", allow_duplicate=True),
    Input("btn-valider",          "n_clicks"),
    Input("btn-rejeter",          "n_clicks"),
    Input("btn-modifier",         "n_clicks"),
    State("planning-detail-id",   "data"),
    State("validation-commentaire", "value"),
    prevent_initial_call=True
)
def valider_rejeter_planning(v, r, m, planning_id, commentaire):
    if ctx.triggered_id not in ("btn-valider", "btn-rejeter", "btn-modifier"):
        return "", None, True

    action_map = {
        "btn-valider" : StatutPlanningEnum.valide,
        "btn-rejeter" : StatutPlanningEnum.rejete,
        "btn-modifier": StatutPlanningEnum.modifie,
    }
    nouveau_statut = action_map[ctx.triggered_id]

    if ctx.triggered_id in ("btn-rejeter", "btn-modifier") and not commentaire:
        return "Un commentaire est obligatoire pour rejeter ou modifier.", None, True

    db = SessionLocal()
    try:
        planning = db.query(Planning).filter(Planning.id == planning_id).first()
        if not planning:
            return "Planning introuvable.", None, True

        planning.statut      = nouveau_statut
        planning.commentaire = commentaire or ""
        planning.updated_at  = datetime.now()
        db.commit()

        # Email notification
        try:
            from utils.mailer import (
                email_planning_valide, email_planning_rejete, email_planning_modifie
            )
            destinataires = get_resp_classe_emails(planning_id)
            classes  = [pc.classe.nom for pc in planning.planning_classes if pc.classe]
            classe_n = classes[0] if classes else "-"
            semaine  = planning.semaine.strftime("%d/%m/%Y") if planning.semaine else "-"

            # Construire la liste des séances AVANT db.close()
            seances_list = _get_seances_list(planning)

            for email_rc, nom_rc in destinataires:
                if ctx.triggered_id == "btn-valider":
                    email_planning_valide(
                        email_rc, nom_rc, classe_n, semaine,
                        seances=seances_list
                    )
                elif ctx.triggered_id == "btn-rejeter":
                    email_planning_rejete(email_rc, nom_rc, classe_n, semaine, commentaire)
                elif ctx.triggered_id == "btn-modifier":
                    email_planning_modifie(email_rc, nom_rc, classe_n, semaine, commentaire)

            # Notifier les professeurs uniquement à la validation
            if ctx.triggered_id == "btn-valider":
                _notifier_professeurs(seances_list, classe_n, semaine)

        except Exception:
            pass

        return "", True, False

    except Exception as e:
        db.rollback()
        return f"Erreur : {str(e)}", None, True
    finally:
        db.close()


@callback(
    Output("planning-feedback",      "children"),
    Output("planning-refresh",       "data", allow_duplicate=True),
    Input("btn-soumettre-planning",  "n_clicks"),
    State("planning-detail-id",      "data"),
    State("planning-session",        "data"),
    prevent_initial_call=True
)
def soumettre_planning(n, planning_id, session):
    if not planning_id:
        return html.Div(), None
    db = SessionLocal()
    try:
        planning = db.query(Planning).filter(Planning.id == planning_id).first()
        if not planning:
            return dbc.Alert("Planning introuvable.", color="danger"), None
        planning.statut     = StatutPlanningEnum.soumis
        planning.updated_at = datetime.now()
        db.commit()

        # Emails : resp. filière + confirmation au resp. de classe
        try:
            from utils.mailer import email_planning_soumis, email_planning_confirmation_rc
            db.refresh(planning)
            seances_list = _get_seances_list(planning)

            classes_ids = [pc.classe_id for pc in planning.planning_classes]
            if classes_ids:
                classe_n = db.query(Classe).filter(Classe.id == classes_ids[0]).first()
                nom_classe  = classe_n.nom if classe_n else "-"
                semaine_str = planning.semaine.strftime("%d/%m/%Y") if planning.semaine else "-"
                user        = db.query(User).filter(User.id == session.get("user_id")).first()
                nom_rc      = f"{user.prenom} {user.nom}" if user else "Responsable"

                # Email au resp. filière
                email_resp, nom_resp = get_resp_filiere_email(classes_ids[0])
                if email_resp:
                    email_planning_soumis(
                        to               = email_resp,
                        nom_resp_filiere = nom_resp,
                        nom_resp_classe  = nom_rc,
                        classe           = nom_classe,
                        semaine          = semaine_str,
                        seances          = seances_list,
                        planning_id      = planning.id,
                    )

                # Confirmation au resp. de classe (créateur ou délégué)
                destinataires = get_resp_classe_emails(planning.id)
                for email_rc, nom_dest in destinataires:
                    email_planning_confirmation_rc(
                        to      = email_rc,
                        nom_rc  = nom_dest,
                        classe  = nom_classe,
                        semaine = semaine_str,
                        seances = seances_list,
                    )
        except Exception:
            pass

        return dbc.Alert("Planning soumis avec succès.", color="success",
                         dismissable=True, duration=4000), True
    except Exception as e:
        db.rollback()
        return dbc.Alert(f"Erreur : {str(e)}", color="danger"), None
    finally:
        db.close()