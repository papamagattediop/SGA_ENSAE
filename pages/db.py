# ============================================================
#  SGA ENSAE — pages/db.py
#  Explorateur de base de données (admin uniquement)
#  Python 3.11 · Dash 2.17.0
# ============================================================

import time
import dash
from dash import html, dcc, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc

from database import SessionLocal, engine
from auth import require_auth

dash.register_page(__name__, path="/db", title="SGA ENSAE — Base de données")

BLEU = "#003580"
VERT = "#006B3F"
OR   = "#F5A623"


def input_style():
    return {
        "fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem",
        "border": "1px solid #e5e7eb", "borderRadius": "8px",
        "padding": "8px 12px", "width": "100%"
    }


# ============================================================
#  LAYOUT
# ============================================================

layout = html.Div(style={"padding": "24px"}, children=[

    # En-tete
    html.Div(style={"marginBottom": "24px"}, children=[
        html.A(href="/admin", style={
            "textDecoration": "none", "display": "inline-flex",
            "alignItems": "center", "gap": "6px", "marginBottom": "12px",
            "color": "#6b7280", "fontFamily": "'Inter', sans-serif",
            "fontSize": "0.82rem", "fontWeight": "500"
        }, children=[
            html.Span("arrow_back", className="material-symbols-outlined",
                      style={"fontSize": "18px"}),
            "Retour Administration"
        ]),
        html.H4("Explorateur de Base de Données", style={
            "fontFamily": "'Montserrat', sans-serif",
            "fontWeight": "800", "color": BLEU, "margin": "0"
        }),
        html.P("Consultation, modification et suppression directe des données — Administrateur uniquement",
               style={"color": "#6b7280", "fontFamily": "'Inter', sans-serif",
                      "margin": "4px 0 0", "fontSize": "0.85rem"})
    ]),

    dbc.Row([
        # Colonne gauche — liste des tables
        dbc.Col([
            html.Div(style={
                "background": "#ffffff", "borderRadius": "12px",
                "border": "1px solid #e5e7eb", "overflow": "hidden",
                "position": "sticky", "top": "20px"
            }, children=[
                html.Div(style={
                    "background": BLEU, "padding": "12px 16px",
                    "display": "flex", "alignItems": "center", "gap": "8px"
                }, children=[
                    html.Span("database", className="material-symbols-outlined",
                              style={"color": "#fff", "fontSize": "18px"}),
                    html.Span("Tables", style={
                        "color": "#fff", "fontFamily": "'Montserrat', sans-serif",
                        "fontWeight": "700", "fontSize": "0.9rem"
                    })
                ]),
                html.Div(id="db-tables-list", style={"padding": "8px"})
            ])
        ], md=3),

        # Colonne droite — contenu table
        dbc.Col([
            html.Div(style={
                "background": "#ffffff", "borderRadius": "12px",
                "border": "1px solid #e5e7eb", "overflow": "hidden"
            }, children=[
                html.Div(style={
                    "padding": "12px 16px", "borderBottom": "1px solid #e5e7eb",
                    "display": "flex", "alignItems": "center",
                    "justifyContent": "space-between", "flexWrap": "wrap", "gap": "8px"
                }, children=[
                    html.Div(style={"display": "flex", "alignItems": "center", "gap": "8px"}, children=[
                        html.Span("table", className="material-symbols-outlined",
                                  style={"color": BLEU, "fontSize": "18px"}),
                        html.Span(id="db-table-title", children="Selectionnez une table",
                                  style={"fontFamily": "'Montserrat', sans-serif",
                                         "fontWeight": "700", "fontSize": "0.9rem", "color": BLEU}),
                        html.Span(id="db-row-count", style={
                            "background": f"{BLEU}15", "color": BLEU,
                            "padding": "1px 8px", "borderRadius": "10px",
                            "fontSize": "0.72rem", "fontWeight": "600"
                        })
                    ]),
                    html.Div(style={"display": "flex", "gap": "8px", "alignItems": "center"}, children=[
                        dbc.Input(id="db-search", placeholder="Rechercher...",
                                  style={**input_style(), "width": "200px",
                                         "fontSize": "0.8rem", "padding": "6px 10px"}),
                        html.Button([
                            html.Span("refresh", className="material-symbols-outlined",
                                      style={"fontSize": "16px"})
                        ], id="btn-db-refresh", n_clicks=0, style={
                            "background": "#f3f4f6", "color": "#374151",
                            "border": "1px solid #e5e7eb", "borderRadius": "7px",
                            "padding": "6px 10px", "cursor": "pointer"
                        }),
                    ])
                ]),
                html.Div(id="db-table-content",
                         style={"overflowX": "auto", "maxHeight": "65vh", "overflowY": "auto"}),
            ])
        ], md=9),
    ], className="g-3"),

    # Stores
    dcc.Store(id="db-active-table", data=None),
    dcc.Store(id="db-edit-row",     data=None),
    dcc.Store(id="db-page-refresh", data=None),

    # Modal edition
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="db-modal-title")),
        dbc.ModalBody([
            html.Div(id="db-modal-form"),
            html.Div(id="db-modal-feedback",
                     style={"color": "#ef4444", "fontSize": "0.8rem", "marginTop": "8px"})
        ]),
        dbc.ModalFooter([
            html.Button("Enregistrer", id="btn-db-save", n_clicks=0, style={
                "background": BLEU, "color": "#fff", "border": "none",
                "borderRadius": "8px", "padding": "9px 20px",
                "fontFamily": "'Montserrat', sans-serif",
                "fontWeight": "700", "fontSize": "0.85rem", "cursor": "pointer"
            }),
            html.Button("Supprimer", id="btn-db-delete", n_clicks=0, style={
                "background": "#ef4444", "color": "#fff", "border": "none",
                "borderRadius": "8px", "padding": "9px 20px",
                "fontFamily": "'Montserrat', sans-serif",
                "fontWeight": "700", "fontSize": "0.85rem", "cursor": "pointer",
                "display": "none"
            }),
            html.Button("Annuler", id="btn-db-cancel", n_clicks=0, style={
                "background": "none", "color": "#6b7280",
                "border": "1px solid #e5e7eb", "borderRadius": "8px",
                "padding": "9px 20px", "cursor": "pointer",
                "fontFamily": "'Inter', sans-serif", "fontSize": "0.85rem"
            }),
        ])
    ], id="modal-db-edit", is_open=False, size="lg"),
])

