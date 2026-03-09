# ============================================================
#  SGA ENSAE — pages/seances.py
#  Module 4 : Cahier de texte et Presences
#  Python 3.11 · Dash 2.17.0
# ============================================================

import dash
from dash import html, dcc, callback, Input, Output, State, ctx, ALL
import dash_bootstrap_components as dbc
from auth import require_auth
from database import SessionLocal
from models import Seance, Presence, Module, Classe, Etudiant, User
from utils.access_helpers import get_classes_for_user, get_default_classe_id
from datetime import date

dash.register_page(__name__, path="/seances", title="SGA ENSAE — Seances et Presences")

BLEU = "#003580"
VERT = "#006B3F"
OR   = "#F5A623"


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
        modules = db.query(Module).filter(Module.classe_id == classe_id).all()
        return [{"label": f"{m.code} — {m.libelle}", "value": m.id} for m in modules]
    finally:
        db.close()

def get_etudiants_by_classe(classe_id):
    db = SessionLocal()
    try:
        etudiants = db.query(Etudiant).filter(Etudiant.classe_id == classe_id).all()
        return [
            {
                "id"      : e.id,
                "nom"     : e.user.nom if e.user else "",
                "prenom"  : e.user.prenom if e.user else "",
                "matricule": e.matricule
            }
            for e in etudiants
        ]
    finally:
        db.close()

def get_seances(classe_id=None, module_id=None):
    db = SessionLocal()
    try:
        q = db.query(Seance)
        if module_id:
            q = q.filter(Seance.module_id == module_id)
        elif classe_id:
            module_ids = [m.id for m in db.query(Module).filter(Module.classe_id == classe_id).all()]
            q = q.filter(Seance.module_id.in_(module_ids))
        seances = q.order_by(Seance.date.desc()).all()
        return [
            {
                "id"        : s.id,
                "date"      : s.date.strftime("%d/%m/%Y") if s.date else "-",
                "module"    : s.module.libelle if s.module else "-",
                "code"      : s.module.code if s.module else "-",
                "debut"     : s.heure_debut.strftime("%H:%M") if s.heure_debut else "-",
                "fin"       : s.heure_fin.strftime("%H:%M") if s.heure_fin else "-",
                "theme"     : s.theme or "-",
                "nb_absents": db.query(Presence).filter(
                    Presence.seance_id == s.id,
                    Presence.present == False
                ).count(),
                "nb_total"  : db.query(Presence).filter(Presence.seance_id == s.id).count(),
            }
            for s in seances
        ]
    finally:
        db.close()


# ============================================================
#  COMPOSANTS UI
# ============================================================

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

def btn_outline(label, btn_id):
    return html.Button(label, id=btn_id, n_clicks=0, style={
        "background": "transparent", "color": "#6b7280",
        "border": "1px solid #d1d5db", "borderRadius": "8px",
        "padding": "9px 18px", "fontFamily": "'Inter', sans-serif",
        "cursor": "pointer", "marginLeft": "8px"
    })

def badge_absent(nb_absents, nb_total):
    if nb_total == 0:
        return html.Span("Aucun etudiant", style={
            "color": "#9ca3af", "fontSize": "0.72rem", "fontFamily": "'Inter', sans-serif"
        })
    color = "#ef4444" if nb_absents > 0 else VERT
    return html.Span(
        f"{nb_absents} absent(s) / {nb_total}",
        style={
            "background" : f"{color}15",
            "color"      : color,
            "padding"    : "2px 8px",
            "borderRadius": "999px",
            "fontSize"   : "0.72rem",
            "fontWeight" : "600",
            "fontFamily" : "'Inter', sans-serif"
        }
    )


# ============================================================
#  LAYOUT
# ============================================================

