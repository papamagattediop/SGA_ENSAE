# ============================================================
#  SGA ENSAE — pages/bulletins.py
#  Module 7 : Bulletins de notes
#  Python 3.11 · Dash 2.17.0
# ============================================================

import dash
from dash import html, dcc, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc
from auth import require_auth
from database import SessionLocal
from utils.scoped_db import resolve_scope
from models import Etudiant, User, Classe, Note, Presence, Module
from utils.access_helpers import get_classes_for_user, get_default_classe_id

dash.register_page(__name__, path="/bulletins", title="SGA ENSAE — Bulletins")

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

def get_etudiants_avec_stats(classe_id=None, classe_ids_scope=None):
    db = SessionLocal()
    try:
        q = db.query(Etudiant).join(User)
        if classe_id:
            if classe_ids_scope is not None and classe_id not in classe_ids_scope:
                return []
            q = q.filter(Etudiant.classe_id == classe_id)
        elif classe_ids_scope is not None:
            if not classe_ids_scope:
                return []
            q = q.filter(Etudiant.classe_id.in_(classe_ids_scope))
        etudiants = q.order_by(User.nom, User.prenom).all()
        result = []
        for e in etudiants:
            notes      = db.query(Note).filter(Note.etudiant_id == e.id).all()
            total_s    = db.query(Presence).filter(Presence.etudiant_id == e.id).count()
            presents   = db.query(Presence).filter(
                Presence.etudiant_id == e.id, Presence.present == True
            ).count()
            modules    = db.query(Module).filter(Module.classe_id == e.classe_id).all()

            # Moyenne ponderee par module
            total_pts  = 0
            total_coef = 0
            for m in modules:
                notes_m = [n for n in notes if n.module_id == m.id]
                note1   = next((n.note for n in notes_m if n.numero == 1), None)
                note2   = next((n.note for n in notes_m if n.numero == 2), None)
                if note1 is not None and note2 is not None:
                    moy_mod = (note1 + note2) / 2
                elif note1 is not None:
                    moy_mod = note1
                elif note2 is not None:
                    moy_mod = note2
                else:
                    moy_mod = None
                if moy_mod is not None:
                    total_pts  += moy_mod * m.coefficient
                    total_coef += m.coefficient

            moy = round(total_pts / total_coef, 2) if total_coef > 0 else None
            taux_assiduite = round((presents / total_s) * 100) if total_s > 0 else 100

            result.append({
                "id"            : e.id,
                "matricule"     : e.matricule,
                "nom"           : e.user.nom if e.user else "",
                "prenom"        : e.user.prenom if e.user else "",
                "classe"        : e.classe.nom if e.classe else "-",
                "moyenne"       : moy,
                "taux_assiduite": taux_assiduite,
                "nb_absences"   : total_s - presents,
                "mention"       : get_mention(moy),
            })

        # Classement
        result_avec_notes = [r for r in result if r["moyenne"] is not None]
        result_avec_notes.sort(key=lambda x: x["moyenne"], reverse=True)
        for rang, r in enumerate(result_avec_notes, 1):
            r["rang"] = rang
        for r in result:
            if "rang" not in r:
                r["rang"] = "-"

        return result
    finally:
        db.close()

def get_mention(moy):
    if moy is None:
        return "-"
    if moy >= 16:
        return "Tres Bien"
    if moy >= 14:
        return "Bien"
    if moy >= 12:
        return "Assez Bien"
    if moy >= 10:
        return "Passable"
    return "Insuffisant"

def get_mention_color(moy):
    if moy is None:
        return "#9ca3af"
    if moy >= 12:
        return VERT
    if moy >= 10:
        return OR
    return "#ef4444"


# ============================================================
#  COMPOSANTS UI
# ============================================================

def moy_chip(moy):
    color = get_mention_color(moy)
    return html.Span(
        f"{moy:.2f}/20" if moy is not None else "-",
        style={
            "background": f"{color}15", "color": color,
            "padding": "2px 10px", "borderRadius": "999px",
            "fontSize": "0.78rem", "fontWeight": "700",
            "fontFamily": "'Montserrat', sans-serif"
        }
    )

def taux_chip(taux):
    color = VERT if taux >= 80 else OR if taux >= 60 else "#ef4444"
    return html.Span(f"{taux}%", style={
        "background": f"{color}15", "color": color,
        "padding": "2px 8px", "borderRadius": "999px",
        "fontSize": "0.72rem", "fontWeight": "600",
        "fontFamily": "'Inter', sans-serif"
    })

