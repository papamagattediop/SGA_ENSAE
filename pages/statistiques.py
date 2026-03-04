# ============================================================
#  SGA ENSAE — pages/statistiques.py
#  Module 8 : Analyses et visualisations statistiques
#  Python 3.11 · Dash 2.17.0 · Plotly
# ============================================================

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from database import SessionLocal
from models import Etudiant, Note, Presence, Module, Classe, Seance, UE
from sqlalchemy import func

dash.register_page(__name__, path="/statistiques", title="SGA ENSAE — Statistiques")

BLEU = "#003580"
VERT = "#006B3F"
OR   = "#F5A623"

PALETTE = [BLEU, VERT, OR, "#8b5cf6", "#ef4444", "#06b6d4",
           "#f97316", "#84cc16", "#ec4899", "#14b8a6"]


# ============================================================
#  UTILITAIRES DB
# ============================================================

def get_classes():
    db = SessionLocal()
    try:
        return [{"label": c.nom, "value": c.id}
                for c in db.query(Classe).all()]
    finally:
        db.close()

def get_notes_data(classe_id=None):
    db = SessionLocal()
    try:
        q = db.query(Note).join(
            Etudiant, Note.etudiant_id == Etudiant.id
        )
        if classe_id:
            q = q.filter(Etudiant.classe_id == classe_id)
        return [n.note for n in q.all() if n.note is not None]
    finally:
        db.close()

def get_moyennes_etudiants(classe_id=None):
    db = SessionLocal()
    try:
        q = db.query(Etudiant)
        if classe_id:
            q = q.filter(Etudiant.classe_id == classe_id)
        etudiants = q.all()
        moyennes = []
        for e in etudiants:
            notes = db.query(Note).filter(Note.etudiant_id == e.id).all()
            if notes:
                moy = round(sum(n.note for n in notes) / len(notes), 2)
                moyennes.append({
                    "nom"   : f"{e.user.prenom} {e.user.nom}" if e.user else "-",
                    "classe": e.classe.nom if e.classe else "-",
                    "moy"   : moy
                })
        return sorted(moyennes, key=lambda x: x["moy"], reverse=True)
    finally:
        db.close()

def get_assiduite_data(classe_id=None):
    db = SessionLocal()
    try:
        q = db.query(Etudiant)
        if classe_id:
            q = q.filter(Etudiant.classe_id == classe_id)
        etudiants = q.all()
        result = []
        for e in etudiants:
            total = db.query(Presence).filter(
                Presence.etudiant_id == e.id).count()
            presents = db.query(Presence).filter(
                Presence.etudiant_id == e.id,
                Presence.present == True).count()
            taux = round((presents / total) * 100) if total > 0 else 100
            result.append({
                "nom"  : f"{e.user.prenom} {e.user.nom}" if e.user else "-",
                "taux" : taux,
                "abs"  : total - presents
            })
        return sorted(result, key=lambda x: x["taux"])
    finally:
        db.close()

def get_progression_modules(classe_id=None):
    db = SessionLocal()
    try:
        q = db.query(Module)
        if classe_id:
            q = q.filter(Module.classe_id == classe_id)
        modules = q.all()
        result  = []
        for m in modules:
            seances = db.query(Seance).filter(
                Seance.module_id == m.id).all()
            heures = sum(
                (s.heure_fin.hour * 60 + s.heure_fin.minute -
                 s.heure_debut.hour * 60 - s.heure_debut.minute) / 60
                for s in seances
                if s.heure_debut and s.heure_fin
            )
            pct = min(round((heures / m.volume_horaire) * 100)
                      if m.volume_horaire else 0, 100)
            result.append({
                "module"  : m.code,
                "libelle" : m.libelle,
                "fait"    : round(heures, 1),
                "total"   : m.volume_horaire or 0,
                "pct"     : pct
            })
        return sorted(result, key=lambda x: x["pct"])
    finally:
        db.close()

def get_notes_par_module(classe_id=None):
    db = SessionLocal()
    try:
        q = db.query(Module)
        if classe_id:
            q = q.filter(Module.classe_id == classe_id)
        modules = q.all()
        result  = []
        for m in modules:
            notes = db.query(Note).join(
                Etudiant, Note.etudiant_id == Etudiant.id
            ).filter(Note.module_id == m.id).all()
            vals = [n.note for n in notes if n.note is not None]
            if vals:
                result.append({
                    "module": m.code,
                    "moy"   : round(sum(vals) / len(vals), 2),
                    "min"   : min(vals),
                    "max"   : max(vals),
                    "n"     : len(vals)
                })
        return sorted(result, key=lambda x: x["moy"], reverse=True)
    finally:
        db.close()