layout = html.Div([
    dcc.Store(id="seances-classe-store"),
    dcc.Store(id="seances-refresh"),

    # -- Retour + En-tete --
    html.Div(style={"marginBottom": "24px"}, children=[
        html.A(
            href="/dashboard",
            style={
                "textDecoration": "none", "display": "inline-flex",
                "alignItems": "center", "gap": "6px", "marginBottom": "12px",
                "color": "#6b7280", "fontFamily": "'Inter', sans-serif",
                "fontSize": "0.82rem", "fontWeight": "500"
            },
            children=[
                html.Span("arrow_back", className="material-symbols-outlined",
                          style={"fontSize": "18px", "verticalAlign": "middle"}),
                "Retour au tableau de bord"
            ]
        ),
        html.H4("Seances et Presences", style={
            "fontFamily": "'Montserrat', sans-serif",
            "fontWeight": "800", "color": BLEU, "margin": "0"
        }),
        html.P("Cahier de texte numerique — enregistrement des seances et appel", style={
            "color": "#6b7280", "fontFamily": "'Inter', sans-serif", "margin": "4px 0 0"
        })
    ]),

    # -- Barre filtres + action --
    html.Div(
        style={
            "background": "#ffffff", "borderRadius": "12px",
            "padding": "16px 24px", "border": "1px solid #e5e7eb",
            "marginBottom": "20px", "display": "flex",
            "alignItems": "center", "gap": "12px", "flexWrap": "wrap"
        },
        children=[
            html.Div(style={"flex": "1", "minWidth": "180px"}, children=[
                dcc.Dropdown(
                    id="seances-filtre-classe",
                    placeholder="Filtrer par classe...",
                    style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
                )
            ]),
            html.Div(style={"flex": "1", "minWidth": "180px"}, children=[
                dcc.Dropdown(
                    id="seances-filtre-module",
                    placeholder="Filtrer par module...",
                    style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
                )
            ]),
            btn_primary("+ Nouvelle seance", "btn-open-seance", BLEU),
        ]
    ),

    # -- Historique des seances --
    html.Div(
        style={
            "background": "#ffffff", "borderRadius": "12px",
            "padding": "20px 24px", "border": "1px solid #e5e7eb",
            "marginBottom": "24px"
        },
        children=[
            html.Div(style={
                "display": "flex", "justifyContent": "space-between",
                "alignItems": "center", "marginBottom": "16px"
            }, children=[
                html.H6("Historique des seances", style={
                    "fontFamily": "'Montserrat', sans-serif",
                    "fontWeight": "700", "color": BLEU, "margin": "0"
                }),
                html.Span(id="seances-nb-total", style={
                    "background": f"{BLEU}10", "color": BLEU,
                    "padding": "2px 10px", "borderRadius": "999px",
                    "fontSize": "0.72rem", "fontWeight": "700",
                    "fontFamily": "'Montserrat', sans-serif"
                })
            ]),
            html.Div(id="seances-liste")
        ]
    ),

    # -- Modal nouvelle seance --
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Enregistrer une seance")),
        dbc.ModalBody([
            field("Classe", dcc.Dropdown(
                id="seance-classe",
                placeholder="Selectionner une classe",
                style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
            )),
            field("Module", dcc.Dropdown(
                id="seance-module",
                placeholder="Selectionner un module",
                style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
            )),
            field("Date", dbc.Input(
                id="seance-date", type="date",
                value=date.today().strftime("%Y-%m-%d"),
                style=input_style()
            )),
            dbc.Row([
                dbc.Col(field("Heure debut", dbc.Input(
                    id="seance-debut", type="time", style=input_style()
                )), md=6),
                dbc.Col(field("Heure fin", dbc.Input(
                    id="seance-fin", type="time", style=input_style()
                )), md=6),
            ]),
            field("Theme / Contenu", dbc.Textarea(
                id="seance-theme",
                placeholder="Decrivez le contenu pedagogique de la seance...",
                rows=3,
                style={**input_style(), "resize": "none"}
            )),

            # -- Appel numerique --
            html.Div(style={
                "borderTop": "1px solid #e5e7eb",
                "marginTop": "8px", "paddingTop": "16px"
            }, children=[
                html.H6("Appel numerique", style={
                    "fontFamily": "'Montserrat', sans-serif",
                    "fontWeight": "700", "color": BLEU,
                    "marginBottom": "4px"
                }),
                html.P(
                    "Cochez les etudiants ABSENTS lors de cette seance.",
                    style={
                        "color": "#6b7280", "fontSize": "0.78rem",
                        "fontFamily": "'Inter', sans-serif", "marginBottom": "12px"
                    }
                ),
                html.Div(id="seance-liste-appel")
            ]),

            html.Div(id="seance-feedback", style={
                "color": "#ef4444", "fontSize": "0.8rem", "marginTop": "8px"
            })
        ]),
        dbc.ModalFooter([
            btn_primary("Enregistrer la seance", "btn-save-seance", BLEU),
            btn_outline("Annuler", "btn-cancel-seance")
        ])
    ], id="modal-seance", is_open=False, size="lg"),

    # -- Modal detail seance --
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Detail de la seance")),
        dbc.ModalBody(id="modal-detail-body"),
        dbc.ModalFooter(
            btn_outline("Fermer", "btn-close-detail")
        )
    ], id="modal-detail", is_open=False, size="lg"),

    html.Div(id="seances-dummy", style={"display": "none"})
])


