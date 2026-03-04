# ============================================================
#  SGA ENSAE — pages/dashboard.py
#  Tableau de bord — vue personnalisee selon le role
#  Python 3.11 · Dash 2.17.0
# ============================================================

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
from auth import require_auth, get_user_by_id
from database import SessionLocal
from models import (
    Etudiant, Classe, Filiere, Module, Seance,
    Presence, Note, Planning, StatutPlanningEnum
)
from sqlalchemy import func

dash.register_page(__name__, path="/dashboard", title="SGA ENSAE — Tableau de bord")

BLEU  = "#003580"
VERT  = "#006B3F"
OR    = "#F5A623"
GRIS  = "#F4F6F9"


# ============================================================
#  COMPOSANTS UTILITAIRES
# ============================================================

def stat_card(titre: str, valeur, icon_name: str, couleur: str, sous_titre: str = "") -> html.Div:
    """Carte statistique sobre et professionnelle."""
    return html.Div(
        style={
            "background"   : "#ffffff",
            "borderRadius" : "12px",
            "padding"      : "20px 24px",
            "boxShadow"    : "0 1px 4px rgba(0,0,0,0.06)",
            "border"       : "1px solid #e5e7eb",
            "height"       : "100%",
        },
        children=[
            html.Div(
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "flex-start"},
                children=[
                    html.Div([
                        html.P(
                            titre,
                            style={
                                "color"        : "#6b7280",
                                "fontSize"     : "0.8rem",
                                "fontFamily"   : "'Inter', sans-serif",
                                "fontWeight"   : "500",
                                "marginBottom" : "6px",
                                "textTransform": "uppercase",
                                "letterSpacing": "0.5px",
                            }
                        ),
                        html.H3(
                            str(valeur),
                            style={
                                "color"      : "#111827",
                                "fontSize"   : "2rem",
                                "fontFamily" : "'Montserrat', sans-serif",
                                "fontWeight" : "800",
                                "margin"     : "0",
                            }
                        ),
                        html.P(
                            sous_titre,
                            style={
                                "color"     : "#9ca3af",
                                "fontSize"  : "0.75rem",
                                "fontFamily": "'Inter', sans-serif",
                                "margin"    : "4px 0 0",
                            }
                        ) if sous_titre else html.Div()
                    ]),
                    html.Div(
                        html.Span(
                            icon_name,
                            className="material-symbols-outlined",
                            style={"fontSize": "32px", "color": couleur}
                        ),
                        style={
                            "width"          : "52px",
                            "height"         : "52px",
                            "borderRadius"   : "12px",
                            "background"     : f"{couleur}18",
                            "display"        : "flex",
                            "alignItems"     : "center",
                            "justifyContent" : "center",
                        }
                    )
                ]
            )
        ]
    )


def section_title(titre: str, sous_titre: str = "") -> html.Div:
    """Titre de section."""
    return html.Div(
        style={"marginBottom": "16px"},
        children=[
            html.H5(
                titre,
                style={
                    "fontFamily" : "'Montserrat', sans-serif",
                    "fontWeight" : "700",
                    "color"      : BLEU,
                    "margin"     : "0",
                }
            ),
            html.P(
                sous_titre,
                style={
                    "color"     : "#6b7280",
                    "fontSize"  : "0.82rem",
                    "fontFamily": "'Inter', sans-serif",
                    "margin"    : "2px 0 0",
                }
            ) if sous_titre else html.Div()
        ]
    )


