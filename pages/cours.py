# ============================================================
#  SGA ENSAE — pages/cours.py
#  Gestion des UE et Modules — CRUD + Import Excel en masse
#  Python 3.11 · Dash 2.17.0
# ============================================================

import dash
from dash import html, dcc, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc
from auth import require_auth
from database import SessionLocal
from models import UE, Module, Classe, Periode, Seance, UEClasse
import pandas as pd
import io
import base64

dash.register_page(__name__, path="/cours", title="SGA ENSAE — Cours et UE")

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

def get_periodes():
    db = SessionLocal()
    try:
        return [{"label": p.libelle, "value": p.id} for p in db.query(Periode).all()]
    finally:
        db.close()

def get_ues(classe_id=None):
    db = SessionLocal()
    try:
        q = db.query(UE)
        if classe_id:
            q = q.join(UE.ue_classes).filter_by(classe_id=classe_id)
        return [
            {
                "id"         : u.id,
                "code"       : u.code,
                "libelle"    : u.libelle,
                "coefficient": u.coefficient,
                "periode"    : u.periode.libelle if u.periode else "-",
                "nb_modules" : len(u.modules),
            }
            for u in q.all()
        ]
    finally:
        db.close()

def get_modules(ue_id=None):
    db = SessionLocal()
    try:
        q = db.query(Module)
        if ue_id:
            q = q.filter(Module.ue_id == ue_id)
        result = []
        for m in q.all():
            seances = db.query(Seance).filter(Seance.module_id == m.id).all()
            heures_faites = sum(
                (s.heure_fin.hour * 60 + s.heure_fin.minute -
                 s.heure_debut.hour * 60 - s.heure_debut.minute) / 60
                for s in seances if s.heure_debut and s.heure_fin
            )
            pct = round((heures_faites / m.volume_horaire) * 100) if m.volume_horaire else 0
            result.append({
                "id"            : m.id,
                "code"          : m.code,
                "libelle"       : m.libelle,
                "enseignant"    : m.enseignant or "-",
                "coefficient"   : m.coefficient,
                "volume_horaire": m.volume_horaire or 0,
                "heures_faites" : round(heures_faites, 1),
                "progression"   : min(pct, 100),
            })
        return result
    finally:
        db.close()


# ============================================================
#  COMPOSANTS UI
# ============================================================

def progress_bar(pct: int) -> html.Div:
    color = VERT if pct >= 100 else OR if pct >= 60 else "#ef4444"
    return html.Div(
        style={"display": "flex", "alignItems": "center", "gap": "8px"},
        children=[
            html.Div(
                style={
                    "flex": "1", "height": "7px",
                    "background": "#e5e7eb", "borderRadius": "999px", "overflow": "hidden"
                },
                children=html.Div(style={
                    "width": f"{pct}%", "height": "100%",
                    "background": color, "borderRadius": "999px", "transition": "width 0.3s"
                })
            ),
            html.Span(f"{pct}%", style={
                "fontSize": "0.72rem", "color": color,
                "fontWeight": "600", "fontFamily": "'Inter', sans-serif", "minWidth": "34px"
            })
        ]
    )


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


# ============================================================
#  GENERATION TEMPLATE EXCEL
# ============================================================