def mention_chip(mention, moy):
    color = get_mention_color(moy)
    return html.Span(mention, style={
        "background": f"{color}12", "color": color,
        "padding": "2px 10px", "borderRadius": "999px",
        "fontSize": "0.72rem", "fontWeight": "600",
        "fontFamily": "'Inter', sans-serif"
    })


# ============================================================
#  LAYOUT
# ============================================================

layout = html.Div([
    dcc.Store(id="bulletins-etudiant-id"),
    dcc.Download(id="download-bulletin-pdf"),

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
        html.H4("Bulletins de Notes", style={
            "fontFamily": "'Montserrat', sans-serif",
            "fontWeight": "800", "color": BLEU, "margin": "0"
        }),
        html.P("Consultation et generation des bulletins par etudiant", style={
            "color": "#6b7280", "fontFamily": "'Inter', sans-serif", "margin": "4px 0 0"
        })
    ]),

    # -- Filtre classe --
    html.Div(style={
        "background": "#ffffff", "borderRadius": "12px",
        "padding": "16px 24px", "border": "1px solid #e5e7eb",
        "marginBottom": "20px", "display": "flex",
        "alignItems": "center", "gap": "12px", "flexWrap": "wrap"
    }, children=[
        html.Div(style={"flex": "1", "minWidth": "200px"}, children=[
            dcc.Dropdown(
                id="bulletins-filtre-classe",
                placeholder="Filtrer par classe...",
                style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
            )
        ]),
        html.Div(style={"flex": "1", "minWidth": "200px"}, children=[
            dcc.Dropdown(
                id="bulletins-filtre-periode",
                placeholder="Periode...",
                options=[
                    {"label": "2024-2025 Semestre 1", "value": "2024-2025 S1"},
                    {"label": "2024-2025 Semestre 2", "value": "2024-2025 S2"},
                    {"label": "2024-2025 Annuel",     "value": "2024-2025"},
                ],
                value="2024-2025",
                style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
            )
        ]),
    ]),

    # -- Contenu principal --
    dbc.Row(style={"alignItems": "stretch"}, children=[

        # -- Classement --
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
                    html.H6("Classement", style={
                        "fontFamily": "'Montserrat', sans-serif",
                        "fontWeight": "700", "color": BLEU, "margin": "0"
                    }),
                    html.Span(id="bulletins-nb", style={
                        "background": f"{BLEU}10", "color": BLEU,
                        "padding": "2px 10px", "borderRadius": "999px",
                        "fontSize": "0.72rem", "fontWeight": "700",
                        "fontFamily": "'Montserrat', sans-serif"
                    })
                ]),
                # En-tete tableau
                html.Div(style={
                    "display": "grid",
                    "gridTemplateColumns": "30px 1fr 80px 70px",
                    "gap": "8px", "padding": "6px 10px",
                    "background": "#f9fafb", "borderRadius": "6px",
                    "marginBottom": "6px",
                    "fontSize": "0.7rem", "fontWeight": "700",
                    "color": "#6b7280", "fontFamily": "'Inter', sans-serif",
                    "textTransform": "uppercase", "letterSpacing": "0.4px"
                }, children=[
                    html.Span("Rg"),
                    html.Span("Etudiant"),
                    html.Span("Moy.", style={"textAlign": "center"}),
                    html.Span("Assid.", style={"textAlign": "center"}),
                ]),
                html.Div(
                    id="bulletins-liste",
                    style={"flex": "1", "overflowY": "auto", "maxHeight": "520px"}
                )
            ]),
            md=5
        ),

        # -- Detail bulletin --
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
                    html.H6("Detail du bulletin", style={
                        "fontFamily": "'Montserrat', sans-serif",
                        "fontWeight": "700", "color": BLEU, "margin": "0"
                    }),
                    html.Div(id="bulletin-btn-pdf")
                ]),
                html.Div(
                    id="bulletin-detail",
                    style={"flex": "1", "overflowY": "auto", "maxHeight": "520px"}
                )
            ]),
            md=7
        )
    ], className="g-3"),
])


# ============================================================
#  CALLBACKS
# ============================================================

