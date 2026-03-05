# ============================================================
#  SGA ENSAE — pages/admin.py
#  Module 8 : Administration — Gestion des utilisateurs
#  Python 3.11 · Dash 2.17.0
# ============================================================

import dash
from dash import html, dcc, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc
from auth import require_auth, hash_password
from database import SessionLocal, engine
from models import (
    User, Etudiant, ResponsableClasse, ResponsableFiliere,
    Classe, Filiere, RoleEnum, MigrationLog
)
from datetime import datetime
import time

dash.register_page(__name__, path="/admin", title="SGA ENSAE — Administration")

BLEU = "#003580"
VERT = "#006B3F"
OR   = "#F5A623"


# ============================================================
#  UTILITAIRES DB
# ============================================================

def get_stats():
    db = SessionLocal()
    try:
        return {
            "nb_users"      : db.query(User).count(),
            "nb_etudiants"  : db.query(Etudiant).count(),
            "nb_resp_classe": db.query(User).filter(User.role == RoleEnum.resp_classe).count(),
            "nb_resp_fil"   : db.query(User).filter(User.role == RoleEnum.resp_filiere).count(),
            "nb_admins"     : db.query(User).filter(User.role == RoleEnum.admin).count(),
            "nb_filieres"   : db.query(Filiere).count(),
            "nb_classes"    : db.query(Classe).count(),
            "nb_migrations" : db.query(MigrationLog).count(),
        }
    finally:
        db.close()

def get_users(role_filtre=None, search=None):
    db = SessionLocal()
    try:
        q = db.query(User)
        if role_filtre and role_filtre != "tous":
            q = q.filter(User.role == role_filtre)
        if search:
            q = q.filter(
                (User.nom.ilike(f"%{search}%")) |
                (User.prenom.ilike(f"%{search}%")) |
                (User.email.ilike(f"%{search}%"))
            )
        users = q.order_by(User.role, User.nom).all()
        result = []
        for u in users:
            extra = ""
            if u.role == RoleEnum.resp_classe and u.resp_classes:
                rc    = u.resp_classes[0]
                tit   = "Titulaire" if getattr(rc, "est_titulaire", True) else "Suppleant"
                extra = f"{rc.classe.nom} ({tit})" if rc.classe else ""
            elif u.role == RoleEnum.resp_filiere and u.resp_filieres:
                extra = u.resp_filieres[0].filiere.libelle if u.resp_filieres[0].filiere else ""
            elif u.role == RoleEnum.eleve and u.etudiant:
                extra = u.etudiant.matricule or ""
            result.append({
                "id"       : u.id,
                "nom"      : u.nom,
                "prenom"   : u.prenom,
                "email"    : u.email,
                "role"     : u.role.value if u.role else "-",
                "actif"    : u.is_active,
                "extra"    : extra,
                "created"  : getattr(u, "created_at", None) and u.created_at.strftime("%d/%m/%Y") or "-",
            })
        return result
    finally:
        db.close()

def get_classes():
    db = SessionLocal()
    try:
        return [{"label": c.nom, "value": c.id} for c in db.query(Classe).all()]
    finally:
        db.close()

def get_filieres():
    db = SessionLocal()
    try:
        return [{"label": f.libelle, "value": f.id} for f in db.query(Filiere).all()]
    finally:
        db.close()

def get_migrations():
    db = SessionLocal()
    try:
        logs = db.query(MigrationLog).order_by(MigrationLog.date_import.desc()).limit(20).all()
        return [
            {
                "fichier": l.fichier,
                "date"   : l.date_import.strftime("%d/%m/%Y %H:%M") if l.date_import else "-",
                "statut" : l.statut.value if l.statut else "-",
                "details": (l.details or "")[:80] + "..." if l.details and len(l.details) > 80 else (l.details or ""),
            }
            for l in logs
        ]
    finally:
        db.close()


# ============================================================
#  COMPOSANTS UI
# ============================================================

def kpi(titre, valeur, icon_name, couleur):
    return html.Div(style={
        "background": "#ffffff", "borderRadius": "12px",
        "padding": "16px 20px", "border": "1px solid #e5e7eb",
        "display": "flex", "alignItems": "center", "gap": "14px"
    }, children=[
        html.Div(
            html.Span(icon_name, className="material-symbols-outlined",
                      style={"fontSize": "26px", "color": couleur}),
            style={
                "width": "46px", "height": "46px", "borderRadius": "10px",
                "background": f"{couleur}15", "display": "flex",
                "alignItems": "center", "justifyContent": "center", "flexShrink": "0"
            }
        ),
        html.Div([
            html.P(titre, style={
                "color": "#6b7280", "fontSize": "0.72rem", "margin": "0",
                "fontFamily": "'Inter', sans-serif", "fontWeight": "500",
                "textTransform": "uppercase", "letterSpacing": "0.4px"
            }),
            html.H4(str(valeur), style={
                "color": "#111827", "fontFamily": "'Montserrat', sans-serif",
                "fontWeight": "800", "margin": "0", "fontSize": "1.6rem"
            })
        ])
    ])

def role_badge(role):
    configs = {
        "admin"        : (BLEU,  "#dbeafe", "Admin"),
        "resp_filiere" : (VERT,  "#d1fae5", "Resp. Filiere"),
        "resp_classe"  : (OR,    "#fef3c7", "Resp. Classe"),
        "eleve"        : ("#6b7280", "#f3f4f6", "Etudiant"),
    }
    color, bg, label = configs.get(role, ("#6b7280", "#f3f4f6", role))
    return html.Span(label, style={
        "background": bg, "color": color,
        "padding": "2px 8px", "borderRadius": "999px",
        "fontSize": "0.68rem", "fontWeight": "700",
        "fontFamily": "'Inter', sans-serif"
    })