def generate_template_excel() -> bytes:
    """
    Genere un template Excel avec deux feuilles :
    - Feuille 1 : UE  (Code_UE, Libelle_UE, Coefficient_UE, Code_Periode, Classe_ID)
    - Feuille 2 : Modules (Code_Module, Libelle_Module, Code_UE_Parent,
                           Enseignant, Coefficient_Module, Volume_Horaire_h, Classe_ID)
    """
    df_ue = pd.DataFrame(columns=[
        "Code_UE", "Libelle_UE", "Coefficient_UE", "Code_Periode", "Classe_ID"
    ])
    df_ue.loc[0] = ["UE-STAT", "Statistiques et Probabilites", 4, "Semestre 1", 1]
    df_ue.loc[1] = ["UE-ECO",  "Economie Generale",            3, "Semestre 1", 1]

    df_mod = pd.DataFrame(columns=[
        "Code_Module", "Libelle_Module", "Code_UE_Parent",
        "Enseignant", "Coefficient_Module", "Volume_Horaire_h", "Classe_ID"
    ])
    df_mod.loc[0] = ["MOD-STAT1", "Statistiques Descriptives", "UE-STAT", "Dr. Diallo",  2, 30, 1]
    df_mod.loc[1] = ["MOD-STAT2", "Probabilites",              "UE-STAT", "Dr. Ndiaye",  2, 25, 1]
    df_mod.loc[2] = ["MOD-ECO1",  "Microeconomie",             "UE-ECO",  "Dr. Ba",      3, 40, 1]

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_ue.to_excel(writer,  sheet_name="UE",      index=False)
        df_mod.to_excel(writer, sheet_name="Modules", index=False)

        # Style en-tetes
        wb = writer.book
        from openpyxl.styles import PatternFill, Font, Alignment
        header_fill_ue  = PatternFill("solid", fgColor="003580")
        header_fill_mod = PatternFill("solid", fgColor="006B3F")
        font_header     = Font(color="FFFFFF", bold=True)

        for sheet_name, fill in [("UE", header_fill_ue), ("Modules", header_fill_mod)]:
            ws = writer.sheets[sheet_name]
            for cell in ws[1]:
                cell.fill      = fill
                cell.font      = font_header
                cell.alignment = Alignment(horizontal="center")
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = 22

    buffer.seek(0)
    return buffer.read()


# ============================================================
#  IMPORT EXCEL EN MASSE
# ============================================================

def import_from_excel(contents: str) -> tuple[int, int, list]:
    """
    Importe UE et Modules depuis un fichier Excel.
    Retourne (nb_ue, nb_modules, erreurs)
    """
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    xl      = pd.ExcelFile(io.BytesIO(decoded))

    erreurs   = []
    nb_ue     = 0
    nb_modules = 0
    db        = SessionLocal()

    try:
        # -- Import UE --
        if "UE" in xl.sheet_names:
            df_ue = xl.parse("UE")
            for _, row in df_ue.iterrows():
                try:
                    code = str(row["Code_UE"]).strip()
                    if db.query(UE).filter(UE.code == code).first():
                        erreurs.append(f"UE '{code}' existe deja — ignoree.")
                        continue
                    periode = db.query(Periode).filter(
                        Periode.libelle == str(row["Code_Periode"]).strip()
                    ).first()
                    if not periode:
                        erreurs.append(f"Periode '{row['Code_Periode']}' introuvable pour UE '{code}'.")
                        continue
                    ue = UE(
                        code=code,
                        libelle=str(row["Libelle_UE"]).strip(),
                        coefficient=float(row["Coefficient_UE"]),
                        periode_id=periode.id
                    )
                    db.add(ue)
                    db.flush()
                    # Liaison classe
                    classe_id = int(row["Classe_ID"])
                    db.add(UEClasse(ue_id=ue.id, classe_id=classe_id))
                    nb_ue += 1
                except Exception as e:
                    erreurs.append(f"Erreur UE ligne {_ + 2} : {str(e)}")

        db.commit()

        # -- Import Modules --
        if "Modules" in xl.sheet_names:
            df_mod = xl.parse("Modules")
            for _, row in df_mod.iterrows():
                try:
                    code = str(row["Code_Module"]).strip()
                    if db.query(Module).filter(Module.code == code).first():
                        erreurs.append(f"Module '{code}' existe deja — ignore.")
                        continue
                    ue = db.query(UE).filter(
                        UE.code == str(row["Code_UE_Parent"]).strip()
                    ).first()
                    if not ue:
                        erreurs.append(f"UE parente '{row['Code_UE_Parent']}' introuvable pour module '{code}'.")
                        continue
                    m = Module(
                        code=code,
                        libelle=str(row["Libelle_Module"]).strip(),
                        enseignant=str(row["Enseignant"]).strip(),
                        coefficient=float(row["Coefficient_Module"]),
                        volume_horaire=int(row["Volume_Horaire_h"]),
                        ue_id=ue.id,
                        classe_id=int(row["Classe_ID"])
                    )
                    db.add(m)
                    nb_modules += 1
                except Exception as e:
                    erreurs.append(f"Erreur Module ligne {_ + 2} : {str(e)}")

        db.commit()

    except Exception as e:
        db.rollback()
        erreurs.append(f"Erreur globale : {str(e)}")
    finally:
        db.close()

    return nb_ue, nb_modules, erreurs


