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

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]


# ============================================================
#  UTILITAIRES DB
# ============================================================

def get_classes():
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
    db = SessionLocal()
    try:
        q = db.query(Planning)
        if role == "resp_classe":
            q = q.filter(Planning.created_by == user_id)
        if filtre_statut and filtre_statut != "tous":
            q = q.filter(Planning.statut == filtre_statut)
        plannings = q.order_by(Planning.semaine.desc()).all()
        result = []
        for p in plannings:
            classes  = [pc.classe.nom for pc in p.planning_classes if pc.classe]
            seances  = p.planning_seances
            result.append({
                "id"       : p.id,
                "semaine"  : p.semaine.strftime("%d/%m/%Y") if p.semaine else "-",
                "statut"   : p.statut.value if p.statut else "-",
                "classes"  : ", ".join(classes),
                "nb_seances": len(seances),
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
    """Retourne l'email du responsable de filiere d'une classe."""
    db = SessionLocal()
    try:
        classe = db.query(Classe).filter(Classe.id == classe_id).first()
        if not classe:
            return None
        resp = db.query(ResponsableFiliere).filter(
            ResponsableFiliere.filiere_id == classe.filiere_id
        ).first()
        if resp and resp.user:
            return resp.user.email, f"{resp.user.prenom} {resp.user.nom}"
        return None, None
    finally:
        db.close()

def get_resp_classe_email(planning_id):
    """Retourne l'email du responsable de classe qui a cree le planning."""
    db = SessionLocal()
    try:
        p = db.query(Planning).filter(Planning.id == planning_id).first()
        if not p or not p.created_by_user:
            return None, None
        u = p.created_by_user
        return u.email, f"{u.prenom} {u.nom}"
    finally:
        db.close()

def prochain_lundi():
    """Retourne la date du prochain lundi."""
    today = date.today()
    jours = (7 - today.weekday()) % 7
    if jours == 0:
        jours = 7
    return today + timedelta(days=jours)


# ============================================================
#  COMPOSANTS UI
# ============================================================

def statut_badge(statut: str) -> html.Span:
    configs = {
        "brouillon": ("#6b7280", "#f3f4f6", "Brouillon"),
        "soumis"   : (BLEU,     "#dbeafe",  "Soumis"),
        "modifie"  : ("#d97706", "#fef3c7", "Modifie"),
        "valide"   : (VERT,     "#d1fae5",  "Valide"),
        "rejete"   : ("#ef4444", "#fee2e2",  "Rejete"),
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

    # -- Retour + En-tete --
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
                    {"label": "Valide",    "value": "valide"},
                    {"label": "Rejete",    "value": "rejete"},
                    {"label": "Modifie",   "value": "modifie"},
                ],
                value="tous",
                style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
            )
        ]),
        html.Div(id="planning-btn-container")
    ]),

    # -- Feedback --
    html.Div(id="planning-feedback", style={"marginBottom": "12px"}),

    # -- Contenu principal --
    dbc.Row(style={"alignItems": "stretch"}, children=[

        # Liste plannings
        dbc.Col(
            html.Div(style={
                "background": "#ffffff", "borderRadius": "12px",
                "padding": "20px", "border": "1px solid #e5e7eb",
                "height": "100%", "display": "flex", "flexDirection": "column"
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
                        "background": f"{BLEU}10", "color": BLEU,
                        "padding": "2px 10px", "borderRadius": "999px",
                        "fontSize": "0.72rem", "fontWeight": "700",
                        "fontFamily": "'Montserrat', sans-serif"
                    })
                ]),
                html.Div(id="planning-liste",
                         style={"flex": "1", "overflowY": "auto", "maxHeight": "560px"})
            ]),
            md=5
        ),

        # Detail planning
        dbc.Col(
            html.Div(style={
                "background": "#ffffff", "borderRadius": "12px",
                "padding": "20px", "border": "1px solid #e5e7eb",
                "height": "100%", "display": "flex", "flexDirection": "column"
            }, children=[
                html.H6("Detail du planning", style={
                    "fontFamily": "'Montserrat', sans-serif",
                    "fontWeight": "700", "color": BLEU, "marginBottom": "14px"
                }),
                html.Div(id="planning-detail",
                         style={"flex": "1", "overflowY": "auto", "maxHeight": "560px"})
            ]),
            md=7
        )
    ], className="g-3"),

    # -- Modal nouveau planning --
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
                placeholder="Selectionner une ou plusieurs classes",
                multi=True,
                style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
            )),

            html.Hr(style={"borderColor": "#e5e7eb"}),
            html.H6("Seances de la semaine", style={
                "fontFamily": "'Montserrat', sans-serif",
                "fontWeight": "700", "color": BLEU, "marginBottom": "12px"
            }),

            # Lignes seances dynamiques
            html.Div(id="planning-seances-container"),

            html.Button(
                "+ Ajouter une seance",
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

    # -- Modal validation (resp filiere) --
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
            btn_primary("Valider",   "btn-valider",  VERT),
            btn_primary("Modifier",  "btn-modifier",  OR),
            btn_primary("Rejeter",   "btn-rejeter",  "#ef4444"),
            btn_outline("Annuler",   "btn-cancel-validation"),
        ])
    ], id="modal-validation", is_open=False, size="lg"),

    html.Div(id="planning-dummy", style={"display": "none"})
])