# ============================================================
#  CALLBACKS
# ============================================================

@callback(
    Output("seances-filtre-classe", "options"),
    Output("seances-filtre-classe", "value"),
    Output("seance-classe",         "options"),
    Output("seance-classe",         "value"),
    Input("session-store", "data")
)
def load_classes(session):
    if not session:
        return [], None, [], None
    role    = session.get("role", "")
    user_id = session.get("user_id")
    opts    = get_classes_for_user(role, user_id)
    default = get_default_classe_id(role, user_id)
    return opts, default, opts, default


@callback(
    Output("seances-filtre-module", "options"),
    Input("seances-filtre-classe",  "value")
)
def load_modules_filtre(classe_id):
    if not classe_id:
        return []
    return get_modules_by_classe(classe_id)


@callback(
    Output("seance-module", "options"),
    Input("seance-classe",  "value")
)
def load_modules_form(classe_id):
    if not classe_id:
        return []
    return get_modules_by_classe(classe_id)


@callback(
    Output("seance-liste-appel", "children"),
    Input("seance-classe", "value")
)
def load_appel(classe_id):
    if not classe_id:
        return html.P("Selectionnez une classe pour charger l'appel.", style={
            "color": "#9ca3af", "fontFamily": "'Inter', sans-serif", "fontSize": "0.82rem"
        })
    etudiants = get_etudiants_by_classe(classe_id)
    if not etudiants:
        return html.P("Aucun etudiant dans cette classe.", style={
            "color": "#9ca3af", "fontFamily": "'Inter', sans-serif", "fontSize": "0.82rem"
        })
    return html.Div([
        # En-tete appel
        html.Div(style={
            "display": "grid",
            "gridTemplateColumns": "1fr auto",
            "padding": "6px 12px",
            "background": "#f9fafb",
            "borderRadius": "6px",
            "marginBottom": "6px",
            "fontSize": "0.72rem",
            "fontWeight": "700",
            "color": "#6b7280",
            "fontFamily": "'Inter', sans-serif",
            "textTransform": "uppercase",
            "letterSpacing": "0.5px"
        }, children=[
            html.Span("Etudiant"),
            html.Span("Absent", style={"textAlign": "center"})
        ]),
        # Liste etudiants
        html.Div([
            html.Div(
                style={
                    "display": "grid",
                    "gridTemplateColumns": "1fr auto",
                    "alignItems": "center",
                    "padding": "8px 12px",
                    "borderRadius": "6px",
                    "border": "1px solid #f3f4f6",
                    "marginBottom": "4px",
                    "background": "#ffffff"
                },
                children=[
                    html.Div([
                        html.Span(f"{e['prenom']} {e['nom']}", style={
                            "fontWeight": "500", "fontSize": "0.85rem",
                            "color": "#111827", "fontFamily": "'Inter', sans-serif"
                        }),
                        html.Span(f"  {e['matricule']}", style={
                            "color": "#9ca3af", "fontSize": "0.72rem",
                            "fontFamily": "'Inter', sans-serif"
                        })
                    ]),
                    dbc.Checkbox(
                        id={"type": "absent-check", "index": e["id"]},
                        value=False,
                        style={"cursor": "pointer"}
                    )
                ]
            )
            for e in etudiants
        ])
    ])