def actif_badge(actif):
    return html.Span(
        "Actif" if actif else "Inactif",
        style={
            "background": "#d1fae5" if actif else "#fee2e2",
            "color": VERT if actif else "#ef4444",
            "padding": "2px 8px", "borderRadius": "999px",
            "fontSize": "0.68rem", "fontWeight": "600",
            "fontFamily": "'Inter', sans-serif"
        }
    )

def input_style():
    return {
        "borderRadius": "8px", "border": "1.5px solid #d1d5db",
        "fontSize": "0.875rem", "fontFamily": "'Inter', sans-serif"
    }

def label_style():
    return {
        "fontWeight": "600", "fontSize": "0.82rem", "color": "#374151",
        "marginBottom": "6px", "display": "block", "fontFamily": "'Inter', sans-serif"
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


# ============================================================
#  LAYOUT
# ============================================================

layout = html.Div([
    dcc.Store(id="admin-refresh", data=0),
    dcc.Upload(id="admin-upload-migration", accept=".xlsx",
               children=html.Div(id="admin-upload-zone")),

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
        html.H4("Administration", style={
            "fontFamily": "'Montserrat', sans-serif",
            "fontWeight": "800", "color": BLEU, "margin": "0"
        }),
        html.P("Gestion des utilisateurs, filieres et migrations de donnees", style={
            "color": "#6b7280", "fontFamily": "'Inter', sans-serif", "margin": "4px 0 0"
        })
    ]),

    # -- KPIs --
    html.Div(id="admin-kpis", style={"marginBottom": "24px"}),

    # -- Onglets --
    dbc.Tabs([

        # ── Onglet Utilisateurs ──────────────────────────────
        dbc.Tab(label="Utilisateurs", tab_id="tab-users", children=[
            html.Div(style={"padding": "20px 0"}, children=[

                # Barre filtres + action
                html.Div(style={
                    "background": "#ffffff", "borderRadius": "12px",
                    "padding": "14px 20px", "border": "1px solid #e5e7eb",
                    "marginBottom": "16px", "display": "flex",
                    "alignItems": "center", "gap": "10px", "flexWrap": "wrap"
                }, children=[
                    html.Div(style={"minWidth": "160px"}, children=[
                        dcc.Dropdown(
                            id="admin-filtre-role",
                            placeholder="Filtrer par role...",
                            options=[
                                {"label": "Tous",             "value": "tous"},
                                {"label": "Admin",            "value": "admin"},
                                {"label": "Resp. Filiere",    "value": "resp_filiere"},
                                {"label": "Resp. Classe",     "value": "resp_classe"},
                                {"label": "Etudiant",         "value": "eleve"},
                            ],
                            value="tous",
                            style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
                        )
                    ]),
                    html.Div(style={"flex": "1", "minWidth": "200px"}, children=[
                        dbc.Input(
                            id="admin-search-user",
                            placeholder="Rechercher nom, prenom ou email...",
                            style=input_style()
                        )
                    ]),
                    html.Div(style={"display": "flex", "gap": "8px"}, children=[
                        html.Button(
                            [html.Span("person_add", className="material-symbols-outlined",
                                       style={"fontSize": "16px", "verticalAlign": "middle",
                                              "marginRight": "6px"}),
                             "Resp. Classe"],
                            id="btn-open-resp-classe", n_clicks=0,
                            style={
                                "background": OR, "color": "#ffffff", "border": "none",
                                "borderRadius": "8px", "padding": "9px 16px",
                                "fontFamily": "'Montserrat', sans-serif",
                                "fontWeight": "600", "fontSize": "0.82rem", "cursor": "pointer"
                            }
                        ),
                        html.Button(
                            [html.Span("supervisor_account", className="material-symbols-outlined",
                                       style={"fontSize": "16px", "verticalAlign": "middle",
                                              "marginRight": "6px"}),
                             "Resp. Filiere"],
                            id="btn-open-resp-filiere", n_clicks=0,
                            style={
                                "background": BLEU, "color": "#ffffff", "border": "none",
                                "borderRadius": "8px", "padding": "9px 16px",
                                "fontFamily": "'Montserrat', sans-serif",
                                "fontWeight": "600", "fontSize": "0.82rem", "cursor": "pointer"
                            }
                        ),
                    ]),
                ]),

                # Feedback
                html.Div(id="admin-user-feedback", style={"marginBottom": "12px"}),

                # Liste utilisateurs
                html.Div(style={
                    "background": "#ffffff", "borderRadius": "12px",
                    "padding": "20px", "border": "1px solid #e5e7eb"
                }, children=[
                    # En-tete tableau
                    html.Div(style={
                        "display": "grid",
                        "gridTemplateColumns": "1fr 1fr 130px 100px 80px 80px",
                        "gap": "8px", "padding": "8px 12px",
                        "background": "#f9fafb", "borderRadius": "6px",
                        "marginBottom": "8px", "fontSize": "0.7rem",
                        "fontWeight": "700", "color": "#6b7280",
                        "fontFamily": "'Inter', sans-serif",
                        "textTransform": "uppercase", "letterSpacing": "0.4px"
                    }, children=[
                        html.Span("Utilisateur"),
                        html.Span("Email"),
                        html.Span("Affectation"),
                        html.Span("Role"),
                        html.Span("Statut"),
                        html.Span("Actions"),
                    ]),
                    html.Div(id="admin-liste-users")
                ])
            ])
        ]),

        # ── Onglet Migration ─────────────────────────────────
        dbc.Tab(label="Migration de donnees", tab_id="tab-migration", children=[
            html.Div(style={"padding": "20px 0"}, children=[

                dbc.Row([
                    # Zone import
                    dbc.Col(html.Div(style={
                        "background": "#ffffff", "borderRadius": "12px",
                        "padding": "24px", "border": "1px solid #e5e7eb",
                        "height": "100%"
                    }, children=[
                        html.H6("Importer des donnees", style={
                            "fontFamily": "'Montserrat', sans-serif",
                            "fontWeight": "700", "color": BLEU, "marginBottom": "16px"
                        }),
                        html.P(
                            "Importez un fichier Excel avec les feuilles : "
                            "Filieres, Classes, Etudiants.",
                            style={"color": "#6b7280", "fontSize": "0.82rem",
                                   "fontFamily": "'Inter', sans-serif", "marginBottom": "16px"}
                        ),

                        # Bouton telecharger template
                        html.Div(style={"marginBottom": "16px"}, children=[
                            html.Button(
                                [html.Span("download", className="material-symbols-outlined",
                                           style={"fontSize": "16px", "verticalAlign": "middle",
                                                  "marginRight": "6px"}),
                                 "Telecharger le template"],
                                id="btn-download-migration-template", n_clicks=0,
                                style={
                                    "background": "#f0fdf4", "color": VERT,
                                    "border": f"1.5px solid {VERT}", "borderRadius": "8px",
                                    "padding": "8px 16px", "fontFamily": "'Inter', sans-serif",
                                    "fontWeight": "600", "fontSize": "0.82rem", "cursor": "pointer"
                                }
                            ),
                            dcc.Download(id="download-migration-template"),
                        ]),

                        # Zone upload
                        dcc.Upload(
                            id="admin-migration-upload",
                            children=html.Div(style={
                                "border": f"2px dashed {BLEU}",
                                "borderRadius": "10px", "padding": "32px",
                                "textAlign": "center", "cursor": "pointer",
                                "background": "#f8faff", "transition": "background 0.2s"
                            }, children=[
                                html.Span("upload_file", className="material-symbols-outlined",
                                          style={"fontSize": "36px", "color": BLEU,
                                                 "display": "block", "marginBottom": "8px"}),
                                html.P("Glissez votre fichier Excel ici", style={
                                    "fontWeight": "600", "color": BLEU,
                                    "fontFamily": "'Inter', sans-serif", "margin": "0"
                                }),
                                html.P("ou cliquez pour selectionner", style={
                                    "color": "#9ca3af", "fontSize": "0.78rem",
                                    "fontFamily": "'Inter', sans-serif", "margin": "4px 0 0"
                                }),
                                html.P(".xlsx uniquement", style={
                                    "color": "#d1d5db", "fontSize": "0.72rem",
                                    "fontFamily": "'Inter', sans-serif", "margin": "4px 0 0"
                                }),
                            ]),
                            accept=".xlsx",
                            max_size=10 * 1024 * 1024
                        ),
                        html.Div(id="migration-feedback", style={"marginTop": "16px"})
                    ]), md=6),

                    # Historique migrations
                    dbc.Col(html.Div(style={
                        "background": "#ffffff", "borderRadius": "12px",
                        "padding": "24px", "border": "1px solid #e5e7eb",
                        "height": "100%"
                    }, children=[
                        html.H6("Historique des imports", style={
                            "fontFamily": "'Montserrat', sans-serif",
                            "fontWeight": "700", "color": BLEU, "marginBottom": "16px"
                        }),
                        html.Div(id="migration-historique")
                    ]), md=6),
                ], className="g-3"),
            ])
        ]),

        # ── Onglet Filieres/Classes ──────────────────────────
        dbc.Tab(label="Filieres et Classes", tab_id="tab-structure", children=[
            html.Div(style={"padding": "20px 0"}, children=[
                dbc.Row([
                    # Filieres
                    dbc.Col(html.Div(style={
                        "background": "#ffffff", "borderRadius": "12px",
                        "padding": "20px", "border": "1px solid #e5e7eb",
                        "height": "100%"
                    }, children=[
                        html.Div(style={
                            "display": "flex", "justifyContent": "space-between",
                            "alignItems": "center", "marginBottom": "14px"
                        }, children=[
                            html.H6("Filieres", style={
                                "fontFamily": "'Montserrat', sans-serif",
                                "fontWeight": "700", "color": BLEU, "margin": "0"
                            }),
                            btn_primary("+ Filiere", "btn-open-filiere", BLEU)
                        ]),
                        html.Div(id="admin-liste-filieres")
                    ]), md=6),

                    # Classes
                    dbc.Col(html.Div(style={
                        "background": "#ffffff", "borderRadius": "12px",
                        "padding": "20px", "border": "1px solid #e5e7eb",
                        "height": "100%"
                    }, children=[
                        html.Div(style={
                            "display": "flex", "justifyContent": "space-between",
                            "alignItems": "center", "marginBottom": "14px"
                        }, children=[
                            html.H6("Classes", style={
                                "fontFamily": "'Montserrat', sans-serif",
                                "fontWeight": "700", "color": BLEU, "margin": "0"
                            }),
                            btn_primary("+ Classe", "btn-open-classe", VERT)
                        ]),
                        html.Div(id="admin-liste-classes")
                    ]), md=6),
                ], className="g-3")
            ])
        ]),


    ], id="admin-tabs", active_tab="tab-users"),

    # ── Modal Resp. Classe — designer depuis la liste ───────
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Designer un Responsable de Classe")),
        dbc.ModalBody([
            html.P(
                "Selectionnez la classe puis choisissez un etudiant ou enseignant "
                "deja inscrit pour le designer comme responsable.",
                style={"color": "#6b7280", "fontSize": "0.82rem",
                       "fontFamily": "'Inter', sans-serif", "marginBottom": "16px"}
            ),
            field("Classe", dcc.Dropdown(
                id="rc-classe",
                placeholder="Selectionner une classe...",
                style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
            )),
            field("Personne a designer", dcc.Dropdown(
                id="rc-personne",
                placeholder="Selectionnez d'abord une classe...",
                style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
            )),
            field("Type de delegue", dcc.RadioItems(
                id="rc-type",
                options=[
                    {"label": html.Span([
                        html.Span("star", className="material-symbols-outlined",
                                  style={"fontSize": "16px", "verticalAlign": "middle",
                                         "marginRight": "4px", "color": "#F5A623"}),
                        "Titulaire"
                     ], style={"display": "inline-flex", "alignItems": "center"}),
                     "value": "titulaire"},
                    {"label": html.Span([
                        html.Span("person", className="material-symbols-outlined",
                                  style={"fontSize": "16px", "verticalAlign": "middle",
                                         "marginRight": "4px", "color": "#6b7280"}),
                        "Suppleant(e)"
                     ], style={"display": "inline-flex", "alignItems": "center"}),
                     "value": "suppleant"},
                ],
                value="titulaire",
                inline=True,
                style={"gap": "20px", "fontFamily": "'Inter', sans-serif",
                       "fontSize": "0.875rem"}
            )),
            # Info sur les delegues actuels
            html.Div(id="rc-delegues-actuels", style={
                "background": "#f9fafb", "borderRadius": "8px",
                "padding": "10px 14px", "marginBottom": "8px",
                "border": "1px solid #e5e7eb", "fontSize": "0.78rem",
                "fontFamily": "'Inter', sans-serif", "color": "#6b7280"
            }),
            html.Div(id="rc-nouveau-container"),
            html.Div(id="rc-feedback",
                     style={"color": "#ef4444", "fontSize": "0.8rem", "marginTop": "8px"})
        ]),
        dbc.ModalFooter([
            btn_primary("Confirmer",  "btn-save-resp-classe", OR),
            btn_outline("Annuler",    "btn-cancel-resp-classe")
        ])
    ], id="modal-resp-classe", is_open=False, size="lg"),

    # ── Modal Resp. Filiere ──────────────────────────────────
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Ajouter un Responsable de Filiere")),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col(field("Nom", dbc.Input(
                    id="rf-nom", placeholder="ex: FALL",
                    style=input_style())), md=6),
                dbc.Col(field("Prenom", dbc.Input(
                    id="rf-prenom", placeholder="ex: Ibrahima",
                    style=input_style())), md=6),
            ]),
            field("Email", dbc.Input(
                id="rf-email", type="email",
                placeholder="ex: ifall@ensae.sn",
                style=input_style())),
            field("Filiere", dcc.Dropdown(
                id="rf-filiere",
                placeholder="Selectionner une filiere",
                style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
            )),
            field("Mot de passe provisoire", dbc.Input(
                id="rf-password", type="password",
                placeholder="Obligatoire pour nouveau compte, optionnel si existant",
                style=input_style())),
            html.Div(id="rf-feedback",
                     style={"color": "#ef4444", "fontSize": "0.8rem"})
        ]),
        dbc.ModalFooter([
            btn_primary("Enregistrer", "btn-save-resp-filiere", BLEU),
            btn_outline("Annuler",     "btn-cancel-resp-filiere")
        ])
    ], id="modal-resp-filiere", is_open=False, size="lg"),

    # Garde un Dropdown hidden pour compatibilite callbacks
    html.Div(dcc.Dropdown(id="user-affectation", style={"display": "none"}),
             style={"display": "none"}),
    html.Div(id="user-role",           style={"display": "none"}),
    html.Div(id="user-affectation-container", style={"display": "none"}),
    html.Div(id="admin-add-user-feedback",    style={"display": "none"}),
    html.Div(id="modal-add-user",             style={"display": "none"}),

    # ── Modal ajout filiere ──────────────────────────────────
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Ajouter une filiere")),
        dbc.ModalBody([
            field("Code", dbc.Input(id="filiere-code",
                                     placeholder="ex: ISEP", style=input_style())),
            field("Libelle", dbc.Input(id="filiere-libelle",
                                        placeholder="ex: Ingenieur Statisticien",
                                        style=input_style())),
            field("Duree (ans)", dbc.Input(id="filiere-duree", type="number",
                                            min=1, max=5, value=3, style=input_style())),
            html.Div(id="filiere-feedback",
                     style={"color": "#ef4444", "fontSize": "0.8rem"})
        ]),
        dbc.ModalFooter([
            btn_primary("Enregistrer", "btn-save-filiere", BLEU),
            btn_outline("Annuler",     "btn-cancel-filiere")
        ])
    ], id="modal-filiere", is_open=False),

    # ── Modal ajout classe ───────────────────────────────────
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Ajouter une classe")),
        dbc.ModalBody([
            field("Nom", dbc.Input(id="classe-nom",
                                    placeholder="ex: ISE Math 1", style=input_style())),
            field("Filiere", dcc.Dropdown(
                id="classe-filiere",
                placeholder="Selectionner une filiere",
                style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
            )),
            field("Niveau", dbc.Input(id="classe-niveau", type="number",
                                       min=1, max=5, value=1, style=input_style())),
            field("Annee scolaire", dbc.Input(id="classe-annee",
                                               placeholder="ex: 2024-2025",
                                               style=input_style())),
            html.Div(id="classe-feedback",
                     style={"color": "#ef4444", "fontSize": "0.8rem"})
        ]),
        dbc.ModalFooter([
            btn_primary("Enregistrer", "btn-save-classe", VERT),
            btn_outline("Annuler",     "btn-cancel-classe")
        ])
    ], id="modal-classe", is_open=False),

    html.Div(id="admin-dummy", style={"display": "none"})
])