@callback(
    Output("bulletins-filtre-classe", "options"),
    Output("bulletins-filtre-classe", "value"),
    Input("session-store", "data")
)
def load_classes(session):
    if not session:
        return [], None
    role    = session.get("role", "")
    user_id = session.get("user_id")
    opts    = get_classes_for_user(role, user_id)
    default = get_default_classe_id(role, user_id)
    return opts, default


@callback(
    Output("bulletins-liste", "children"),
    Output("bulletins-nb",    "children"),
    Input("bulletins-filtre-classe",  "value"),
    Input("bulletins-filtre-periode", "value"),
    State("session-store",            "data")
)
def afficher_liste(classe_id, periode, session):
    role    = (session or {}).get("role", "")
    user_id = (session or {}).get("user_id")
    scope   = resolve_scope(role, user_id, None)
    etudiants = get_etudiants_avec_stats(classe_id, classe_ids_scope=scope)
    if not etudiants:
        return html.P("Aucun etudiant trouve.", style={
            "color": "#9ca3af", "fontFamily": "'Inter', sans-serif",
            "fontSize": "0.875rem", "textAlign": "center", "padding": "20px"
        }), "0"
    if role == "eleve":
        db = SessionLocal()
        etudiant = db.query(Etudiant).filter(Etudiant.user_id == user_id).first()
        db.close()
        etudiants = get_etudiants_avec_stats(None, classe_ids_scope=[etudiant.classe_id])
        etudiants = [e for e in etudiants if e["id"] == etudiant.id]

    items = []
    for e in etudiants:
        rang_display = e["rang"]
        rang_color   = OR if rang_display == 1 else BLEU if rang_display == 2 else VERT if rang_display == 3 else "#9ca3af"

        items.append(html.Div(
            id={"type": "bulletin-item", "index": e["id"]},
            style={
                "display": "grid",
                "gridTemplateColumns": "30px 1fr 80px 70px",
                "gap": "8px", "alignItems": "center",
                "padding": "10px", "borderRadius": "8px",
                "border": "1px solid #e5e7eb", "marginBottom": "6px",
                "background": "#fafafa", "cursor": "pointer",
                "transition": "border-color 0.2s"
            },
            children=[
                # Rang
                html.Div(str(rang_display), style={
                    "fontWeight": "800", "fontSize": "0.9rem",
                    "color": rang_color, "fontFamily": "'Montserrat', sans-serif",
                    "textAlign": "center"
                }),
                # Nom
                html.Div([
                    html.Div(f"{e['prenom']} {e['nom']}", style={
                        "fontWeight": "600", "fontSize": "0.85rem",
                        "color": "#111827", "fontFamily": "'Inter', sans-serif"
                    }),
                    html.Div(e["matricule"], style={
                        "color": "#9ca3af", "fontSize": "0.7rem",
                        "fontFamily": "'Inter', sans-serif"
                    })
                ]),
                # Moyenne
                html.Div(moy_chip(e["moyenne"]), style={"textAlign": "center"}),
                # Taux
                html.Div(taux_chip(e["taux_assiduite"]), style={"textAlign": "center"}),
            ]
        ))

    return html.Div(items), str(len(etudiants))


