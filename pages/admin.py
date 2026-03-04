# ============================================================
#  SGA ENSAE — pages/admin.py
#  Module 8 : Administration — Gestion des utilisateurs
#  Python 3.11 · Dash 2.17.0
# ============================================================

import dash
from dash import html, dcc, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc
from auth import require_auth, hash_password
from database import SessionLocal
from models import (
    User, Etudiant, ResponsableClasse, ResponsableFiliere,
    Classe, Filiere, RoleEnum, MigrationLog
)
from datetime import datetime

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
                extra = u.resp_classes[0].classe.nom if u.resp_classes[0].classe else ""
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
                "created"  : u.created_at.strftime("%d/%m/%Y") if u.created_at else "-",
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
    dcc.Store(id="admin-refresh"),
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
                    btn_primary("+ Ajouter un responsable", "btn-open-add-user", BLEU),
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

    # ── Modal ajout responsable ─────────────────────────────
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Ajouter un responsable")),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col(field("Nom", dbc.Input(
                    id="user-nom", placeholder="ex: DIALLO",
                    style=input_style())), md=6),
                dbc.Col(field("Prenom", dbc.Input(
                    id="user-prenom", placeholder="ex: Mamadou",
                    style=input_style())), md=6),
            ]),
            field("Email", dbc.Input(
                id="user-email", type="email",
                placeholder="ex: mdiallo@ensae.sn",
                style=input_style())),
            field("Role", dcc.Dropdown(
                id="user-role",
                options=[
                    {"label": "Admin",            "value": "admin"},
                    {"label": "Resp. Filiere",    "value": "resp_filiere"},
                    {"label": "Resp. Classe",     "value": "resp_classe"},
                ],
                placeholder="Selectionner un role",
                style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
            )),
            html.Div(id="user-affectation-container"),
            field("Mot de passe", dbc.Input(
                id="user-password", type="password",
                placeholder="Minimum 6 caracteres",
                style=input_style())),
            html.Div(id="admin-add-user-feedback",
                     style={"color": "#ef4444", "fontSize": "0.8rem"})
        ]),
        dbc.ModalFooter([
            btn_primary("Enregistrer", "btn-save-user", BLEU),
            btn_outline("Annuler",     "btn-cancel-user")
        ])
    ], id="modal-add-user", is_open=False, size="lg"),

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
    ok, _ = require_auth(session, roles=["admin"])
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
    Input("admin-refresh", "data"),
    Input("session-store", "data")
)
def afficher_filieres(_, session):
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
                    html.Span(f["code"] if hasattr(f, "code") else f.code, style={
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
    Input("admin-refresh", "data"),
    Input("session-store", "data")
)
def afficher_classes(_, session):
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
    Input("admin-refresh", "data"),
    Input("session-store", "data")
)
def afficher_migrations(_, session):
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


# -- Modals --
@callback(
    Output("modal-add-user", "is_open"),
    Input("btn-open-add-user", "n_clicks"),
    Input("btn-cancel-user",   "n_clicks"),
    Input("btn-save-user",     "n_clicks"),
    prevent_initial_call=True
)
def toggle_modal_user(o, c, s):
    return ctx.triggered_id == "btn-open-add-user"


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
    Output("user-affectation-container", "children"),
    Input("user-role", "value")
)
def show_affectation(role):
    if role == "resp_classe":
        return field("Classe", dcc.Dropdown(
            id="user-affectation", options=get_classes(),
            placeholder="Selectionner une classe",
            style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
        ))
    elif role == "resp_filiere":
        return field("Filiere", dcc.Dropdown(
            id="user-affectation", options=get_filieres(),
            placeholder="Selectionner une filiere",
            style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
        ))
    return html.Div(dcc.Dropdown(id="user-affectation", style={"display": "none"}))


@callback(
    Output("admin-add-user-feedback", "children"),
    Output("admin-refresh",           "data"),
    Output("modal-add-user",          "is_open", allow_duplicate=True),
    Input("btn-save-user",            "n_clicks"),
    State("user-nom",        "value"),
    State("user-prenom",     "value"),
    State("user-email",      "value"),
    State("user-role",       "value"),
    State("user-affectation","value"),
    State("user-password",   "value"),
    prevent_initial_call=True
)
def save_user(n, nom, prenom, email, role, affectation, password):
    if not all([nom, prenom, email, role, password]):
        return "Tous les champs sont obligatoires.", None, True
    if len(password) < 6:
        return "Le mot de passe doit faire au moins 6 caracteres.", None, True
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first():
            return f"Email '{email}' deja utilise.", None, True
        user = User(
            nom=nom.upper(), prenom=prenom, email=email,
            password_hash=hash_password(password),
            role=RoleEnum(role), is_active=True,
            created_at=datetime.now()
        )
        db.add(user)
        db.flush()
        if role == "resp_classe" and affectation:
            db.add(ResponsableClasse(user_id=user.id, classe_id=affectation))
        elif role == "resp_filiere" and affectation:
            db.add(ResponsableFiliere(user_id=user.id, filiere_id=affectation))
        db.commit()
        return "", True, False
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
        if db.query(Filiere).filter(Filiere.code == code).first():
            return f"Code '{code}' deja utilise.", None, True
        db.add(Filiere(code=code, libelle=libelle, duree_ans=int(duree)))
        db.commit()
        return "", True, False
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
        db.add(Classe(
            nom=nom, filiere_id=filiere_id,
            niveau=int(niveau), annee_scolaire=annee
        ))
        db.commit()
        return "", True, False
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
        return True
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