# ============================================================
#  CALLBACKS
# ============================================================

@callback(
    Output("planning-session",     "data"),
    Output("planning-btn-container","children"),
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
def load_classes(_):
    return get_classes()


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
                html.Div(style={"display": "flex", "justifyContent": "space-between",
                                "alignItems": "center", "marginBottom": "8px"}, children=[
                    html.Span(f"Seance {i + 1}", style={
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
                    dbc.Col(field("Debut", dbc.Input(
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
    State("planning-nb-seances",    "data"),
    prevent_initial_call=True
)
def add_seance_row(n, nb):
    return (nb or 1) + 1


@callback(
    Output("planning-liste",   "children"),
    Output("planning-nb",      "children"),
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
        return html.P("Aucun planning trouve.", style={
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
                    html.Span(f"{p['nb_seances']} seance(s)", style={
                        "color": "#6b7280", "fontSize": "0.7rem",
                        "fontFamily": "'Inter', sans-serif"
                    }),
                    html.Span(f"Cree le {p['created_at']}", style={
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
    Output("planning-detail", "children"),
    Input({"type": "planning-item", "index": dash.ALL}, "n_clicks"),
    State("planning-session", "data"),
    prevent_initial_call=True
)
def afficher_detail(n_clicks, session):
    if not any(n_clicks):
        return html.Div()
    planning_id = ctx.triggered_id["index"]
    detail = get_planning_detail(planning_id)
    if not detail:
        return html.P("Planning introuvable.")

    role = session.get("role", "") if session else ""

    # Grouper seances par jour
    jours_data = {}
    for s in detail["seances"]:
        jour = s["jour"]
        if jour not in jours_data:
            jours_data[jour] = []
        jours_data[jour].append(s)

    # Boutons action selon statut et role
    action_btns = []
    if role in ("resp_filiere", "admin") and detail["statut"] == "soumis":
        action_btns.append(
            html.Button("Valider / Rejeter", id="btn-open-validation", n_clicks=0,
                        style={
                            "background": BLEU, "color": "#fff", "border": "none",
                            "borderRadius": "8px", "padding": "8px 16px",
                            "fontFamily": "'Montserrat', sans-serif", "fontWeight": "600",
                            "fontSize": "0.82rem", "cursor": "pointer"
                        })
        )
    if role in ("resp_classe", "admin") and detail["statut"] == "brouillon":
        action_btns.append(
            html.Button("Soumettre", id="btn-soumettre-planning", n_clicks=0,
                        style={
                            "background": VERT, "color": "#fff", "border": "none",
                            "borderRadius": "8px", "padding": "8px 16px",
                            "fontFamily": "'Montserrat', sans-serif", "fontWeight": "600",
                            "fontSize": "0.82rem", "cursor": "pointer"
                        })
        )

    return html.Div([
        # Header detail
        html.Div(style={
            "background": f"{BLEU}08", "borderRadius": "10px",
            "padding": "14px 16px", "marginBottom": "16px",
            "border": f"1px solid {BLEU}20"
        }, children=[
            html.Div(style={
                "display": "flex", "justifyContent": "space-between",
                "alignItems": "center", "marginBottom": "8px"
            }, children=[
                html.Div([
                    html.Span("Semaine du ", style={
                        "color": "#9ca3af", "fontSize": "0.75rem",
                        "fontFamily": "'Inter', sans-serif"
                    }),
                    html.Span(detail["semaine"], style={
                        "fontWeight": "800", "color": BLEU,
                        "fontSize": "1rem", "fontFamily": "'Montserrat', sans-serif"
                    }),
                ]),
                statut_badge(detail["statut"])
            ]),
            html.Div(style={"display": "flex", "gap": "8px", "flexWrap": "wrap",
                            "marginBottom": "8px"}, children=[
                html.Span(c, style={
                    "background": f"{BLEU}12", "color": BLEU,
                    "padding": "2px 8px", "borderRadius": "4px",
                    "fontSize": "0.72rem", "fontWeight": "600",
                    "fontFamily": "'Inter', sans-serif"
                }) for c in detail["classes"]
            ]),
            html.Div(action_btns, style={"display": "flex", "gap": "8px"})
        ]),

        # Commentaire si present
        html.Div(style={
            "background": "#fffbeb", "border": "1px solid #fde68a",
            "borderRadius": "8px", "padding": "10px 14px", "marginBottom": "14px"
        }, children=[
            html.Span("Commentaire : ", style={
                "fontWeight": "600", "fontSize": "0.82rem",
                "color": "#d97706", "fontFamily": "'Montserrat', sans-serif"
            }),
            html.Span(detail["commentaire"], style={
                "fontSize": "0.82rem", "color": "#374151",
                "fontFamily": "'Inter', sans-serif"
            })
        ]) if detail["commentaire"] else html.Div(),

        # Seances par jour
        html.H6("Seances planifiees", style={
            "fontFamily": "'Montserrat', sans-serif", "fontWeight": "700",
            "color": BLEU, "marginBottom": "10px"
        }),

        html.Div([
            html.Div(style={"marginBottom": "12px"}, children=[
                html.Div(jour, style={
                    "background": f"{VERT}10", "color": VERT,
                    "padding": "4px 12px", "borderRadius": "6px",
                    "fontWeight": "700", "fontSize": "0.78rem",
                    "fontFamily": "'Montserrat', sans-serif", "marginBottom": "6px"
                }),
                html.Div([
                    html.Div(style={
                        "display": "grid",
                        "gridTemplateColumns": "1fr 80px 100px",
                        "gap": "8px", "alignItems": "center",
                        "padding": "8px 12px", "borderRadius": "6px",
                        "border": "1px solid #f3f4f6", "marginBottom": "4px",
                        "background": "#ffffff"
                    }, children=[
                        html.Div([
                            html.Span(s["code"], style={
                                "background": f"{BLEU}12", "color": BLEU,
                                "padding": "1px 6px", "borderRadius": "3px",
                                "fontSize": "0.68rem", "fontWeight": "700",
                                "fontFamily": "'Montserrat', sans-serif",
                                "marginRight": "6px"
                            }),
                            html.Span(s["module"], style={
                                "fontSize": "0.82rem", "color": "#374151",
                                "fontFamily": "'Inter', sans-serif", "fontWeight": "500"
                            })
                        ]),
                        html.Span(s["date"], style={
                            "fontSize": "0.75rem", "color": "#6b7280",
                            "fontFamily": "'Inter', sans-serif", "textAlign": "center"
                        }),
                        html.Span(f"{s['heure_debut']} - {s['heure_fin']}", style={
                            "fontSize": "0.75rem", "color": "#6b7280",
                            "fontFamily": "'Inter', sans-serif", "textAlign": "center"
                        })
                    ])
                    for s in seances_jour
                ])
            ])
            for jour, seances_jour in jours_data.items()
        ]) if detail["seances"] else html.P("Aucune seance planifiee.", style={
            "color": "#9ca3af", "fontFamily": "'Inter', sans-serif",
            "fontSize": "0.875rem", "textAlign": "center"
        }),

        dcc.Store(id="planning-detail-id", data=planning_id)
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
    Input("btn-open-validation",    "n_clicks"),
    Input("btn-cancel-validation",  "n_clicks"),
    Input("btn-valider",            "n_clicks"),
    Input("btn-rejeter",            "n_clicks"),
    Input("btn-modifier",           "n_clicks"),
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

    statut = (StatutPlanningEnum.brouillon
              if ctx.triggered_id == "btn-save-brouillon"
              else StatutPlanningEnum.soumis)

    db = SessionLocal()
    try:
        from datetime import time as dtime
        semaine_date = datetime.strptime(semaine, "%Y-%m-%d").date()
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

        # Seances
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

        # Envoyer email si soumis
        if statut == StatutPlanningEnum.soumis and classes:
            try:
                from utils.mailer import email_planning_soumis
                email_resp, nom_resp = get_resp_filiere_email(classes[0])
                if email_resp:
                    user = db.query(User).filter(
                        User.id == session.get("user_id")
                    ).first()
                    nom_rc   = f"{user.prenom} {user.nom}" if user else "Responsable"
                    classe_n = db.query(Classe).filter(Classe.id == classes[0]).first()
                    email_planning_soumis(
                        to               = email_resp,
                        nom_resp_filiere = nom_resp,
                        nom_resp_classe  = nom_rc,
                        classe           = classe_n.nom if classe_n else "-",
                        semaine          = semaine_date.strftime("%d/%m/%Y"),
                        seances          = [],
                        planning_id      = planning.id
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
    Output("validation-feedback",  "children"),
    Output("planning-refresh",     "data", allow_duplicate=True),
    Output("modal-validation",     "is_open", allow_duplicate=True),
    Input("btn-valider",           "n_clicks"),
    Input("btn-rejeter",           "n_clicks"),
    Input("btn-modifier",          "n_clicks"),
    State("validation-commentaire","value"),
    State("planning-detail-id",    "data"),
    State("planning-session",      "data"),
    prevent_initial_call=True
)
def valider_planning(v, r, m, commentaire, planning_id, session):
    if ctx.triggered_id not in ("btn-valider", "btn-rejeter", "btn-modifier"):
        return "", None, False
    if not planning_id:
        return "Aucun planning selectionne.", None, True

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

        planning.statut     = nouveau_statut
        planning.commentaire = commentaire or ""
        planning.updated_at  = datetime.now()
        db.commit()

        # Email notification
        try:
            from utils.mailer import (
                email_planning_valide, email_planning_rejete, email_planning_modifie
            )
            email_rc, nom_rc = get_resp_classe_email(planning_id)
            classes = [pc.classe.nom for pc in planning.planning_classes if pc.classe]
            classe_n = classes[0] if classes else "-"
            semaine  = planning.semaine.strftime("%d/%m/%Y") if planning.semaine else "-"

            if email_rc:
                if ctx.triggered_id == "btn-valider":
                    email_planning_valide(email_rc, nom_rc, classe_n, semaine)
                elif ctx.triggered_id == "btn-rejeter":
                    email_planning_rejete(email_rc, nom_rc, classe_n, semaine, commentaire)
                elif ctx.triggered_id == "btn-modifier":
                    email_planning_modifie(email_rc, nom_rc, classe_n, semaine, commentaire)
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
        return dbc.Alert("Planning soumis avec succes.", color="success",
                         dismissable=True,
                         style={"fontFamily": "'Inter', sans-serif",
                                "fontSize": "0.875rem"}), True
    except Exception as e:
        db.rollback()
        return dbc.Alert(f"Erreur : {str(e)}", color="danger"), None
    finally:
        db.close()