# ============================================================
#  LAYOUT
# ============================================================

layout = html.Div([
    dcc.Store(id="cours-ue-selectionnee"),
    dcc.Download(id="download-template-excel"),

    # -- En-tete --
    html.Div(style={"marginBottom": "24px"}, children=[
        # Fleche retour
        html.A(
            href="/dashboard",
            style={"textDecoration": "none", "display": "inline-flex", "alignItems": "center",
                   "gap": "6px", "marginBottom": "12px", "color": "#6b7280",
                   "fontFamily": "'Inter', sans-serif", "fontSize": "0.82rem",
                   "fontWeight": "500", "transition": "color 0.2s"},
            children=[
                html.Span("arrow_back", className="material-symbols-outlined",
                          style={"fontSize": "18px", "verticalAlign": "middle"}),
                "Retour au tableau de bord"
            ]
        ),
        html.H4("Cours et Unites d'Enseignement", style={
            "fontFamily": "'Montserrat', sans-serif",
            "fontWeight": "800", "color": BLEU, "margin": "0"
        }),
        html.P("Gestion des UE et des modules par classe", style={
            "color": "#6b7280", "fontFamily": "'Inter', sans-serif", "margin": "4px 0 0"
        })
    ]),

    # -- Barre d'actions globale --
    html.Div(
        style={
            "background": "#ffffff", "borderRadius": "12px",
            "padding": "16px 24px", "boxShadow": "0 2px 12px rgba(0,0,0,0.07)",
            "marginBottom": "20px", "display": "flex",
            "alignItems": "center", "gap": "12px", "flexWrap": "wrap"
        },
        children=[
            html.Div(style={"flex": "1", "minWidth": "200px"}, children=[
                dcc.Dropdown(
                    id="cours-filtre-classe",
                    placeholder="Filtrer par classe...",
                    style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
                )
            ]),
            # Boutons import/export
            html.Button(
                [
                    html.Span("download", className="material-symbols-outlined",
                              style={"fontSize": "16px", "verticalAlign": "middle", "marginRight": "6px"}),
                    "Template Excel"
                ],
                id="btn-download-template", n_clicks=0,
                style={
                    "background": "#f0fdf4", "color": VERT,
                    "border": f"1.5px solid {VERT}", "borderRadius": "8px",
                    "padding": "8px 16px", "fontFamily": "'Inter', sans-serif",
                    "fontWeight": "600", "fontSize": "0.82rem", "cursor": "pointer"
                }
            ),
            dcc.Upload(
                id="cours-upload-excel",
                children=html.Button(
                    [
                        html.Span("upload", className="material-symbols-outlined",
                                  style={"fontSize": "16px", "verticalAlign": "middle", "marginRight": "6px"}),
                        "Importer Excel"
                    ],
                    style={
                        "background": "#eff6ff", "color": BLEU,
                        "border": f"1.5px solid {BLEU}", "borderRadius": "8px",
                        "padding": "8px 16px", "fontFamily": "'Inter', sans-serif",
                        "fontWeight": "600", "fontSize": "0.82rem", "cursor": "pointer"
                    }
                ),
                accept=".xlsx"
            ),
            btn_primary("+ Ajouter UE",     "btn-open-ue",     BLEU),
            btn_primary("+ Ajouter Module", "btn-open-module", VERT),
        ]
    ),

    # -- Feedback import --
    html.Div(id="import-feedback", style={"marginBottom": "16px"}),

    # -- Colonnes UE | Modules — meme hauteur --
    dbc.Row(
        style={"alignItems": "stretch"},
        children=[
            # Colonne UE
            dbc.Col(
                html.Div(
                    style={
                        "background": "#ffffff", "borderRadius": "12px",
                        "padding": "20px", "boxShadow": "0 2px 12px rgba(0,0,0,0.07)",
                        "height": "100%", "display": "flex", "flexDirection": "column"
                    },
                    children=[
                        html.Div(style={
                            "display": "flex", "justifyContent": "space-between",
                            "alignItems": "center", "marginBottom": "14px"
                        }, children=[
                            html.H6("Unites d'Enseignement", style={
                                "fontFamily": "'Montserrat', sans-serif",
                                "fontWeight": "700", "color": BLEU, "margin": "0"
                            }),
                            html.Span(id="cours-nb-ue", style={
                                "background": f"{BLEU}15", "color": BLEU,
                                "padding": "2px 10px", "borderRadius": "999px",
                                "fontSize": "0.72rem", "fontWeight": "700",
                                "fontFamily": "'Montserrat', sans-serif"
                            })
                        ]),
                        html.Div(
                            id="cours-liste-ue",
                            style={"flex": "1", "overflowY": "auto", "maxHeight": "520px"}
                        )
                    ]
                ),
                md=5
            ),

            # Colonne Modules
            dbc.Col(
                html.Div(
                    style={
                        "background": "#ffffff", "borderRadius": "12px",
                        "padding": "20px", "boxShadow": "0 2px 12px rgba(0,0,0,0.07)",
                        "height": "100%", "display": "flex", "flexDirection": "column"
                    },
                    children=[
                        html.Div(style={
                            "display": "flex", "justifyContent": "space-between",
                            "alignItems": "center", "marginBottom": "14px"
                        }, children=[
                            html.H6("Modules", style={
                                "fontFamily": "'Montserrat', sans-serif",
                                "fontWeight": "700", "color": VERT, "margin": "0"
                            }),
                            html.Span(id="cours-nb-modules", style={
                                "background": f"{VERT}15", "color": VERT,
                                "padding": "2px 10px", "borderRadius": "999px",
                                "fontSize": "0.72rem", "fontWeight": "700",
                                "fontFamily": "'Montserrat', sans-serif"
                            })
                        ]),
                        html.P(
                            "Cliquez sur une UE pour voir ses modules",
                            id="cours-hint-modules",
                            style={
                                "color": "#9ca3af", "fontSize": "0.78rem",
                                "fontFamily": "'Inter', sans-serif", "margin": "0 0 10px"
                            }
                        ),
                        html.Div(
                            id="cours-liste-modules",
                            style={"flex": "1", "overflowY": "auto", "maxHeight": "480px"}
                        )
                    ]
                ),
                md=7
            )
        ],
        className="g-3"
    ),

    # -- Modal UE --
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Ajouter une UE")),
        dbc.ModalBody([
            field("Code UE",    dbc.Input(id="ue-code",    placeholder="ex: UE-STAT",  style=input_style())),
            field("Libelle",    dbc.Input(id="ue-libelle", placeholder="ex: Statistiques et Probabilites", style=input_style())),
            field("Periode",    dcc.Dropdown(id="ue-periode",    placeholder="Selectionner une periode",
                                             style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"})),
            field("Classe(s)",  dcc.Dropdown(id="ue-classes",    placeholder="Selectionner une ou plusieurs classes",
                                             multi=True,
                                             style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"})),
            field("Coefficient", dbc.Input(id="ue-coefficient", type="number", min=1, max=10, step=0.5, value=1, style=input_style())),
            html.Div(id="ue-feedback", style={"color": "#ef4444", "fontSize": "0.8rem"})
        ]),
        dbc.ModalFooter([
            btn_primary("Enregistrer", "btn-save-ue", BLEU),
            btn_outline("Annuler",     "btn-cancel-ue")
        ])
    ], id="modal-ue", is_open=False),

    # -- Modal Module --
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Ajouter un Module")),
        dbc.ModalBody([
            field("UE parente",  dcc.Dropdown(id="module-ue",     placeholder="Selectionner une UE",
                                              style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"})),
            field("Classe",      dcc.Dropdown(id="module-classe",  placeholder="Selectionner une classe",
                                              style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"})),
            field("Code Module", dbc.Input(id="module-code",      placeholder="ex: MOD-STAT1", style=input_style())),
            field("Libelle",     dbc.Input(id="module-libelle",   placeholder="ex: Statistiques Descriptives", style=input_style())),
            field("Enseignant",  dbc.Input(id="module-enseignant",placeholder="ex: Dr. Diallo", style=input_style())),
            field("Coefficient", dbc.Input(id="module-coefficient", type="number", min=1, max=10, step=0.5, value=1, style=input_style())),
            field("Volume horaire (h)", dbc.Input(id="module-volume", type="number", min=1, step=1, placeholder="ex: 30", style=input_style())),
            html.Div(id="module-feedback", style={"color": "#ef4444", "fontSize": "0.8rem"})
        ]),
        dbc.ModalFooter([
            btn_primary("Enregistrer", "btn-save-module", VERT),
            btn_outline("Annuler",     "btn-cancel-module")
        ])
    ], id="modal-module", is_open=False),

    html.Div(id="cours-refresh", style={"display": "none"})
])


# ============================================================
#  CALLBACKS
# ============================================================

@callback(
    Output("cours-filtre-classe", "options"),
    Output("module-classe",        "options"),
    Output("ue-classes",           "options"),
    Input("session-store", "data")
)
def load_classes(_):
    opts = get_classes()
    return opts, opts, opts


@callback(
    Output("ue-periode", "options"),
    Input("session-store", "data")
)
def load_periodes(_):
    return get_periodes()


@callback(
    Output("module-ue", "options"),
    Input("cours-filtre-classe", "value"),
    Input("cours-refresh", "children")
)
def load_ues_dropdown(classe_id, _):
    ues = get_ues(classe_id)
    return [{"label": f"{u['code']} — {u['libelle']}", "value": u["id"]} for u in ues]


@callback(
    Output("cours-liste-ue",  "children"),
    Output("cours-nb-ue",     "children"),
    Input("cours-filtre-classe", "value"),
    Input("cours-refresh",       "children")
)
def afficher_ues(classe_id, _):
    ues = get_ues(classe_id)
    if not ues:
        return html.P("Aucune UE trouvee.", style={
            "color": "#9ca3af", "fontFamily": "'Inter', sans-serif",
            "fontSize": "0.875rem", "textAlign": "center", "padding": "20px"
        }), "0"

    items = [
        html.Div(
            id={"type": "ue-item", "index": u["id"]},
            style={
                "padding": "12px 14px", "borderRadius": "8px",
                "border": "1.5px solid #e5e7eb", "marginBottom": "8px",
                "cursor": "pointer", "background": "#fafafa",
                "transition": "border-color 0.2s"
            },
            children=[
                html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"}, children=[
                    html.Div([
                        html.Span(u["code"], style={
                            "background": f"{BLEU}15", "color": BLEU,
                            "padding": "2px 7px", "borderRadius": "4px",
                            "fontSize": "0.7rem", "fontWeight": "700",
                            "fontFamily": "'Montserrat', sans-serif", "marginRight": "8px"
                        }),
                        html.Span(u["libelle"], style={
                            "fontWeight": "600", "color": "#111827",
                            "fontSize": "0.85rem", "fontFamily": "'Inter', sans-serif"
                        }),
                    ]),
                    html.Span(f"Coef. {u['coefficient']}", style={
                        "color": "#6b7280", "fontSize": "0.72rem", "fontFamily": "'Inter', sans-serif"
                    })
                ]),
                html.Div(style={"marginTop": "5px", "display": "flex", "gap": "10px"}, children=[
                    html.Span(u["periode"], style={
                        "color": "#9ca3af", "fontSize": "0.7rem", "fontFamily": "'Inter', sans-serif"
                    }),
                    html.Span(f"{u['nb_modules']} module(s)", style={
                        "color": VERT, "fontSize": "0.7rem",
                        "fontFamily": "'Inter', sans-serif", "fontWeight": "600"
                    }),
                ])
            ]
        )
        for u in ues
    ]
    return html.Div(items), str(len(ues))


@callback(
    Output("cours-liste-modules", "children"),
    Output("cours-nb-modules",    "children"),
    Output("cours-hint-modules",  "style"),
    Input("cours-ue-selectionnee", "data"),
    Input("cours-refresh",         "children")
)
def afficher_modules(ue_id, _):
    hint_visible = {"color": "#9ca3af", "fontSize": "0.78rem",
                    "fontFamily": "'Inter', sans-serif", "margin": "0 0 10px"}
    hint_hidden  = {"display": "none"}

    if not ue_id:
        return html.Div(), "0", hint_visible

    modules = get_modules(ue_id)
    if not modules:
        return html.P("Aucun module dans cette UE.", style={
            "color": "#9ca3af", "fontFamily": "'Inter', sans-serif",
            "fontSize": "0.875rem", "textAlign": "center", "padding": "20px"
        }), "0", hint_hidden

    items = [
        html.Div(
            style={
                "padding": "14px", "borderRadius": "8px",
                "border": "1.5px solid #e5e7eb", "marginBottom": "10px",
                "background": "#fafafa"
            },
            children=[
                html.Div(style={
                    "display": "flex", "justifyContent": "space-between",
                    "alignItems": "center", "marginBottom": "6px"
                }, children=[
                    html.Div([
                        html.Span(m["code"], style={
                            "background": f"{VERT}15", "color": VERT,
                            "padding": "2px 7px", "borderRadius": "4px",
                            "fontSize": "0.7rem", "fontWeight": "700",
                            "fontFamily": "'Montserrat', sans-serif", "marginRight": "8px"
                        }),
                        html.Span(m["libelle"], style={
                            "fontWeight": "600", "color": "#111827",
                            "fontSize": "0.85rem", "fontFamily": "'Inter', sans-serif"
                        }),
                    ]),
                    html.Span(f"Coef. {m['coefficient']}", style={
                        "color": "#6b7280", "fontSize": "0.72rem", "fontFamily": "'Inter', sans-serif"
                    })
                ]),
                html.Span(f"Enseignant : {m['enseignant']}  |  {m['heures_faites']}h / {m['volume_horaire']}h", style={
                    "color": "#6b7280", "fontSize": "0.75rem",
                    "fontFamily": "'Inter', sans-serif", "display": "block", "marginBottom": "8px"
                }),
                progress_bar(m["progression"])
            ]
        )
        for m in modules
    ]
    return html.Div(items), str(len(modules)), hint_hidden


# -- Modals --
@callback(
    Output("modal-ue", "is_open"),
    Input("btn-open-ue",    "n_clicks"),
    Input("btn-cancel-ue",  "n_clicks"),
    Input("btn-save-ue",    "n_clicks"),
    prevent_initial_call=True
)
def toggle_modal_ue(o, c, s):
    return ctx.triggered_id == "btn-open-ue"


@callback(
    Output("modal-module", "is_open"),
    Input("btn-open-module",   "n_clicks"),
    Input("btn-cancel-module", "n_clicks"),
    Input("btn-save-module",   "n_clicks"),
    prevent_initial_call=True
)
def toggle_modal_module(o, c, s):
    return ctx.triggered_id == "btn-open-module"


# -- Sauvegarde UE --
@callback(
    Output("ue-feedback",     "children"),
    Output("cours-refresh",   "children"),
    Output("modal-ue",        "is_open", allow_duplicate=True),
    Input("btn-save-ue",      "n_clicks"),
    State("ue-code",          "value"),
    State("ue-libelle",       "value"),
    State("ue-periode",       "value"),
    State("ue-classes",       "value"),
    State("ue-coefficient",   "value"),
    prevent_initial_call=True
)
def save_ue(n, code, libelle, periode_id, classes, coef):
    if not all([code, libelle, periode_id, classes, coef]):
        return "Tous les champs sont obligatoires.", "", True
    db = SessionLocal()
    try:
        if db.query(UE).filter(UE.code == code).first():
            return f"Le code '{code}' existe deja.", "", True
        ue = UE(code=code, libelle=libelle, periode_id=periode_id, coefficient=float(coef))
        db.add(ue)
        db.flush()
        for cid in classes:
            db.add(UEClasse(ue_id=ue.id, classe_id=cid))
        db.commit()
        return "", "refresh", False
    except Exception as e:
        db.rollback()
        return f"Erreur : {str(e)}", "", True
    finally:
        db.close()


# -- Sauvegarde Module --
@callback(
    Output("module-feedback",    "children"),
    Output("cours-refresh",      "children", allow_duplicate=True),
    Output("modal-module",       "is_open",  allow_duplicate=True),
    Input("btn-save-module",     "n_clicks"),
    State("module-ue",           "value"),
    State("module-classe",       "value"),
    State("module-code",         "value"),
    State("module-libelle",      "value"),
    State("module-enseignant",   "value"),
    State("module-coefficient",  "value"),
    State("module-volume",       "value"),
    prevent_initial_call=True
)
def save_module(n, ue_id, classe_id, code, libelle, enseignant, coef, volume):
    if not all([ue_id, classe_id, code, libelle, coef, volume]):
        return "Tous les champs obligatoires doivent etre remplis.", "", True
    db = SessionLocal()
    try:
        if db.query(Module).filter(Module.code == code).first():
            return f"Le code '{code}' existe deja.", "", True
        m = Module(
            code=code, libelle=libelle, enseignant=enseignant,
            coefficient=float(coef), volume_horaire=int(volume),
            ue_id=ue_id, classe_id=classe_id
        )
        db.add(m)
        db.commit()
        return "", "refresh", False
    except Exception as e:
        db.rollback()
        return f"Erreur : {str(e)}", "", True
    finally:
        db.close()


# -- Telechargement template Excel --
@callback(
    Output("download-template-excel", "data"),
    Input("btn-download-template",    "n_clicks"),
    prevent_initial_call=True
)
def download_template(n):
    data = generate_template_excel()
    return dcc.send_bytes(data, "template_ue_modules_ensae.xlsx")


# -- Import Excel --
@callback(
    Output("import-feedback",  "children"),
    Output("cours-refresh",    "children", allow_duplicate=True),
    Input("cours-upload-excel","contents"),
    prevent_initial_call=True
)
def import_excel(contents):
    if not contents:
        return html.Div(), ""
    try:
        nb_ue, nb_mod, erreurs = import_from_excel(contents)
        messages = []
        if nb_ue or nb_mod:
            messages.append(
                dbc.Alert(
                    f"{nb_ue} UE et {nb_mod} module(s) importes avec succes.",
                    color="success", dismissable=True,
                    style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
                )
            )
        if erreurs:
            messages.append(
                dbc.Alert(
                    [html.Strong("Avertissements :"), html.Ul([html.Li(e) for e in erreurs])],
                    color="warning", dismissable=True,
                    style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.82rem"}
                )
            )
        return html.Div(messages), "refresh"
    except Exception as e:
        return dbc.Alert(
            f"Erreur lors de l'import : {str(e)}",
            color="danger", dismissable=True,
            style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
        ), ""