def get_seances_par_semaine():
    db = SessionLocal()
    try:
        seances = db.query(Seance).filter(Seance.date != None).all()
        par_sem = {}
        for s in seances:
            sem = s.date.strftime("%Y-S%W")
            par_sem[sem] = par_sem.get(sem, 0) + 1
        return dict(sorted(par_sem.items()))
    finally:
        db.close()


# ============================================================
#  GRAPHIQUES PLOTLY
# ============================================================

def fig_layout(fig, title=""):
    fig.update_layout(
        title=dict(text=title, font=dict(family="Montserrat", size=13,
                                          color=BLEU), x=0.02),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="Inter", size=11, color="#374151"),
        margin=dict(l=40, r=20, t=40, b=40),
        legend=dict(
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
            font=dict(size=10)
        ),
        xaxis=dict(showgrid=True, gridcolor="#f3f4f6",
                   linecolor="#e5e7eb"),
        yaxis=dict(showgrid=True, gridcolor="#f3f4f6",
                   linecolor="#e5e7eb"),
    )
    return fig

def empty_fig(message="Aucune donnee disponible"):
    fig = go.Figure()
    fig.add_annotation(
        text=message, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=13, color="#9ca3af", family="Inter"),
    )
    fig.update_layout(
        plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
    )
    return fig

def graph_distribution_notes(notes):
    if not notes:
        return empty_fig("Aucune note enregistree")
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=notes,
        nbinsx=20,
        marker_color=BLEU,
        marker_line_color="white",
        marker_line_width=1,
        opacity=0.85,
        name="Notes"
    ))
    # Ligne moyenne
    moy = sum(notes) / len(notes)
    fig.add_vline(x=moy, line_dash="dash", line_color=OR,
                  annotation_text=f"Moy: {moy:.2f}",
                  annotation_font_color=OR,
                  annotation_font_size=10)
    fig.add_vline(x=10, line_dash="dot", line_color="#ef4444",
                  annotation_text="Seuil 10",
                  annotation_font_color="#ef4444",
                  annotation_font_size=10)
    fig.update_xaxes(range=[0, 20], title_text="Note /20")
    fig.update_yaxes(title_text="Nombre d'etudiants")
    return fig_layout(fig, "Distribution des notes")

def graph_moyennes_etudiants(moyennes):
    if not moyennes:
        return empty_fig("Aucune donnee disponible")
    top20 = moyennes[:20]
    colors_bar = [
        VERT if m["moy"] >= 12 else
        OR   if m["moy"] >= 10 else
        "#ef4444"
        for m in top20
    ]
    fig = go.Figure(go.Bar(
        x=[m["nom"] for m in top20],
        y=[m["moy"] for m in top20],
        marker_color=colors_bar,
        marker_line_color="white",
        marker_line_width=0.5,
        text=[f"{m['moy']:.1f}" for m in top20],
        textposition="outside",
        textfont=dict(size=9),
    ))
    fig.add_hline(y=10, line_dash="dot", line_color="#ef4444",
                  annotation_text="Moyenne 10",
                  annotation_font_color="#ef4444",
                  annotation_font_size=9)
    fig.update_xaxes(tickangle=-35, tickfont=dict(size=9))
    fig.update_yaxes(range=[0, 22], title_text="Moyenne /20")
    return fig_layout(fig, "Classement des etudiants (Top 20)")

def graph_assiduite(assiduite):
    if not assiduite:
        return empty_fig("Aucune donnee disponible")
    bottom20 = assiduite[:20]
    colors_bar = [
        "#ef4444" if a["taux"] < 60 else
        OR         if a["taux"] < 80 else
        VERT
        for a in bottom20
    ]
    fig = go.Figure(go.Bar(
        x=[a["nom"] for a in bottom20],
        y=[a["taux"] for a in bottom20],
        marker_color=colors_bar,
        marker_line_color="white",
        text=[f"{a['taux']}%" for a in bottom20],
        textposition="outside",
        textfont=dict(size=9),
    ))
    fig.add_hline(y=80, line_dash="dash", line_color=OR,
                  annotation_text="Seuil 80%",
                  annotation_font_color=OR,
                  annotation_font_size=9)
    fig.update_xaxes(tickangle=-35, tickfont=dict(size=9))
    fig.update_yaxes(range=[0, 110], title_text="Taux d'assiduite (%)")
    return fig_layout(fig, "Assiduite par etudiant (les plus absents)")

def graph_progression_modules(progression):
    if not progression:
        return empty_fig("Aucune donnee disponible")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Heures effectuees",
        x=[p["module"] for p in progression],
        y=[p["fait"] for p in progression],
        marker_color=BLEU,
        text=[f"{p['fait']}h" for p in progression],
        textposition="auto",
        textfont=dict(size=9, color="white"),
    ))
    fig.add_trace(go.Bar(
        name="Heures restantes",
        x=[p["module"] for p in progression],
        y=[max(p["total"] - p["fait"], 0) for p in progression],
        marker_color="#e5e7eb",
    ))
    fig.update_layout(barmode="stack")
    fig.update_xaxes(tickangle=-35, tickfont=dict(size=9))
    fig.update_yaxes(title_text="Heures")
    return fig_layout(fig, "Progression horaire par module")