# ============================================================
#  CALLBACKS — EXPLORATEUR BASE DE DONNÉES
# ============================================================

# Tables exposées avec leurs libellés et colonnes éditables
DB_TABLES = {
    "users"          : {"label": "Utilisateurs",       "icon": "people",         "color": BLEU},
    "etudiants"      : {"label": "Etudiants",          "icon": "school",         "color": VERT},
    "filieres"       : {"label": "Filieres",           "icon": "account_tree",   "color": "#8b5cf6"},
    "classes"        : {"label": "Classes",            "icon": "class",          "color": OR},
    "resp_classes"   : {"label": "Resp. Classes",      "icon": "manage_accounts","color": OR},
    "resp_filieres"  : {"label": "Resp. Filieres",     "icon": "supervisor_account","color": "#8b5cf6"},
    "modules"        : {"label": "Modules",            "icon": "menu_book",      "color": BLEU},
    "seances"        : {"label": "Seances",            "icon": "calendar_today", "color": VERT},
    "presences"      : {"label": "Presences",          "icon": "how_to_reg",     "color": VERT},
    "notes"          : {"label": "Notes",              "icon": "grade",          "color": OR},
    "periodes"       : {"label": "Periodes",           "icon": "date_range",     "color": BLEU},
    "ue"             : {"label": "Unites d'Ens.",      "icon": "library_books",  "color": BLEU},
    "plannings"      : {"label": "Plannings",          "icon": "event_note",     "color": "#8b5cf6"},
    "migration_logs" : {"label": "Logs Migration",     "icon": "history",        "color": "#6b7280"},
}