# ============================================================
#  CALLBACKS
# ============================================================

@callback(
    Output("admin-kpis", "children"),
    Input("session-store", "data"),
    Input("admin-refresh", "data")
)
def load_kpis(session, _):
    ok, _ = require_auth(session, required_roles=["admin"])
    if not ok:
        return html.Div()
    s = get_stats()
    return dbc.Row([
        dbc.Col(kpi("Utilisateurs",      s["nb_users"],       "people",          BLEU), md=3),
        dbc.Col(kpi("Etudiants",         s["nb_etudiants"],   "school",          VERT), md=3),
        dbc.Col(kpi("Resp. Classes",     s["nb_resp_classe"], "manage_accounts", OR),   md=3),
        dbc.Col(kpi("Filieres",          s["nb_filieres"],    "account_tree",    "#8b5cf6"), md=3),
    ], className="g-3")


@callback(
    Output("admin-liste-users", "children"),
    Input("admin-filtre-role",  "value"),
    Input("admin-search-user",  "value"),
    Input("admin-refresh",      "data")
)
def afficher_users(role, search, _):
    users = get_users(role, search)
    if not users:
        return html.P("Aucun utilisateur trouve.", style={
            "color": "#9ca3af", "fontFamily": "'Inter', sans-serif",
            "fontSize": "0.875rem", "textAlign": "center", "padding": "20px"
        })

    return html.Div([
        html.Div(style={
            "display": "grid",
            "gridTemplateColumns": "1fr 1fr 130px 100px 80px 80px",
            "gap": "8px", "alignItems": "center",
            "padding": "10px 12px", "borderRadius": "8px",
            "border": "1px solid #e5e7eb", "marginBottom": "6px",
            "background": "#fafafa"
        }, children=[
            html.Div([
                html.Div(f"{u['prenom']} {u['nom']}", style={
                    "fontWeight": "600", "fontSize": "0.85rem",
                    "color": "#111827", "fontFamily": "'Inter', sans-serif"
                }),
                html.Div(f"Cree le {u['created']}", style={
                    "color": "#9ca3af", "fontSize": "0.68rem",
                    "fontFamily": "'Inter', sans-serif"
                })
            ]),
            html.Span(u["email"], style={
                "color": "#6b7280", "fontSize": "0.78rem",
                "fontFamily": "'Inter', sans-serif",
                "overflow": "hidden", "textOverflow": "ellipsis"
            }),
            html.Span(u["extra"] or "-", style={
                "color": "#374151", "fontSize": "0.78rem",
                "fontFamily": "'Inter', sans-serif"
            }),
            role_badge(u["role"]),
            actif_badge(u["actif"]),
            html.Div(style={"display": "flex", "gap": "4px"}, children=[
                html.Button(
                    html.Span("block", className="material-symbols-outlined",
                              style={"fontSize": "16px",
                                     "color": "#ef4444" if u["actif"] else VERT}),
                    id={"type": "btn-toggle-user", "index": u["id"]},
                    n_clicks=0,
                    title="Activer / Desactiver",
                    style={
                        "background": "transparent", "border": "1px solid #e5e7eb",
                        "borderRadius": "6px", "padding": "3px 6px", "cursor": "pointer"
                    }
                )
            ])
        ])
        for u in users
    ])


