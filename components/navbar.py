# ============================================================
#  SGA ENSAE — components/navbar.py
#  Navbar avec menus déroulants CSS pur, sans callbacks
#  Python 3.11 · Dash 2.17.0
# ============================================================

from dash import html

BLEU  = "#003580"
VERT  = "#006B3F"
OR    = "#F5A623"



# ============================================================
#  HELPERS
# ============================================================

def mi(name, color=None):
    s = {}
    if color: s["color"] = color
    return html.Span(name, className="mi", style=s)

def sga_link(label, href, icon_name):
    return html.Li(
        html.A([mi(icon_name), label], href=href, className="sga-link"),
        style={"listStyle": "none"}
    )

def sga_dropdown(trigger_label, trigger_icon, items, accent=OR):
    """
    items : liste de tuples (label, href, icon) ou "---" ou "## Titre"
    """
    menu = []
    for it in items:
        if it == "---":
            menu.append(html.Li(html.Div(className="sga-sep")))
        elif isinstance(it, str) and it.startswith("##"):
            menu.append(html.Li(html.Div(it[2:].strip(), className="sga-grp")))
        else:
            lbl, href, ico = it[0], it[1], it[2]
            menu.append(html.Li(
                html.A([mi(ico, accent), html.Span(lbl)],
                       href=href, className="sga-dd-item")
            ))

    return html.Li([
        html.Div([
            mi(trigger_icon),
            html.Span(trigger_label),
            html.Span("expand_more", className="chv mi")
        ], className="sga-dd-btn"),
        html.Ul(menu, className="sga-dd-menu")
    ], className="sga-dd")


# ============================================================
#  NAVBAR
# ============================================================

ROLE_LABELS = {
    "admin":        "Administrateur",
    "resp_filiere": "Resp. Filière",
    "resp_classe":  "Délégué / Resp. Classe",
    "eleve":        "Étudiant",
}

def create_navbar(session: dict) -> html.Div:
    role      = session.get("role",   "")
    prenom    = session.get("prenom", "")
    nom       = session.get("nom",    "")
    initiales = (prenom[0] + nom[0]).upper() if prenom and nom else "?"

    nav_items = []

    # ── Dashboard ────────────────────────────────────────────
    nav_items.append(sga_link("Accueil", "/dashboard", "dashboard"))

    # ── Pédagogie ────────────────────────────────────────────
    if role in ("admin", "resp_filiere", "resp_classe"):
        nav_items.append(sga_dropdown(
            "Pédagogie", "menu_book",
            [
                ("Cours & UE",   "/cours",    "library_books"),
                ("Séances",      "/seances",  "calendar_today"),
                ("Planning",     "/planning", "event_note"),
            ],
            accent=VERT
        ))

    # ── Étudiants ────────────────────────────────────────────
    if role in ("admin", "resp_filiere", "resp_classe"):
        nav_items.append(sga_dropdown(
            "Étudiants", "school",
            [
                ("Gestion",      "/etudiants",   "people"),
                ("Bulletins",    "/bulletins",   "description"),
            ],
            accent=VERT
        ))
    if role == "eleve":
        nav_items.append(sga_link("Mon planning", "/planning", "event_note"))
        nav_items.append(sga_link("Mes notes",    "/etudiants", "school"))
        nav_items.append(sga_link("Mon bulletin", "/bulletins", "description"))

    # ── Analyses ─────────────────────────────────────────────
    if role in ("admin", "resp_filiere"):
        nav_items.append(sga_link("Statistiques", "/statistiques", "bar_chart"))

    # ── Administration ───────────────────────────────────────
    if role == "admin":
        nav_items.append(sga_dropdown(
            "Admin", "manage_accounts",
            [
                "## Gestion",
                ("Utilisateurs & Rôles",  "/admin", "supervisor_account"),
                ("Base de données",       "/db",    "database"),
                "---",
                "## Données",
                ("Migration Excel",       "/admin", "upload_file"),
                ("Filières & Classes",    "/admin", "account_tree"),
            ],
            accent=OR
        ))

    # ── Zone utilisateur ─────────────────────────────────────
    user_zone = html.Div([
        html.Div(initiales, className="sga-avatar"),
        html.Div([
            html.Div(f"{prenom} {nom}",             className="sga-uname"),
            html.Div(ROLE_LABELS.get(role, role),   className="sga-urole"),
        ]),
        # Menu user déroulant au hover
        html.Div([
            html.Div([
                html.Div(f"{prenom} {nom}",                 className="sga-user-fullname"),
                html.Div(ROLE_LABELS.get(role, role),       className="sga-user-rolelbl"),
            ], className="sga-user-header"),
            html.A([mi("logout"), "Déconnexion"], href="/", className="sga-logout")
        ], className="sga-user-menu")
    ], className="sga-user")

    return html.Nav(className="sga-navbar", children=[
        # Logo
        html.A([
            html.Img(src="/assets/img/logo_ensae.png"),
            html.Div([
                html.Div("SGA ENSAE",           className="sga-logo-title"),
                html.Div("Gestion Académique",  className="sga-logo-sub"),
            ])
        ], href="/dashboard", className="sga-logo"),

        # Navigation
        html.Ul(nav_items, className="sga-nav"),

        # Utilisateur
        user_zone,
    ])