def get_table_rows(table_name: str, search: str = "", limit: int = 200):
    """Lit les lignes d'une table via SQLAlchemy text()."""
    from sqlalchemy import text, inspect as sa_inspect
    db = SessionLocal()
    try:
        insp    = sa_inspect(engine)
        cols    = [c["name"] for c in insp.get_columns(table_name)]
        q       = f"SELECT * FROM {table_name}"
        if search:
            conditions = " OR ".join([f"CAST({c} AS TEXT) LIKE :s" for c in cols])
            q += f" WHERE {conditions}"
        q += f" LIMIT {limit}"
        params = {"s": f"%{search}%"} if search else {}
        rows   = db.execute(text(q), params).fetchall()
        count  = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        return cols, [list(r) for r in rows], count
    finally:
        db.close()


def delete_row(table_name: str, row_id: int):
    from sqlalchemy import text
    db = SessionLocal()
    try:
        db.execute(text(f"DELETE FROM {table_name} WHERE id = :id"), {"id": row_id})
        db.commit()
        return True, ""
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()


def upsert_row(table_name: str, data: dict, row_id=None):
    from sqlalchemy import text, inspect as sa_inspect
    db = SessionLocal()
    try:
        insp     = sa_inspect(engine)
        col_defs = {c["name"]: c for c in insp.get_columns(table_name)}
        # Nettoyer les valeurs
        clean = {}
        for k, v in data.items():
            if k == "id":
                continue
            if k in col_defs:
                clean[k] = None if v == "" else v

        if row_id:
            sets   = ", ".join([f"{k} = :{k}" for k in clean])
            clean["_id"] = row_id
            db.execute(text(f"UPDATE {table_name} SET {sets} WHERE id = :_id"), clean)
        else:
            cols   = ", ".join(clean.keys())
            vals   = ", ".join([f":{k}" for k in clean.keys()])
            db.execute(text(f"INSERT INTO {table_name} ({cols}) VALUES ({vals})"), clean)
        db.commit()
        return True, ""
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()


# ── Liste des tables ─────────────────────────────────────────
@callback(
    Output("db-tables-list", "children"),
    Input("db-page-refresh", "data"),
)
def render_tables_list(_):

    items = []
    for tname, cfg in DB_TABLES.items():
        from sqlalchemy import text
        db = SessionLocal()
        try:
            count = db.execute(text(f"SELECT COUNT(*) FROM {tname}")).scalar()
        except:
            count = "?"
        finally:
            db.close()

        items.append(html.Button(
            style={
                "width": "100%", "textAlign": "left", "background": "none",
                "border": "none", "borderRadius": "8px", "padding": "9px 12px",
                "cursor": "pointer", "display": "flex", "alignItems": "center",
                "gap": "10px", "marginBottom": "2px",
                "transition": "background 0.15s",
            },
            id={"type": "btn-table", "index": tname},
            n_clicks=0,
            children=[
                html.Span(cfg["icon"], className="material-symbols-outlined",
                          style={"fontSize": "17px", "color": cfg["color"]}),
                html.Span(cfg["label"], style={
                    "fontFamily": "'Inter', sans-serif", "fontSize": "0.82rem",
                    "fontWeight": "500", "color": "#374151", "flex": "1"
                }),
                html.Span(str(count), style={
                    "background": f"{cfg['color']}18", "color": cfg["color"],
                    "padding": "1px 7px", "borderRadius": "8px",
                    "fontSize": "0.68rem", "fontWeight": "700"
                })
            ]
        ))
    return items


# ── Clic sur une table → stocker le nom ──────────────────────
@callback(
    Output("db-active-table", "data"),
    Input({"type": "btn-table", "index": dash.ALL}, "n_clicks"),
    prevent_initial_call=True
)
def select_table(n_clicks):
    if not any(n_clicks):
        return dash.no_update
    return ctx.triggered_id["index"]