@callback(
    Output("bulletin-detail",   "children"),
    Output("bulletin-btn-pdf",  "children"),
    Output("bulletins-etudiant-id", "data"),
    Input({"type": "bulletin-item", "index": dash.ALL}, "n_clicks"),
    State("bulletins-filtre-periode", "value"),
    prevent_initial_call=True
)
def afficher_detail(n_clicks, periode):
    if not any(n_clicks):
        return html.Div(), html.Div(), None

    etudiant_id = ctx.triggered_id["index"]
    etudiants   = get_etudiants_avec_stats()
    e_data      = next((e for e in etudiants if e["id"] == etudiant_id), None)
    if not e_data:
        return html.P("Etudiant introuvable."), html.Div(), None

    # Bouton PDF
    btn_pdf = html.Button(
        [
            html.Span("picture_as_pdf", className="material-symbols-outlined",
                      style={"fontSize": "16px", "verticalAlign": "middle",
                             "marginRight": "6px"}),
            "Telecharger PDF"
        ],
        id="btn-telecharger-pdf",
        n_clicks=0,
        style={
            "background": "#fef2f2", "color": "#ef4444",
            "border": "1.5px solid #ef4444", "borderRadius": "8px",
            "padding": "7px 14px", "fontFamily": "'Inter', sans-serif",
            "fontWeight": "600", "fontSize": "0.78rem", "cursor": "pointer"
        }
    )

    # Notes detaillees
    db = SessionLocal()
    try:
        e       = db.query(Etudiant).filter(Etudiant.id == etudiant_id).first()
        modules = db.query(Module).filter(Module.classe_id == e.classe_id).all()
        notes   = db.query(Note).filter(Note.etudiant_id == etudiant_id).all()

        ues_data = {}
        for m in modules:
            notes_m = [n for n in notes if n.module_id == m.id]
            note1   = next((n.note for n in notes_m if n.numero == 1), None)
            note2   = next((n.note for n in notes_m if n.numero == 2), None)
            if note1 is not None and note2 is not None:
                moy_mod = round((note1 + note2) / 2, 2)
            elif note1 is not None:
                moy_mod = note1
            elif note2 is not None:
                moy_mod = note2
            else:
                moy_mod = None
            ue = m.ue.libelle if m.ue else "Sans UE"
            if ue not in ues_data:
                ues_data[ue] = []
            ues_data[ue].append({
                "module": m.libelle, "code": m.code,
                "coef": m.coefficient,
                "note1": note1, "note2": note2, "moy": moy_mod
            })
    finally:
        db.close()

    moy_color = get_mention_color(e_data["moyenne"])

    detail = html.Div([
        # Header etudiant
        html.Div(style={
            "background": f"{BLEU}08", "borderRadius": "10px",
            "padding": "14px 16px", "marginBottom": "16px",
            "border": f"1px solid {BLEU}20"
        }, children=[
            html.Div(style={"display": "flex", "gap": "12px", "alignItems": "center"}, children=[
                html.Div(
                    f"{e_data['prenom'][0]}{e_data['nom'][0]}",
                    style={
                        "width": "44px", "height": "44px", "borderRadius": "50%",
                        "background": BLEU, "color": "#fff",
                        "fontFamily": "'Montserrat', sans-serif", "fontWeight": "800",
                        "fontSize": "1rem", "display": "flex",
                        "alignItems": "center", "justifyContent": "center"
                    }
                ),
                html.Div([
                    html.H6(f"{e_data['prenom']} {e_data['nom']}", style={
                        "fontFamily": "'Montserrat', sans-serif", "fontWeight": "800",
                        "color": BLEU, "margin": "0"
                    }),
                    html.Span(e_data["matricule"], style={
                        "color": "#6b7280", "fontSize": "0.75rem",
                        "fontFamily": "'Inter', sans-serif"
                    })
                ])
            ]),
            html.Hr(style={"borderColor": "#e5e7eb", "margin": "10px 0"}),
            dbc.Row([
                dbc.Col([
                    html.P("Moyenne", style={"color": "#9ca3af", "fontSize": "0.68rem",
                           "fontFamily": "'Inter', sans-serif", "margin": "0",
                           "textTransform": "uppercase"}),
                    html.P(
                        f"{e_data['moyenne']:.2f}/20" if e_data["moyenne"] else "-",
                        style={"fontWeight": "800", "color": moy_color,
                               "fontSize": "1.3rem",
                               "fontFamily": "'Montserrat', sans-serif", "margin": "0"}
                    )
                ], md=3),
                dbc.Col([
                    html.P("Mention", style={"color": "#9ca3af", "fontSize": "0.68rem",
                           "fontFamily": "'Inter', sans-serif", "margin": "0",
                           "textTransform": "uppercase"}),
                    mention_chip(e_data["mention"], e_data["moyenne"])
                ], md=3),
                dbc.Col([
                    html.P("Rang", style={"color": "#9ca3af", "fontSize": "0.68rem",
                           "fontFamily": "'Inter', sans-serif", "margin": "0",
                           "textTransform": "uppercase"}),
                    html.P(str(e_data["rang"]), style={
                        "fontWeight": "800", "color": OR,
                        "fontSize": "1.3rem",
                        "fontFamily": "'Montserrat', sans-serif", "margin": "0"
                    })
                ], md=3),
                dbc.Col([
                    html.P("Assiduite", style={"color": "#9ca3af", "fontSize": "0.68rem",
                           "fontFamily": "'Inter', sans-serif", "margin": "0",
                           "textTransform": "uppercase"}),
                    html.P(f"{e_data['taux_assiduite']}%", style={
                        "fontWeight": "800",
                        "color": VERT if e_data["taux_assiduite"] >= 80 else "#ef4444",
                        "fontSize": "1.3rem",
                        "fontFamily": "'Montserrat', sans-serif", "margin": "0"
                    })
                ], md=3),
            ])
        ]),

        # Notes par UE
        html.H6("Notes par UE", style={
            "fontFamily": "'Montserrat', sans-serif", "fontWeight": "700",
            "color": BLEU, "marginBottom": "10px"
        }),

        html.Div([
            html.Div(style={"marginBottom": "12px"}, children=[
                # Titre UE
                html.Div(ue_name, style={
                    "background": f"{VERT}10", "color": VERT,
                    "padding": "5px 12px", "borderRadius": "6px",
                    "fontWeight": "700", "fontSize": "0.78rem",
                    "fontFamily": "'Montserrat', sans-serif", "marginBottom": "4px"
                }),
                # En-tete colonnes
                html.Div(style={
                    "display": "grid",
                    "gridTemplateColumns": "1fr 60px 60px 70px 90px",
                    "gap": "4px", "padding": "4px 8px",
                    "fontSize": "0.65rem", "fontWeight": "700",
                    "color": "#9ca3af", "fontFamily": "'Inter', sans-serif",
                    "textTransform": "uppercase"
                }, children=[
                    html.Span("Module"),
                    html.Span("Note 1", style={"textAlign": "center"}),
                    html.Span("Note 2", style={"textAlign": "center"}),
                    html.Span("Moyenne", style={"textAlign": "center"}),
                    html.Span("Mention",  style={"textAlign": "center"}),
                ]),
                # Lignes modules
                html.Div([
                    html.Div(style={
                        "display": "grid",
                        "gridTemplateColumns": "1fr 60px 60px 70px 90px",
                        "gap": "4px", "alignItems": "center",
                        "padding": "7px 8px", "borderRadius": "6px",
                        "border": "1px solid #f3f4f6", "marginBottom": "3px",
                        "background": "#fafafa" if i % 2 == 0 else "#ffffff"
                    }, children=[
                        html.Span(n["module"], style={
                            "fontSize": "0.82rem", "color": "#374151",
                            "fontFamily": "'Inter', sans-serif", "fontWeight": "500"
                        }),
                        html.Span(
                            f"{n['note1']:.1f}" if n["note1"] is not None else "-",
                            style={"fontSize": "0.78rem", "color": "#6b7280",
                                   "fontFamily": "'Inter', sans-serif", "textAlign": "center"}
                        ),
                        html.Span(
                            f"{n['note2']:.1f}" if n["note2"] is not None else "-",
                            style={"fontSize": "0.78rem", "color": "#6b7280",
                                   "fontFamily": "'Inter', sans-serif", "textAlign": "center"}
                        ),
                        html.Span(
                            f"{n['moy']:.2f}" if n["moy"] is not None else "-",
                            style={
                                "fontSize": "0.85rem", "fontWeight": "700",
                                "color": get_mention_color(n["moy"]),
                                "fontFamily": "'Montserrat', sans-serif",
                                "textAlign": "center"
                            }
                        ),
                        html.Div(mention_chip(get_mention(n["moy"]), n["moy"]),
                                 style={"textAlign": "center"})
                    ])
                    for i, n in enumerate(ue_mods)
                ])
            ])
            for ue_name, ue_mods in ues_data.items()
        ]) if ues_data else html.P("Aucune note enregistree.", style={
            "color": "#9ca3af", "fontFamily": "'Inter', sans-serif",
            "fontSize": "0.875rem", "textAlign": "center", "padding": "20px"
        })
    ])

    return detail, btn_pdf, etudiant_id


@callback(
    Output("download-bulletin-pdf",   "data"),
    Input("btn-telecharger-pdf",      "n_clicks"),
    State("bulletins-etudiant-id",    "data"),
    State("bulletins-filtre-periode", "value"),
    prevent_initial_call=True
)
def telecharger_pdf(n, etudiant_id, periode):
    if not etudiant_id:
        return None
    from utils.pdf_generator import generate_bulletin
    try:
        pdf_bytes = generate_bulletin(etudiant_id, periode or "2024-2025")
        db = SessionLocal()
        try:
            e = db.query(Etudiant).filter(Etudiant.id == etudiant_id).first()
            matricule = e.matricule if e else str(etudiant_id)
        finally:
            db.close()
        return dcc.send_bytes(pdf_bytes, f"bulletin_{matricule}.pdf")
    except Exception as ex:
        return None