@callback(
    Output("admin-liste-filieres", "children"),
    Input("admin-refresh",  "data"),
    Input("admin-tabs",     "active_tab"),
)
def afficher_filieres(_, active_tab):
    if active_tab != "tab-structure":
        return dash.no_update
    db = SessionLocal()
    try:
        filieres = db.query(Filiere).all()
        if not filieres:
            return html.P("Aucune filiere.", style={
                "color": "#9ca3af", "fontFamily": "'Inter', sans-serif",
                "fontSize": "0.875rem", "textAlign": "center"
            })
        return html.Div([
            html.Div(style={
                "display": "flex", "justifyContent": "space-between",
                "alignItems": "center", "padding": "10px 14px",
                "borderRadius": "8px", "border": "1px solid #e5e7eb",
                "marginBottom": "6px", "background": "#fafafa"
            }, children=[
                html.Div([
                    html.Span(f.code, style={
                        "background": f"{BLEU}15", "color": BLEU,
                        "padding": "1px 7px", "borderRadius": "4px",
                        "fontSize": "0.7rem", "fontWeight": "700",
                        "fontFamily": "'Montserrat', sans-serif", "marginRight": "8px"
                    }),
                    html.Span(f.libelle, style={
                        "fontWeight": "600", "fontSize": "0.85rem",
                        "color": "#111827", "fontFamily": "'Inter', sans-serif"
                    })
                ]),
                html.Span(f"{f.duree_ans} an(s)", style={
                    "color": "#9ca3af", "fontSize": "0.72rem",
                    "fontFamily": "'Inter', sans-serif"
                })
            ])
            for f in filieres
        ])
    finally:
        db.close()