@callback(
    Output("seances-liste",    "children"),
    Output("seances-nb-total", "children"),
    Input("seances-filtre-classe", "value"),
    Input("seances-filtre-module", "value"),
    Input("seances-refresh",       "data")
)
def afficher_seances(classe_id, module_id, _):
    seances = get_seances(classe_id, module_id)
    if not seances:
        return html.P("Aucune seance enregistree.", style={
            "color": "#9ca3af", "fontFamily": "'Inter', sans-serif",
            "fontSize": "0.875rem", "textAlign": "center", "padding": "20px"
        }), "0"

    items = []
    for s in seances:
        items.append(
            html.Div(
                style={
                    "display": "grid",
                    "gridTemplateColumns": "100px 1fr 120px 140px auto",
                    "alignItems": "center",
                    "gap": "12px",
                    "padding": "12px 16px",
                    "borderRadius": "8px",
                    "border": "1px solid #e5e7eb",
                    "marginBottom": "8px",
                    "background": "#fafafa",
                    "cursor": "pointer"
                },
                children=[
                    # Date
                    html.Div([
                        html.Div(s["date"].split("/")[0], style={
                            "fontSize": "1.4rem", "fontWeight": "800",
                            "color": BLEU, "fontFamily": "'Montserrat', sans-serif",
                            "lineHeight": "1"
                        }),
                        html.Div(f"{s['date'].split('/')[1]}/{s['date'].split('/')[2]}", style={
                            "fontSize": "0.72rem", "color": "#9ca3af",
                            "fontFamily": "'Inter', sans-serif"
                        })
                    ], style={"textAlign": "center"}),

                    # Module + theme
                    html.Div([
                        html.Div([
                            html.Span(s["code"], style={
                                "background": f"{BLEU}12", "color": BLEU,
                                "padding": "1px 6px", "borderRadius": "4px",
                                "fontSize": "0.68rem", "fontWeight": "700",
                                "fontFamily": "'Montserrat', sans-serif",
                                "marginRight": "6px"
                            }),
                            html.Span(s["module"], style={
                                "fontWeight": "600", "color": "#111827",
                                "fontSize": "0.85rem", "fontFamily": "'Inter', sans-serif"
                            })
                        ]),
                        html.P(s["theme"][:60] + "..." if len(s["theme"]) > 60 else s["theme"],
                               style={
                                   "color": "#6b7280", "fontSize": "0.75rem",
                                   "fontFamily": "'Inter', sans-serif",
                                   "margin": "3px 0 0"
                               })
                    ]),

                    # Horaire
                    html.Div([
                        html.Span("schedule", className="material-symbols-outlined",
                                  style={"fontSize": "14px", "verticalAlign": "middle",
                                         "color": "#9ca3af", "marginRight": "4px"}),
                        html.Span(f"{s['debut']} - {s['fin']}", style={
                            "fontSize": "0.78rem", "color": "#6b7280",
                            "fontFamily": "'Inter', sans-serif"
                        })
                    ], style={"display": "flex", "alignItems": "center"}),

                    # Presences
                    badge_absent(s["nb_absents"], s["nb_total"]),

                    # Bouton detail
                    html.Button(
                        html.Span("visibility", className="material-symbols-outlined",
                                  style={"fontSize": "18px", "color": "#6b7280"}),
                        id={"type": "btn-detail-seance", "index": s["id"]},
                        n_clicks=0,
                        style={
                            "background": "transparent", "border": "1px solid #e5e7eb",
                            "borderRadius": "6px", "padding": "4px 8px", "cursor": "pointer"
                        }
                    )
                ]
            )
        )
    return html.Div(items), str(len(seances))