def graph_notes_par_module(notes_mod):
    if not notes_mod:
        return empty_fig("Aucune donnee disponible")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Moyenne",
        x=[n["module"] for n in notes_mod],
        y=[n["moy"] for n in notes_mod],
        marker_color=[
            VERT if n["moy"] >= 12 else
            OR   if n["moy"] >= 10 else
            "#ef4444"
            for n in notes_mod
        ],
        text=[f"{n['moy']:.1f}" for n in notes_mod],
        textposition="outside",
        textfont=dict(size=9),
        error_y=dict(
            type="data",
            symmetric=False,
            array=[n["max"] - n["moy"] for n in notes_mod],
            arrayminus=[n["moy"] - n["min"] for n in notes_mod],
            color="#9ca3af",
            thickness=1.5,
            width=4
        )
    ))
    fig.add_hline(y=10, line_dash="dot", line_color="#ef4444",
                  annotation_text="Seuil 10",
                  annotation_font_color="#ef4444",
                  annotation_font_size=9)
    fig.update_xaxes(tickangle=-35, tickfont=dict(size=9))
    fig.update_yaxes(range=[0, 22], title_text="Moyenne /20")
    return fig_layout(fig, "Moyennes par module (min / moy / max)")

def graph_repartition_mentions(notes):
    if not notes:
        return empty_fig("Aucune donnee disponible")
    tranches = {
        "Insuffisant (<10)" : len([n for n in notes if n < 10]),
        "Passable (10-12)"  : len([n for n in notes if 10 <= n < 12]),
        "Assez Bien (12-14)": len([n for n in notes if 12 <= n < 14]),
        "Bien (14-16)"      : len([n for n in notes if 14 <= n < 16]),
        "Tres Bien (>=16)"  : len([n for n in notes if n >= 16]),
    }
    colors_pie = ["#ef4444", OR, VERT, BLEU, "#8b5cf6"]
    fig = go.Figure(go.Pie(
        labels=list(tranches.keys()),
        values=list(tranches.values()),
        marker_colors=colors_pie,
        hole=0.45,
        textinfo="percent+label",
        textfont=dict(size=10),
        insidetextorientation="radial",
    ))
    fig.update_layout(showlegend=False)
    return fig_layout(fig, "Repartition des mentions")

def graph_seances_semaine(data):
    if not data:
        return empty_fig("Aucune donnee disponible")
    fig = go.Figure(go.Scatter(
        x=list(data.keys()),
        y=list(data.values()),
        mode="lines+markers",
        line=dict(color=BLEU, width=2.5),
        marker=dict(color=OR, size=7, line=dict(color=BLEU, width=1.5)),
        fill="tozeroy",
        fillcolor=f"rgba(0,53,128,0.08)",
    ))
    fig.update_xaxes(tickangle=-35, tickfont=dict(size=9),
                     title_text="Semaine")
    fig.update_yaxes(title_text="Nombre de seances")
    return fig_layout(fig, "Evolution des seances par semaine")


# ============================================================
#  COMPOSANTS UI
# ============================================================

def stat_chip(label, valeur, couleur):
    return html.Div(style={
        "background": "#ffffff", "borderRadius": "10px",
        "padding": "14px 18px", "border": "1px solid #e5e7eb",
        "textAlign": "center"
    }, children=[
        html.P(label, style={
            "color": "#6b7280", "fontSize": "0.7rem", "margin": "0",
            "fontFamily": "'Inter', sans-serif", "fontWeight": "500",
            "textTransform": "uppercase", "letterSpacing": "0.4px"
        }),
        html.H4(str(valeur), style={
            "color": couleur, "fontFamily": "'Montserrat', sans-serif",
            "fontWeight": "800", "margin": "4px 0 0", "fontSize": "1.5rem"
        })
    ])

def graph_card(graph_id, height=320):
    return html.Div(style={
        "background": "#ffffff", "borderRadius": "12px",
        "padding": "4px", "border": "1px solid #e5e7eb",
        "height": "100%"
    }, children=[
        dcc.Graph(
            id=graph_id,
            config={"displayModeBar": False, "responsive": True},
            style={"height": f"{height}px"}
        )
    ])


# ============================================================
#  LAYOUT
# ============================================================