@callback(
    Output("admin-liste-classes", "children"),
    Input("admin-refresh",  "data"),
    Input("admin-tabs",     "active_tab"),
)
def afficher_classes(_, active_tab):
    if active_tab != "tab-structure":
        return dash.no_update
    db = SessionLocal()
    try:
        classes = db.query(Classe).order_by(Classe.nom).all()
        if not classes:
            return html.P("Aucune classe.", style={
                "color": "#9ca3af", "fontFamily": "'Inter', sans-serif",
                "fontSize": "0.875rem", "textAlign": "center"
            })
        return html.Div([
            html.Div(style={
                "display": "flex", "justifyContent": "space-between",
                "alignItems": "center", "padding": "10px 14px",
                "borderRadius": "8px", "border": "1px solid #e5e7eb",
                "marginBottom": "6px", "background": "#fafafa"
            }, children=[
                html.Div([
                    html.Span(c.nom, style={
                        "fontWeight": "600", "fontSize": "0.85rem",
                        "color": "#111827", "fontFamily": "'Inter', sans-serif"
                    }),
                    html.Span(f"  Niveau {c.niveau}", style={
                        "color": "#9ca3af", "fontSize": "0.72rem",
                        "fontFamily": "'Inter', sans-serif"
                    })
                ]),
                html.Span(c.filiere.code if c.filiere else "-", style={
                    "background": f"{VERT}15", "color": VERT,
                    "padding": "1px 7px", "borderRadius": "4px",
                    "fontSize": "0.7rem", "fontWeight": "700",
                    "fontFamily": "'Montserrat', sans-serif"
                })
            ])
            for c in classes
        ])
    finally:
        db.close()