# -- Modals --
@callback(
    Output("modal-seance", "is_open"),
    Input("btn-open-seance",   "n_clicks"),
    Input("btn-cancel-seance", "n_clicks"),
    Input("btn-save-seance",   "n_clicks"),
    prevent_initial_call=True
)
def toggle_modal_seance(o, c, s):
    return ctx.triggered_id == "btn-open-seance"


@callback(
    Output("seance-feedback",  "children"),
    Output("seances-refresh",  "data"),
    Output("modal-seance",     "is_open", allow_duplicate=True),
    Input("btn-save-seance",   "n_clicks"),
    State("seance-classe",     "value"),
    State("seance-module",     "value"),
    State("seance-date",       "value"),
    State("seance-debut",      "value"),
    State("seance-fin",        "value"),
    State("seance-theme",      "value"),
    State({"type": "absent-check", "index": ALL}, "value"),
    State({"type": "absent-check", "index": ALL}, "id"),
    State("session-store",     "data"),
    prevent_initial_call=True
)
def save_seance(n, classe_id, module_id, date_val, debut, fin, theme,
                absents_vals, absents_ids, session):
    if not all([classe_id, module_id, date_val, debut, fin]):
        return "Les champs classe, module, date et horaires sont obligatoires.", None, True

    db = SessionLocal()
    try:
        from datetime import datetime, time as dtime
        h_debut = dtime(*map(int, debut.split(":")))
        h_fin   = dtime(*map(int, fin.split(":")))
        date_obj = datetime.strptime(date_val, "%Y-%m-%d").date()

        seance = Seance(
            module_id=module_id,
            date=date_obj,
            heure_debut=h_debut,
            heure_fin=h_fin,
            theme=theme or "",
            created_by=session.get("user_id")
        )
        db.add(seance)
        db.flush()

        # Enregistrer les presences
        etudiants = db.query(Etudiant).filter(Etudiant.classe_id == classe_id).all()
        absents_set = {
            aid["index"]
            for val, aid in zip(absents_vals, absents_ids) if val
        }
        for e in etudiants:
            db.add(Presence(
                seance_id=seance.id,
                etudiant_id=e.id,
                present=(e.id not in absents_set)
            ))

        db.commit()
        return "", True, False
    except Exception as ex:
        db.rollback()
        return f"Erreur : {str(ex)}", None, True
    finally:
        db.close()