def planning_badge(statut: str) -> html.Span:
    """Badge de statut planning."""
    colors = {
        "brouillon" : ("#6b7280", "#f3f4f6"),
        "soumis"    : ("#003580", "#dbeafe"),
        "modifie"   : ("#d97706", "#fef3c7"),
        "valide"    : ("#006B3F", "#d1fae5"),
        "rejete"    : ("#ef4444", "#fee2e2"),
    }
    text_col, bg_col = colors.get(statut, ("#6b7280", "#f3f4f6"))
    return html.Span(
        statut.capitalize(),
        style={
            "background"   : bg_col,
            "color"        : text_col,
            "padding"      : "2px 10px",
            "borderRadius" : "999px",
            "fontSize"     : "0.72rem",
            "fontFamily"   : "'Inter', sans-serif",
            "fontWeight"   : "600",
        }
    )


# ============================================================
#  VUES PAR ROLE
# ============================================================

def vue_admin(session: dict) -> html.Div:
    """Dashboard administrateur."""
    db = SessionLocal()
    try:
        nb_etudiants  = db.query(func.count(Etudiant.id)).scalar()
        nb_classes    = db.query(func.count(Classe.id)).scalar()
        nb_filieres   = db.query(func.count(Filiere.id)).scalar()
        nb_modules    = db.query(func.count(Module.id)).scalar()
        nb_plannings  = db.query(func.count(Planning.id)).filter(
            Planning.statut == StatutPlanningEnum.soumis
        ).scalar()
    finally:
        db.close()

    return html.Div([
        # -- Titre --
        html.Div(
            style={"marginBottom": "28px"},
            children=[
                html.H4(
                    f"Bonjour, {session.get('prenom')} {session.get('nom')}",
                    style={
                        "fontFamily" : "'Montserrat', sans-serif",
                        "fontWeight" : "800",
                        "color"      : BLEU,
                        "margin"     : "0",
                    }
                ),
                html.P(
                    "Vue administrateur — Tableau de bord general",
                    style={"color": "#6b7280", "fontFamily": "'Inter', sans-serif", "margin": "4px 0 0"}
                )
            ]
        ),

        # -- Statistiques --
        dbc.Row([
            dbc.Col(stat_card("Etudiants",        nb_etudiants, "school",          BLEU, "Total inscrits"),        md=3),
            dbc.Col(stat_card("Classes",           nb_classes,   "meeting_room",    VERT, "Toutes filieres"),       md=3),
            dbc.Col(stat_card("Filieres",          nb_filieres,  "account_tree",    OR,   "ISEP, ISE, AS, Masters"),md=3),
            dbc.Col(stat_card("Modules",           nb_modules,   "menu_book",       "#8b5cf6", "Total cours"),      md=3),
        ], className="g-3 mb-4"),

        # -- Alertes plannings en attente --
        html.Div([
            section_title("Plannings en attente de validation", f"{nb_plannings} planning(s) soumis"),
            html.Div(
                dbc.Alert(
                    f"{nb_plannings} planning(s) en attente de validation.",
                    color="warning",
                    style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
                ) if nb_plannings > 0 else dbc.Alert(
                    "Aucun planning en attente.",
                    color="success",
                    style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
                )
            )
        ], style={
            "background"   : "#ffffff",
            "borderRadius" : "12px",
            "padding"      : "24px",
            "boxShadow"    : "0 2px 12px rgba(0,0,0,0.07)",
            "marginBottom" : "24px",
        }),

        # -- Acces rapides --
        html.Div([
            section_title("Acces rapides"),
            dbc.Row([
                dbc.Col(acces_rapide("Gerer les utilisateurs", "manage_accounts", "/admin",        BLEU), md=3),
                dbc.Col(acces_rapide("Gerer les cours",        "menu_book",       "/cours",        VERT), md=3),
                dbc.Col(acces_rapide("Voir les etudiants",     "school",          "/etudiants",    OR),   md=3),
                dbc.Col(acces_rapide("Statistiques",           "bar_chart",       "/statistiques", "#8b5cf6"), md=3),
            ], className="g-3")
        ], style={
            "background"   : "#ffffff",
            "borderRadius" : "12px",
            "padding"      : "24px",
            "boxShadow"    : "0 2px 12px rgba(0,0,0,0.07)",
        }),
    ])