@callback(
    Output("migration-historique", "children"),
    Input("admin-refresh",  "data"),
    Input("admin-tabs",     "active_tab"),
)
def afficher_migrations(_, active_tab):
    logs = get_migrations()
    if not logs:
        return html.P("Aucun import effectue.", style={
            "color": "#9ca3af", "fontFamily": "'Inter', sans-serif",
            "fontSize": "0.875rem", "textAlign": "center"
        })
    return html.Div([
        html.Div(style={
            "padding": "10px 14px", "borderRadius": "8px",
            "border": "1px solid #e5e7eb", "marginBottom": "6px",
            "background": "#fafafa"
        }, children=[
            html.Div(style={"display": "flex", "justifyContent": "space-between",
                            "marginBottom": "4px"}, children=[
                html.Span(l["fichier"], style={
                    "fontWeight": "600", "fontSize": "0.82rem",
                    "color": "#111827", "fontFamily": "'Inter', sans-serif"
                }),
                html.Span(l["statut"].upper(), style={
                    "background": "#d1fae5" if l["statut"] == "succes" else "#fee2e2",
                    "color": VERT if l["statut"] == "succes" else "#ef4444",
                    "padding": "1px 8px", "borderRadius": "999px",
                    "fontSize": "0.68rem", "fontWeight": "700",
                    "fontFamily": "'Inter', sans-serif"
                })
            ]),
            html.Div(style={"display": "flex", "justifyContent": "space-between"}, children=[
                html.Span(l["details"], style={
                    "color": "#6b7280", "fontSize": "0.72rem",
                    "fontFamily": "'Inter', sans-serif"
                }),
                html.Span(l["date"], style={
                    "color": "#9ca3af", "fontSize": "0.7rem",
                    "fontFamily": "'Inter', sans-serif"
                })
            ])
        ])
        for l in logs
    ])


# -- Modals Resp Classe --
@callback(
    Output("modal-resp-classe", "is_open"),
    Input("btn-open-resp-classe",   "n_clicks"),
    Input("btn-cancel-resp-classe", "n_clicks"),
    Input("btn-save-resp-classe",   "n_clicks"),
    prevent_initial_call=True
)
def toggle_modal_rc(o, c, s):
    return ctx.triggered_id == "btn-open-resp-classe"


@callback(
    Output("rc-classe",  "options"),
    Output("rf-filiere", "options"),
    Input("session-store", "data")
)
def load_dropdowns(_):
    return get_classes(), get_filieres()


@callback(
    Output("rc-personne", "options"),
    Output("rc-personne", "placeholder"),
    Input("rc-classe",    "value")
)
def load_personnes_classe(classe_id):
    if not classe_id:
        return [], "Selectionnez d abord une classe..."
    db = SessionLocal()
    try:
        # Etudiants de la classe
        etudiants = db.query(Etudiant).filter(
            Etudiant.classe_id == classe_id
        ).join(User).order_by(User.nom).all()

        # Utilisateurs deja resp_classe ou resp_filiere (enseignants/admins)
        autres = db.query(User).filter(
            User.role.in_([RoleEnum.resp_classe, RoleEnum.resp_filiere, RoleEnum.admin])
        ).order_by(User.nom).all()

        opts = []
        if etudiants:
            opts.append({"label": "── Etudiants de la classe ──", "value": "",
                         "disabled": True})
            for e in etudiants:
                if e.user:
                    opts.append({
                        "label": f"{e.user.prenom} {e.user.nom} ({e.matricule})",
                        "value": e.user_id
                    })
        if autres:
            opts.append({"label": "── Autres utilisateurs ──", "value": "",
                         "disabled": True})
            for u in autres:
                opts.append({
                    "label": f"{u.prenom} {u.nom} — {u.role.value}",
                    "value": u.id
                })

        if not opts:
            return [], "Aucune personne trouvee dans cette classe"
        return opts, "Selectionner une personne..."
    finally:
        db.close()