# ── Afficher le contenu de la table ─────────────────────────
@callback(
    Output("db-table-content", "children"),
    Output("db-table-title",   "children"),
    Output("db-row-count",     "children"),
    Input("db-active-table",   "data"),
    Input("db-search",         "value"),
    Input("btn-db-refresh",    "n_clicks"),
    Input("db-page-refresh",     "data"),
)
def render_table(table_name, search, _, __):
    if not table_name:
        return (
            html.Div(style={"padding": "40px", "textAlign": "center"}, children=[
                html.Span("database", className="material-symbols-outlined",
                          style={"fontSize": "48px", "color": "#d1d5db"}),
                html.P("Selectionnez une table dans la liste",
                       style={"color": "#9ca3af", "fontFamily": "'Inter', sans-serif",
                              "marginTop": "8px"})
            ]),
            "Base de données", ""
        )

    cfg  = DB_TABLES.get(table_name, {"label": table_name, "color": BLEU})
    cols, rows, total = get_table_rows(table_name, search or "")

    if not rows:
        return (
            html.Div(html.P("Aucune donnee.", style={
                "color": "#9ca3af", "padding": "20px",
                "fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"
            })),
            cfg["label"],
            f"{total} ligne(s)"
        )

    # Styles tableau
    th_style = {
        "padding": "8px 12px", "fontFamily": "'Montserrat', sans-serif",
        "fontSize": "0.72rem", "fontWeight": "700", "color": "#ffffff",
        "background": cfg["color"], "whiteSpace": "nowrap",
        "position": "sticky", "top": "0", "zIndex": "1"
    }
    td_style = {
        "padding": "7px 12px", "fontFamily": "'Inter', sans-serif",
        "fontSize": "0.78rem", "color": "#374151",
        "borderBottom": "1px solid #f3f4f6", "maxWidth": "200px",
        "overflow": "hidden", "textOverflow": "ellipsis", "whiteSpace": "nowrap"
    }

    header = html.Tr([html.Th(c, style=th_style) for c in cols] +
                     [html.Th("Actions", style={**th_style, "textAlign": "center"})])

    body_rows = []
    for row in rows:
        row_id = row[0] if row else None
        cells  = [html.Td(
            str(v)[:60] + ("…" if v and len(str(v)) > 60 else "") if v is not None else html.Span(
                "null", style={"color": "#d1d5db", "fontStyle": "italic"}),
            style=td_style, title=str(v) if v is not None else ""
        ) for v in row]

        # Boutons actions
        actions = html.Td(style={**td_style, "textAlign": "center"}, children=[
            html.Button(
                html.Span("edit", className="material-symbols-outlined",
                          style={"fontSize": "15px"}),
                id={"type": "btn-db-edit",   "index": f"{table_name}:{row_id}"},
                n_clicks=0,
                style={"background": f"{BLEU}15", "border": "none", "borderRadius": "5px",
                       "padding": "3px 7px", "cursor": "pointer", "color": BLEU,
                       "marginRight": "4px"}
            ),
            html.Button(
                html.Span("delete", className="material-symbols-outlined",
                          style={"fontSize": "15px"}),
                id={"type": "btn-db-delete-row", "index": f"{table_name}:{row_id}"},
                n_clicks=0,
                style={"background": "#fef2f2", "border": "none", "borderRadius": "5px",
                       "padding": "3px 7px", "cursor": "pointer", "color": "#ef4444"}
            ),
        ])
        body_rows.append(html.Tr(cells + [actions],
                                 style={"background": "#fff" if len(body_rows) % 2 == 0
                                        else "#fafafa"}))

    table = html.Table(
        [html.Thead(header), html.Tbody(body_rows)],
        style={"width": "100%", "borderCollapse": "collapse"}
    )

    footer = html.Div(
        f"Affichage de {len(rows)} / {total} lignes" +
        (" — affinez la recherche pour voir plus" if total > 200 else ""),
        style={"padding": "8px 12px", "fontSize": "0.72rem", "color": "#9ca3af",
               "borderTop": "1px solid #f3f4f6", "fontFamily": "'Inter', sans-serif"}
    )

    return [table, footer], cfg["label"], f"{total} ligne(s)"