def vue_resp_filiere(session: dict) -> html.Div:
    """Dashboard responsable de filiere."""
    db = SessionLocal()
    try:
        nb_etudiants = db.query(func.count(Etudiant.id)).scalar()
        nb_modules   = db.query(func.count(Module.id)).scalar()
        nb_plannings = db.query(func.count(Planning.id)).filter(
            Planning.statut == StatutPlanningEnum.soumis
        ).scalar()
    finally:
        db.close()

    return html.Div([
        html.Div(
            style={"marginBottom": "28px"},
            children=[
                html.H4(
                    f"Bonjour, {session.get('prenom')} {session.get('nom')}",
                    style={"fontFamily": "'Montserrat', sans-serif", "fontWeight": "800", "color": BLEU, "margin": "0"}
                ),
                html.P(
                    "Vue responsable de filiere",
                    style={"color": "#6b7280", "fontFamily": "'Inter', sans-serif", "margin": "4px 0 0"}
                )
            ]
        ),

        dbc.Row([
            dbc.Col(stat_card("Etudiants",         nb_etudiants, "school",       BLEU, "Dans votre filiere"), md=4),
            dbc.Col(stat_card("Modules",            nb_modules,   "menu_book",   VERT, "Total modules"),      md=4),
            dbc.Col(stat_card("Plannings a valider",nb_plannings, "event_note",  OR,   "En attente"),         md=4),
        ], className="g-3 mb-4"),

        html.Div([
            section_title("Acces rapides"),
            dbc.Row([
                dbc.Col(acces_rapide("Valider un planning", "event_note",  "/planning",     OR),   md=3),
                dbc.Col(acces_rapide("Voir les etudiants",  "school",      "/etudiants",    BLEU), md=3),
                dbc.Col(acces_rapide("Bulletins",           "description", "/bulletins",    VERT), md=3),
                dbc.Col(acces_rapide("Statistiques",        "bar_chart",   "/statistiques", "#8b5cf6"), md=3),
            ], className="g-3")
        ], style={
            "background": "#ffffff", "borderRadius": "12px",
            "padding": "24px", "boxShadow": "0 2px 12px rgba(0,0,0,0.07)",
        }),
    ])


def vue_resp_classe(session: dict) -> html.Div:
    """Dashboard responsable de classe."""
    db = SessionLocal()
    try:
        nb_etudiants = db.query(func.count(Etudiant.id)).scalar()
        nb_seances   = db.query(func.count(Seance.id)).scalar()
        nb_modules   = db.query(func.count(Module.id)).scalar()
    finally:
        db.close()

    return html.Div([
        html.Div(
            style={"marginBottom": "28px"},
            children=[
                html.H4(
                    f"Bonjour, {session.get('prenom')} {session.get('nom')}",
                    style={"fontFamily": "'Montserrat', sans-serif", "fontWeight": "800", "color": BLEU, "margin": "0"}
                ),
                html.P(
                    "Vue responsable de classe",
                    style={"color": "#6b7280", "fontFamily": "'Inter', sans-serif", "margin": "4px 0 0"}
                )
            ]
        ),

        dbc.Row([
            dbc.Col(stat_card("Etudiants", nb_etudiants, "school",         BLEU, "Dans votre classe"), md=4),
            dbc.Col(stat_card("Seances",   nb_seances,   "calendar_today", VERT, "Enregistrees"),      md=4),
            dbc.Col(stat_card("Modules",   nb_modules,   "menu_book",      OR,   "Cette periode"),     md=4),
        ], className="g-3 mb-4"),

        html.Div([
            section_title("Acces rapides"),
            dbc.Row([
                dbc.Col(acces_rapide("Nouvelle seance",     "add_circle",   "/seances",  BLEU), md=3),
                dbc.Col(acces_rapide("Proposer un planning","event_note",   "/planning", VERT), md=3),
                dbc.Col(acces_rapide("Saisir des notes",    "edit_note",    "/etudiants",OR),   md=3),
                dbc.Col(acces_rapide("Voir les bulletins",  "description",  "/bulletins","#8b5cf6"), md=3),
            ], className="g-3")
        ], style={
            "background": "#ffffff", "borderRadius": "12px",
            "padding": "24px", "boxShadow": "0 2px 12px rgba(0,0,0,0.07)",
        }),
    ])