layout = html.Div([

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
        html.H4("Statistiques et Analyses", style={
            "fontFamily": "'Montserrat', sans-serif",
            "fontWeight": "800", "color": BLEU, "margin": "0"
        }),
        html.P("Visualisations des performances academiques et de l'assiduite",
               style={"color": "#6b7280", "fontFamily": "'Inter', sans-serif",
                      "margin": "4px 0 0"})
    ]),

    # -- Filtre --
    html.Div(style={
        "background": "#ffffff", "borderRadius": "12px",
        "padding": "14px 24px", "border": "1px solid #e5e7eb",
        "marginBottom": "20px", "display": "flex",
        "alignItems": "center", "gap": "12px"
    }, children=[
        html.Span("filter_list", className="material-symbols-outlined",
                  style={"fontSize": "20px", "color": BLEU}),
        html.Div(style={"width": "220px"}, children=[
            dcc.Dropdown(
                id="stats-filtre-classe",
                placeholder="Toutes les classes",
                style={"fontFamily": "'Inter', sans-serif", "fontSize": "0.875rem"}
            )
        ]),
        html.P("Par defaut : statistiques globales de toute l'ecole. "
               "Selectionnez une classe pour filtrer.",
               style={"color": "#9ca3af", "fontSize": "0.78rem",
                      "fontFamily": "'Inter', sans-serif", "margin": "0"})
    ]),

    # -- KPIs rapides --
    html.Div(id="stats-kpis", style={"marginBottom": "24px"}),

    # -- Ligne 1 : Distribution + Mentions --
    dbc.Row([
        dbc.Col(graph_card("graph-distribution"), md=8),
        dbc.Col(graph_card("graph-mentions", height=320), md=4),
    ], className="g-3 mb-3"),

    # -- Ligne 2 : Classement etudiants --
    dbc.Row([
        dbc.Col(graph_card("graph-classement", height=300), md=12),
    ], className="g-3 mb-3"),

    # -- Ligne 3 : Assiduite + Progression modules --
    dbc.Row([
        dbc.Col(graph_card("graph-assiduite",   height=300), md=6),
        dbc.Col(graph_card("graph-progression", height=300), md=6),
    ], className="g-3 mb-3"),

    # -- Ligne 4 : Notes par module + Seances --
    dbc.Row([
        dbc.Col(graph_card("graph-notes-modules", height=300), md=7),
        dbc.Col(graph_card("graph-seances-semaine", height=300), md=5),
    ], className="g-3"),
])


# ============================================================
#  CALLBACKS
# ============================================================

@callback(
    Output("stats-filtre-classe", "options"),
    Input("session-store", "data")
)
def load_classes(_):
    return get_classes()


@callback(
    Output("stats-kpis",            "children"),
    Output("graph-distribution",    "figure"),
    Output("graph-mentions",        "figure"),
    Output("graph-classement",      "figure"),
    Output("graph-assiduite",       "figure"),
    Output("graph-progression",     "figure"),
    Output("graph-notes-modules",   "figure"),
    Output("graph-seances-semaine", "figure"),
    Input("stats-filtre-classe",    "value"),
    Input("session-store",          "data"),
)
def update_all(classe_id, session):
    # classe_id = None => stats globales de toute l'ecole
    notes      = get_notes_data(classe_id)
    moyennes   = get_moyennes_etudiants(classe_id)
    assiduite  = get_assiduite_data(classe_id)
    progression= get_progression_modules(classe_id)
    notes_mod  = get_notes_par_module(classe_id)
    seances_sem= get_seances_par_semaine()

    # classe_id None = toutes classes (stats globales)
    # KPIs
    nb_notes   = len(notes)
    moy_gen    = round(sum(notes) / nb_notes, 2) if notes else None
    taux_reuss = round(len([n for n in notes if n >= 10]) / nb_notes * 100) \
                 if nb_notes else None
    moy_assid  = round(sum(a["taux"] for a in assiduite) / len(assiduite)) \
                 if assiduite else None

    kpis = dbc.Row([
        dbc.Col(stat_chip("Moyenne generale",
                          f"{moy_gen}/20" if moy_gen else "-", BLEU), md=3),
        dbc.Col(stat_chip("Taux de reussite",
                          f"{taux_reuss}%" if taux_reuss is not None else "-", VERT), md=3),
        dbc.Col(stat_chip("Notes enregistrees",
                          nb_notes, OR), md=3),
        dbc.Col(stat_chip("Assiduite moyenne",
                          f"{moy_assid}%" if moy_assid else "-", "#8b5cf6"), md=3),
    ], className="g-3")

    return (
        kpis,
        graph_distribution_notes(notes),
        graph_repartition_mentions(notes),
        graph_moyennes_etudiants(moyennes),
        graph_assiduite(assiduite),
        graph_progression_modules(progression),
        graph_notes_par_module(notes_mod),
        graph_seances_semaine(seances_sem),
    )