# ── Ouvrir modal édition ─────────────────────────────────────
@callback(
    Output("modal-db-edit",    "is_open"),
    Output("db-modal-title",   "children"),
    Output("db-modal-form",    "children"),
    Output("db-edit-row",      "data"),
    Output("btn-db-delete",    "style"),
    Input({"type": "btn-db-edit",       "index": dash.ALL}, "n_clicks"),
    Input("btn-db-cancel",     "n_clicks"),
    Input("btn-db-save",       "n_clicks"),
    prevent_initial_call=True
)
def open_edit_modal(edit_clicks, cancel, save):
    from sqlalchemy import text, inspect as sa_inspect
    triggered = ctx.triggered_id

    if triggered in ("btn-db-cancel", "btn-db-save"):
        return False, "", [], None, {"display": "none"}

    if not any(edit_clicks):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    ref        = triggered["index"]                # "table_name:row_id"
    table_name, row_id = ref.rsplit(":", 1)
    row_id     = int(row_id)

    db = SessionLocal()
    try:
        insp    = sa_inspect(engine)
        cols    = [c["name"] for c in insp.get_columns(table_name)]
        row     = db.execute(text(f"SELECT * FROM {table_name} WHERE id = :id"),
                             {"id": row_id}).fetchone()
    finally:
        db.close()

    if not row:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    row_dict = dict(zip(cols, row))
    form_fields = []
    for col, val in row_dict.items():
        form_fields.append(
            html.Div(style={"marginBottom": "12px"}, children=[
                html.Label(col, style={
                    "fontFamily": "'Inter', sans-serif", "fontSize": "0.78rem",
                    "fontWeight": "600", "color": "#374151", "marginBottom": "4px",
                    "display": "block"
                }),
                dbc.Input(
                    id={"type": "db-field", "index": col},
                    value=str(val) if val is not None else "",
                    disabled=(col == "id"),
                    style={
                        **input_style(),
                        "background": "#f9fafb" if col == "id" else "#ffffff",
                        "fontSize": "0.82rem"
                    }
                )
            ])
        )

    delete_style = {
        "background": "#ef4444", "color": "#fff", "border": "none",
        "borderRadius": "8px", "padding": "9px 20px",
        "fontFamily": "'Montserrat', sans-serif",
        "fontWeight": "700", "fontSize": "0.85rem", "cursor": "pointer"
    }

    cfg   = DB_TABLES.get(table_name, {"label": table_name})
    title = f"Modifier — {cfg['label']} (id={row_id})"

    return True, title, form_fields, {"table": table_name, "id": row_id}, delete_style


# ── Sauvegarder édition ──────────────────────────────────────
@callback(
    Output("db-modal-feedback", "children"),
    Output("db-page-refresh",   "data", allow_duplicate=True),
    Output("modal-db-edit",     "is_open", allow_duplicate=True),
    Input("btn-db-save",        "n_clicks"),
    State("db-edit-row",        "data"),
    State({"type": "db-field",  "index": dash.ALL}, "value"),
    State({"type": "db-field",  "index": dash.ALL}, "id"),
    prevent_initial_call=True
)
def save_db_row(n, row_info, values, ids):
    if not n or not row_info:
        return dash.no_update, dash.no_update, dash.no_update
    data = {id_["index"]: val for id_, val in zip(ids, values)}
    ok, err = upsert_row(row_info["table"], data, row_id=row_info["id"])
    if ok:
        return "", time.time(), False
    return f"Erreur : {err}", dash.no_update, True


# ── Supprimer ligne ──────────────────────────────────────────
@callback(
    Output("db-page-refresh",            "data", allow_duplicate=True),
    Output("modal-db-edit",              "is_open", allow_duplicate=True),
    Input("btn-db-delete",               "n_clicks"),
    Input({"type": "btn-db-delete-row",  "index": dash.ALL}, "n_clicks"),
    State("db-edit-row",                 "data"),
    prevent_initial_call=True
)
def delete_db_row(n_modal, n_rows, row_info):
    triggered = ctx.triggered_id

    # Suppression depuis le modal
    if triggered == "btn-db-delete" and n_modal and row_info:
        ok, _ = delete_row(row_info["table"], row_info["id"])
        return (time.time(), False) if ok else (dash.no_update, True)

    # Suppression rapide depuis le tableau
    if isinstance(triggered, dict) and triggered.get("type") == "btn-db-delete-row":
        if any(n_rows):
            ref        = triggered["index"]
            table_name, row_id = ref.rsplit(":", 1)
            ok, _      = delete_row(table_name, int(row_id))
            return (time.time(), dash.no_update) if ok else (dash.no_update, dash.no_update)

    return dash.no_update, dash.no_update