def vue_eleve(session: dict) -> html.Div:
    """Dashboard etudiant."""
    return html.Div([
        html.Div(
            style={"marginBottom": "28px"},
            children=[
                html.H4(
                    f"Bonjour, {session.get('prenom')} {session.get('nom')}",
                    style={"fontFamily": "'Montserrat', sans-serif", "fontWeight": "800", "color": BLEU, "margin": "0"}
                ),
                html.P(
                    "Votre espace etudiant",
                    style={"color": "#6b7280", "fontFamily": "'Inter', sans-serif", "margin": "4px 0 0"}
                )
            ]
        ),

        html.Div([
            section_title("Acces rapides"),
            dbc.Row([
                dbc.Col(acces_rapide("Mes notes",       "grade",       "/etudiants", BLEU), md=3),
                dbc.Col(acces_rapide("Mes absences",    "event_busy",  "/etudiants", VERT), md=3),
                dbc.Col(acces_rapide("Mon bulletin",    "description", "/bulletins", OR),   md=3),
                dbc.Col(acces_rapide("Mon planning",    "event_note",  "/planning",  "#8b5cf6"), md=3),
            ], className="g-3")
        ], style={
            "background": "#ffffff", "borderRadius": "12px",
            "padding": "24px", "boxShadow": "0 2px 12px rgba(0,0,0,0.07)",
        }),
    ])


def acces_rapide(label: str, icon_name: str, href: str, couleur: str) -> html.A:
    """Carte d'acces rapide cliquable."""
    return html.A(
        href=href,
        style={"textDecoration": "none"},
        children=html.Div(
            style={
                "background"   : "#ffffff",
                "border"       : f"1.5px solid {couleur}22",
                "borderRadius" : "10px",
                "padding"      : "18px",
                "textAlign"    : "center",
                "cursor"       : "pointer",
                "transition"   : "all 0.2s",
                "height"       : "100%",
            },
            children=[
                html.Div(
                    html.Span(
                        icon_name,
                        className="material-symbols-outlined",
                        style={"fontSize": "28px", "color": couleur}
                    ),
                    style={
                        "width"          : "52px",
                        "height"         : "52px",
                        "borderRadius"   : "12px",
                        "background"     : f"{couleur}15",
                        "display"        : "flex",
                        "alignItems"     : "center",
                        "justifyContent" : "center",
                        "margin"         : "0 auto 12px",
                    }
                ),
                html.P(
                    label,
                    style={
                        "color"      : "#374151",
                        "fontSize"   : "0.82rem",
                        "fontFamily" : "'Inter', sans-serif",
                        "fontWeight" : "600",
                        "margin"     : "0",
                    }
                )
            ]
        )
    )


# ============================================================
#  LAYOUT
# ============================================================

layout = html.Div(id="dashboard-content")


# ============================================================
#  CALLBACK
# ============================================================

@callback(
    Output("dashboard-content", "children"),
    Input("session-store", "data")
)
def render_dashboard(session):
    ok, redirect = require_auth(session)
    if not ok:
        return dcc.Location(pathname=redirect, id="dash-redirect")

    role = session.get("role", "")

    if role == "admin":
        return vue_admin(session)
    elif role == "resp_filiere":
        return vue_resp_filiere(session)
    elif role == "resp_classe":
        return vue_resp_classe(session)
    elif role == "eleve":
        return vue_eleve(session)
    else:
        return html.Div("Role non reconnu.")