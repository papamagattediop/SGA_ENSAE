# ============================================================
#  SGA ENSAE — components/navbar.py
#  Barre de navigation avec icones Material Symbols
#  Python 3.11 · Dash 2.17.0
# ============================================================

import dash_bootstrap_components as dbc
from dash import html

BLEU  = "#003580"
VERT  = "#006B3F"
OR    = "#F5A623"
BLANC = "#FFFFFF"


def icon(name: str, size: str = "20px") -> html.Span:
    """
    Retourne une icone Material Symbols.
    Utilisation : icon("dashboard"), icon("school"), icon("logout")
    Voir toutes les icones : https://fonts.google.com/icons
    """
    return html.Span(
        name,
        className="material-symbols-outlined",
        style={
            "fontSize"     : size,
            "verticalAlign": "middle",
            "lineHeight"   : "1",
        }
    )


def logo_ensae() -> html.Div:
    """Logo ENSAE depuis assets/img/logo_ensae.png avec style."""
    return html.Div(
        style={"display": "flex", "alignItems": "center", "gap": "10px"},
        children=[
            # Logo image avec style
            html.Div(
                style={
                    "display"       : "flex",
                    "alignItems"    : "center",
                    "justifyContent": "center",
                    "flexShrink"    : "0",
                },
                children=html.Img(
                    src="/assets/img/logo_ensae.png",
                    style={
                        "height"      : "44px",
                        "width"       : "auto",
                        "objectFit"   : "contain",
                        "borderRadius": "8px",
                        "padding"     : "3px",
                        "background"  : "rgba(255,255,255,0.92)",
                        "boxShadow"   : "0 2px 10px rgba(0,0,0,0.25), 0 0 0 1.5px rgba(245,166,35,0.5)",
                        "transition"  : "box-shadow 0.2s",
                    }
                )
            ),
            # Texte
            html.Div([
                html.Div(
                    "SGA ENSAE",
                    style={
                        "fontFamily"   : "'Montserrat', sans-serif",
                        "fontWeight"   : "800",
                        "fontSize"     : "0.95rem",
                        "color"        : BLANC,
                        "lineHeight"   : "1.1",
                        "letterSpacing": "0.5px",
                    }
                ),
                html.Div(
                    "Gestion Academique",
                    style={
                        "fontFamily": "'Inter', sans-serif",
                        "fontSize"  : "0.62rem",
                        "color"     : "rgba(255,255,255,0.6)",
                        "fontWeight": "400",
                    }
                ),
            ])
        ]
    )


def nav_link(label: str, href: str, icon_name: str) -> dbc.NavItem:
    """Genere un lien de navigation avec icone."""
    return dbc.NavItem(
        dbc.NavLink(
            html.Span(
                [icon(icon_name), html.Span(label, style={"marginLeft": "6px"})],
                style={"display": "flex", "alignItems": "center"}
            ),
            href=href,
            active="exact",
            style={
                "color"        : "rgba(255,255,255,0.82)",
                "padding"      : "7px 13px",
                "borderRadius" : "6px",
                "fontFamily"   : "'Inter', sans-serif",
                "fontSize"     : "0.85rem",
                "transition"   : "background 0.2s",
                "display"      : "flex",
                "alignItems"   : "center",
            }
        )
    )


def create_navbar(session: dict) -> html.Div:
    """Genere la navbar complete selon le role connecte."""

    role   = session.get("role", "")
    prenom = session.get("prenom", "")
    nom    = session.get("nom", "")

    # -- Liens selon role --
    links = [nav_link("Tableau de bord", "/dashboard", "dashboard")]

    if role in ("admin", "resp_filiere", "resp_classe"):
        links += [
            nav_link("Cours et UE",  "/cours",      "menu_book"),
            nav_link("Seances",      "/seances",    "calendar_today"),
            nav_link("Etudiants",    "/etudiants",  "school"),
            nav_link("Planning",     "/planning",   "event_note"),
            nav_link("Bulletins",    "/bulletins",  "description"),
        ]

    if role in ("admin", "resp_filiere"):
        links.append(nav_link("Statistiques", "/statistiques", "bar_chart"))

    if role == "admin":
        links.append(nav_link("Administration", "/admin", "manage_accounts"))

    # -- Badge utilisateur connecte --
    initiales = f"{prenom[0]}{nom[0]}" if prenom and nom else "?"

    user_badge = dbc.NavItem(
        html.Div(
            style={
                "display"    : "flex",
                "alignItems" : "center",
                "gap"        : "10px",
                "marginLeft" : "16px",
                "paddingLeft": "16px",
                "borderLeft" : "1px solid rgba(255,255,255,0.2)",
            },
            children=[
                # Avatar initiales
                html.Div(
                    initiales,
                    style={
                        "width"          : "34px",
                        "height"         : "34px",
                        "borderRadius"   : "50%",
                        "background"     : OR,
                        "display"        : "flex",
                        "alignItems"     : "center",
                        "justifyContent" : "center",
                        "color"          : BLEU,
                        "fontWeight"     : "700",
                        "fontSize"       : "0.75rem",
                        "fontFamily"     : "'Montserrat', sans-serif",
                        "flexShrink"     : "0",
                    }
                ),
                # Nom + role
                html.Div([
                    html.Div(
                        f"{prenom} {nom}",
                        style={
                            "color"      : BLANC,
                            "fontSize"   : "0.8rem",
                            "fontWeight" : "600",
                            "fontFamily" : "'Inter', sans-serif",
                            "lineHeight" : "1.1",
                        }
                    ),
                    html.Div(
                        role.replace("_", " ").title(),
                        style={
                            "color"     : OR,
                            "fontSize"  : "0.62rem",
                            "fontFamily": "'Inter', sans-serif",
                        }
                    ),
                ]),
                # Bouton deconnexion
                dbc.NavLink(
                    html.Span(
                        [icon("logout", "18px"),
                         html.Span("Deconnexion", style={"marginLeft": "4px", "fontSize": "0.75rem"})],
                        style={"display": "flex", "alignItems": "center"}
                    ),
                    href="/",
                    style={
                        "color"       : "rgba(255,255,255,0.6)",
                        "padding"     : "5px 10px",
                        "borderRadius": "6px",
                        "border"      : "1px solid rgba(255,255,255,0.2)",
                        "fontFamily"  : "'Inter', sans-serif",
                        "transition"  : "all 0.2s",
                    }
                )
            ]
        )
    )

    links.append(user_badge)

    return html.Div([
        dbc.Navbar(
            dbc.Container([
                dbc.NavbarBrand(logo_ensae(), href="/dashboard"),
                dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
                dbc.Collapse(
                    dbc.Nav(
                        links,
                        navbar=True,
                        className="ms-auto",
                        style={"alignItems": "center", "gap": "2px"}
                    ),
                    id="navbar-collapse",
                    navbar=True,
                    is_open=False,
                )
            ], fluid=True),
            style={
                "background"  : f"linear-gradient(135deg, {BLEU} 0%, #002060 100%)",
                "borderBottom": f"3px solid {OR}",
                "padding"     : "6px 0",
                "boxShadow"   : "0 2px 12px rgba(0,53,128,0.3)",
            },
            dark=True,
            sticky="top",
        )
    ])