@callback(
    Output("rc-delegues-actuels", "children"),
    Input("rc-classe", "value"),
    Input("admin-refresh", "data")
)
def show_delegues_actuels(classe_id, _):
    if not classe_id:
        return "Selectionnez une classe pour voir les delegues actuels."
    db = SessionLocal()
    try:
        resp = db.query(ResponsableClasse).filter(
            ResponsableClasse.classe_id == classe_id
        ).all()
        if not resp:
            return html.Span("Aucun delegue designe pour cette classe.",
                             style={"color": "#9ca3af"})
        items = []
        for r in resp:
            u = r.user
            est_tit = getattr(r, "est_titulaire", True)
            label   = "Titulaire" if est_tit else "Suppleant(e)"
            color   = OR if est_tit else "#6b7280"
            icon    = "star" if est_tit else "person"
            items.append(html.Div(style={
                "display": "inline-flex", "alignItems": "center",
                "gap": "6px", "marginRight": "16px"
            }, children=[
                html.Span(icon, className="material-symbols-outlined",
                          style={"fontSize": "15px", "color": color}),
                html.Span(f"{label} : ", style={"fontWeight": "600", "color": color}),
                html.Span(f"{u.prenom} {u.nom}" if u else "?",
                          style={"color": "#374151"})
            ]))
        return html.Div(items)
    finally:
        db.close()


@callback(
    Output("rc-feedback",    "children"),
    Output("admin-refresh",  "data", allow_duplicate=True),
    Output("modal-resp-classe", "is_open", allow_duplicate=True),
    Input("btn-save-resp-classe", "n_clicks"),
    State("rc-classe",   "value"),
    State("rc-personne", "value"),
    State("rc-type",     "value"),
    prevent_initial_call=True
)
def save_resp_classe(n, classe_id, user_id, rc_type):
    est_titulaire = (rc_type == "titulaire")
    if not classe_id or not user_id:
        return "Veuillez selectionner une classe et une personne.", None, True
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return "Utilisateur introuvable.", None, True

        # Changer le role en resp_classe si necessaire
        if user.role == RoleEnum.eleve:
            user.role = RoleEnum.resp_classe

        # Supprimer l'eventuelle affectation existante du meme type pour cette classe
        old_same_type = db.query(ResponsableClasse).filter(
            ResponsableClasse.classe_id == classe_id,
            ResponsableClasse.est_titulaire == est_titulaire
        ).first()
        if old_same_type:
            # Remettre l'ancien en eleve si plus aucune affectation
            old_user = db.query(User).filter(User.id == old_same_type.user_id).first()
            db.delete(old_same_type)
            db.flush()
            if old_user:
                remaining = db.query(ResponsableClasse).filter(
                    ResponsableClasse.user_id == old_user.id
                ).count()
                if remaining == 0:
                    old_user.role = RoleEnum.eleve

        # Supprimer si cette personne etait deja resp de cette classe (autre type)
        old_person = db.query(ResponsableClasse).filter(
            ResponsableClasse.user_id == user_id,
            ResponsableClasse.classe_id == classe_id
        ).first()
        if old_person:
            db.delete(old_person)

        db.add(ResponsableClasse(
            user_id=user_id,
            classe_id=classe_id,
            est_titulaire=est_titulaire
        ))
        db.commit()
        return "", time.time(), False
    except Exception as ex:
        db.rollback()
        return f"Erreur : {str(ex)}", None, True
    finally:
        db.close()


# -- Modal Resp Filiere --
@callback(
    Output("modal-resp-filiere", "is_open"),
    Input("btn-open-resp-filiere",   "n_clicks"),
    Input("btn-cancel-resp-filiere", "n_clicks"),
    Input("btn-save-resp-filiere",   "n_clicks"),
    prevent_initial_call=True
)
def toggle_modal_rf(o, c, s):
    return ctx.triggered_id == "btn-open-resp-filiere"


@callback(
    Output("modal-filiere", "is_open"),
    Input("btn-open-filiere",  "n_clicks"),
    Input("btn-cancel-filiere","n_clicks"),
    Input("btn-save-filiere",  "n_clicks"),
    prevent_initial_call=True
)
def toggle_modal_filiere(o, c, s):
    return ctx.triggered_id == "btn-open-filiere"


@callback(
    Output("modal-classe",  "is_open"),
    Output("classe-filiere","options"),
    Input("btn-open-classe",  "n_clicks"),
    Input("btn-cancel-classe","n_clicks"),
    Input("btn-save-classe",  "n_clicks"),
    prevent_initial_call=True
)
def toggle_modal_classe(o, c, s):
    return ctx.triggered_id == "btn-open-classe", get_filieres()