@callback(
    Output("modal-detail",      "is_open"),
    Output("modal-detail-body", "children"),
    Input({"type": "btn-detail-seance", "index": ALL}, "n_clicks"),
    Input("btn-close-detail", "n_clicks"),
    prevent_initial_call=True
)
def show_detail(n_clicks_list, close):
    if ctx.triggered_id == "btn-close-detail":
        return False, html.Div()
    if not any(n_clicks_list):
        return False, html.Div()

    seance_id = ctx.triggered_id["index"]
    db = SessionLocal()
    try:
        s = db.query(Seance).filter(Seance.id == seance_id).first()
        if not s:
            return False, html.Div()

        presences = db.query(Presence).filter(Presence.seance_id == seance_id).all()
        presents  = [p for p in presences if p.present]
        absents   = [p for p in presences if not p.present]

        body = html.Div([
            # Infos seance
            html.Div(style={
                "background": "#f9fafb", "borderRadius": "8px",
                "padding": "14px 16px", "marginBottom": "16px"
            }, children=[
                html.Div(style={"display": "flex", "gap": "24px", "flexWrap": "wrap"}, children=[
                    html.Div([
                        html.P("Module", style={"color": "#9ca3af", "fontSize": "0.72rem",
                               "fontFamily": "'Inter', sans-serif", "margin": "0"}),
                        html.P(s.module.libelle if s.module else "-", style={
                            "fontWeight": "600", "color": "#111827",
                            "fontSize": "0.875rem", "fontFamily": "'Inter', sans-serif", "margin": "0"
                        })
                    ]),
                    html.Div([
                        html.P("Date", style={"color": "#9ca3af", "fontSize": "0.72rem",
                               "fontFamily": "'Inter', sans-serif", "margin": "0"}),
                        html.P(s.date.strftime("%d/%m/%Y") if s.date else "-", style={
                            "fontWeight": "600", "color": "#111827",
                            "fontSize": "0.875rem", "fontFamily": "'Inter', sans-serif", "margin": "0"
                        })
                    ]),
                    html.Div([
                        html.P("Horaire", style={"color": "#9ca3af", "fontSize": "0.72rem",
                               "fontFamily": "'Inter', sans-serif", "margin": "0"}),
                        html.P(
                            f"{s.heure_debut.strftime('%H:%M')} - {s.heure_fin.strftime('%H:%M')}"
                            if s.heure_debut and s.heure_fin else "-",
                            style={
                                "fontWeight": "600", "color": "#111827",
                                "fontSize": "0.875rem", "fontFamily": "'Inter', sans-serif", "margin": "0"
                            }
                        )
                    ]),
                ])
            ]),

            # Theme
            html.Div(style={"marginBottom": "16px"}, children=[
                html.P("Contenu pedagogique", style={
                    "fontWeight": "700", "color": BLEU, "fontSize": "0.82rem",
                    "fontFamily": "'Montserrat', sans-serif", "marginBottom": "6px"
                }),
                html.P(s.theme or "Aucun theme renseigne.", style={
                    "color": "#374151", "fontSize": "0.875rem",
                    "fontFamily": "'Inter', sans-serif", "lineHeight": "1.5"
                })
            ]),

            # Absents / Presents
            dbc.Row([
                dbc.Col([
                    html.P(f"Absents ({len(absents)})", style={
                        "fontWeight": "700", "color": "#ef4444",
                        "fontSize": "0.82rem", "fontFamily": "'Montserrat', sans-serif",
                        "marginBottom": "8px"
                    }),
                    html.Div([
                        html.Div(
                            f"{p.etudiant.user.prenom} {p.etudiant.user.nom}" if p.etudiant and p.etudiant.user else "-",
                            style={
                                "padding": "6px 10px", "borderRadius": "6px",
                                "background": "#fef2f2", "color": "#ef4444",
                                "fontSize": "0.78rem", "fontFamily": "'Inter', sans-serif",
                                "marginBottom": "4px", "fontWeight": "500"
                            }
                        ) for p in absents
                    ]) if absents else html.P("Aucun absent", style={
                        "color": "#9ca3af", "fontSize": "0.78rem",
                        "fontFamily": "'Inter', sans-serif"
                    })
                ], md=6),
                dbc.Col([
                    html.P(f"Presents ({len(presents)})", style={
                        "fontWeight": "700", "color": VERT,
                        "fontSize": "0.82rem", "fontFamily": "'Montserrat', sans-serif",
                        "marginBottom": "8px"
                    }),
                    html.Div([
                        html.Div(
                            f"{p.etudiant.user.prenom} {p.etudiant.user.nom}" if p.etudiant and p.etudiant.user else "-",
                            style={
                                "padding": "6px 10px", "borderRadius": "6px",
                                "background": "#f0fdf4", "color": VERT,
                                "fontSize": "0.78rem", "fontFamily": "'Inter', sans-serif",
                                "marginBottom": "4px", "fontWeight": "500"
                            }
                        ) for p in presents
                    ]) if presents else html.P("Aucun present", style={
                        "color": "#9ca3af", "fontSize": "0.78rem",
                        "fontFamily": "'Inter', sans-serif"
                    })
                ], md=6),
            ])
        ])
        return True, body
    finally:
        db.close()