@callback(
    Output("rf-feedback",        "children"),
    Output("admin-refresh",      "data", allow_duplicate=True),
    Output("modal-resp-filiere", "is_open", allow_duplicate=True),
    Input("btn-save-resp-filiere", "n_clicks"),
    State("rf-nom",      "value"),
    State("rf-prenom",   "value"),
    State("rf-email",    "value"),
    State("rf-filiere",  "value"),
    State("rf-password", "value"),
    prevent_initial_call=True
)
def save_resp_filiere(n, nom, prenom, email, filiere_id, password):
    if not all([nom, prenom, email, filiere_id]):
        return "Nom, prénom, email et filière sont obligatoires.", None, True
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.strip().lower()).first()

        if user:
            # Utilisateur existant (ex-etudiant) → on le promeut simplement
            user.role      = RoleEnum.resp_filiere
            user.is_active = True
            # Mettre a jour nom/prenom si fournis
            if nom:    user.nom    = nom.upper()
            if prenom: user.prenom = prenom
            # Changer le mot de passe seulement si fourni
            if password and len(password) >= 6:
                user.password_hash = hash_password(password)
        else:
            # Nouvel utilisateur — mot de passe obligatoire
            if not password or len(password) < 6:
                return "Mot de passe obligatoire (min. 6 caractères) pour un nouvel utilisateur.", None, True
            user = User(
                nom           = nom.upper(),
                prenom        = prenom,
                email         = email.strip().lower(),
                password_hash = hash_password(password),
                role          = RoleEnum.resp_filiere,
                is_active     = True,
            )
            db.add(user)
            db.flush()

        # Supprimer ancienne affectation filiere si existe
        old = db.query(ResponsableFiliere).filter(
            ResponsableFiliere.user_id == user.id
        ).first()
        if old:
            db.delete(old)

        db.add(ResponsableFiliere(user_id=user.id, filiere_id=filiere_id))
        db.commit()
        return "", time.time(), False
    except Exception as ex:
        db.rollback()
        return f"Erreur : {str(ex)}", None, True
    finally:
        db.close()


@callback(
    Output("filiere-feedback", "children"),
    Output("admin-refresh",    "data", allow_duplicate=True),
    Output("modal-filiere",    "is_open", allow_duplicate=True),
    Input("btn-save-filiere",  "n_clicks"),
    State("filiere-code",      "value"),
    State("filiere-libelle",   "value"),
    State("filiere-duree",     "value"),
    prevent_initial_call=True
)
def save_filiere(n, code, libelle, duree):
    if not all([code, libelle, duree]):
        return "Tous les champs sont obligatoires.", None, True
    db = SessionLocal()
    try:
        existing = db.query(Filiere).filter(Filiere.code == code.strip().upper()).first()
        if existing:
            # Mise a jour au lieu de doublon
            existing.libelle   = libelle.strip()
            existing.duree_ans = int(duree)
            db.commit()
            return "", time.time(), False
        db.add(Filiere(
            code      = code.strip().upper(),
            libelle   = libelle.strip(),
            duree_ans = int(duree)
        ))
        db.commit()
        return "", time.time(), False
    except Exception as ex:
        db.rollback()
        return f"Erreur : {str(ex)}", None, True
    finally:
        db.close()


@callback(
    Output("classe-feedback", "children"),
    Output("admin-refresh",   "data", allow_duplicate=True),
    Output("modal-classe",    "is_open", allow_duplicate=True),
    Input("btn-save-classe",  "n_clicks"),
    State("classe-nom",       "value"),
    State("classe-filiere",   "value"),
    State("classe-niveau",    "value"),
    State("classe-annee",     "value"),
    prevent_initial_call=True
)
def save_classe(n, nom, filiere_id, niveau, annee):
    if not all([nom, filiere_id, niveau, annee]):
        return "Tous les champs sont obligatoires.", None, True
    db = SessionLocal()
    try:
        existing = db.query(Classe).filter(
            Classe.nom            == nom.strip(),
            Classe.annee_scolaire == annee.strip()
        ).first()
        if existing:
            # Mise a jour au lieu de doublon
            existing.filiere_id     = filiere_id
            existing.niveau         = int(niveau)
            db.commit()
            return "", time.time(), False
        db.add(Classe(
            nom            = nom.strip(),
            filiere_id     = filiere_id,
            niveau         = int(niveau),
            annee_scolaire = annee.strip()
        ))
        db.commit()
        return "", time.time(), False
    except Exception as ex:
        db.rollback()
        return f"Erreur : {str(ex)}", None, True
    finally:
        db.close()


@callback(
    Output("admin-refresh",                "data", allow_duplicate=True),
    Input({"type": "btn-toggle-user", "index": dash.ALL}, "n_clicks"),
    prevent_initial_call=True
)
def toggle_user(n_clicks):
    if not any(n_clicks):
        return None
    user_id = ctx.triggered_id["index"]
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.id == user_id).first()
        if u:
            u.is_active = not u.is_active
            db.commit()
        return time.time()
    finally:
        db.close()


@callback(
    Output("download-migration-template", "data"),
    Input("btn-download-migration-template", "n_clicks"),
    prevent_initial_call=True
)
def download_migration_template(n):
    from utils.migration import generate_migration_template
    data = generate_migration_template()
    return dcc.send_bytes(data, "template_migration_ensae.xlsx")


@callback(
    Output("migration-feedback", "children"),
    Output("admin-refresh",      "data", allow_duplicate=True),
    Input("admin-migration-upload", "contents"),
    State("admin-migration-upload", "filename"),
    prevent_initial_call=True
)
def do_migration(contents, filename):
    if not contents:
        return html.Div(), None
    from utils.migration import migrate_from_excel
    try:
        resultats = migrate_from_excel(contents, filename or "import.xlsx")
        messages  = []
        for feuille, res in resultats.items():
            if res["nb"] > 0:
                messages.append(dbc.Alert(
                    f"{feuille} : {res['nb']} enregistrement(s) importe(s).",
                    color="success", dismissable=True,
                    style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
                ))
            if res["erreurs"]:
                messages.append(dbc.Alert(
                    [html.Strong("Avertissements : "),
                     html.Ul([html.Li(e) for e in res["erreurs"]])],
                    color="warning", dismissable=True,
                    style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.82rem"}
                ))
        return html.Div(messages), True
    except Exception as ex:
        return dbc.Alert(f"Erreur : {str(ex)}", color="danger",
                         style={"fontFamily": "'Inter', sans-serif"}), None