# ============================================================
#  SGA ENSAE — pages/login.py
#  Page de connexion — Layout split : image gauche / form droite
#  Python 3.11 · Dash 2.17.0
# ============================================================

import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from auth import login

dash.register_page(__name__, path="/", title="SGA ENSAE — Connexion")

BLEU = "#003580"
VERT = "#006B3F"
OR   = "#F5A623"


# ============================================================
#  HELPERS UI
# ============================================================

def _role_chip(label: str, icon: str, color: str) -> html.Div:
    return html.Div(
        style={
            "display"     : "inline-flex",
            "alignItems"  : "center",
            "gap"         : "5px",
            "background"  : f"{color}10",
            "border"      : f"1px solid {color}30",
            "borderRadius": "999px",
            "padding"     : "4px 10px",
            "fontSize"    : "0.72rem",
            "fontWeight"  : "600",
            "color"       : color,
            "fontFamily"  : "'Inter', sans-serif",
        },
        children=[
            html.Span(icon, className="material-symbols-outlined",
                      style={"fontSize": "13px"}),
            label,
        ]
    )


# ============================================================
#  LAYOUT
# ============================================================

layout = html.Div(
    style={
        "minHeight"  : "100vh",
        "display"    : "flex",
        "fontFamily" : "'Inter', sans-serif",
        "background" : "#f8fafc",
    },
    children=[

        # ══════════════════════════════════════════════════════
        #  PANNEAU GAUCHE — Image bâtiment + overlay texte
        # ══════════════════════════════════════════════════════
        html.Div(
            style={
                "flex"           : "1",
                "position"       : "relative",
                "overflow"       : "hidden",
                "display"        : "flex",
                "flexDirection"  : "column",
                "justifyContent" : "flex-end",
                "minWidth"       : "0",
            },
            children=[

                # Image de fond — bâtiment ENSAE
                html.Img(
                    src="/assets/img/ensae_building.png",
                    style={
                        "position"       : "absolute",
                        "top"            : "0",
                        "left"           : "0",
                        "width"          : "100%",
                        "height"         : "100%",
                        "objectFit"      : "cover",
                        "objectPosition" : "center",
                    }
                ),

                # Overlay gradient
                html.Div(
                    style={
                        "position"   : "absolute",
                        "top"        : "0",
                        "left"       : "0",
                        "width"      : "100%",
                        "height"     : "100%",
                        "background" : "linear-gradient(to bottom, rgba(0,31,77,0.25) 0%, rgba(0,31,77,0.88) 100%)",
                    }
                ),

                # Contenu texte en bas
                html.Div(
                    style={
                        "position" : "relative",
                        "zIndex"   : "2",
                        "padding"  : "44px 48px",
                        "color"    : "#ffffff",
                    },
                    children=[

                        # Badge
                        html.Div(
                            style={
                                "display"        : "inline-flex",
                                "alignItems"     : "center",
                                "gap"            : "8px",
                                "background"     : "rgba(255,255,255,0.12)",
                                "backdropFilter" : "blur(8px)",
                                "borderRadius"   : "999px",
                                "padding"        : "6px 16px",
                                "marginBottom"   : "22px",
                                "border"         : "1px solid rgba(255,255,255,0.2)",
                            },
                            children=[
                                html.Div(style={
                                    "width": "7px", "height": "7px",
                                    "borderRadius": "50%", "background": OR,
                                }),
                                html.Span("ENSAE Pierre Ndiaye De DAKAR", style={
                                    "fontSize"     : "0.75rem",
                                    "fontWeight"   : "600",
                                    "letterSpacing": "0.04em",
                                }),
                            ]
                        ),

                        html.H2(
                            "École Nationale de la Statistique",
                            style={
                                "fontFamily" : "'Montserrat', sans-serif",
                                "fontWeight" : "800",
                                "fontSize"   : "1.65rem",
                                "margin"     : "0 0 4px",
                                "lineHeight" : "1.25",
                            }
                        ),
                        html.H2(
                            "et de l'Analyse Économique",
                            style={
                                "fontFamily" : "'Montserrat', sans-serif",
                                "fontWeight" : "800",
                                "fontSize"   : "1.65rem",
                                "margin"     : "0 0 18px",
                                "lineHeight" : "1.25",
                                "color"      : OR,
                            }
                        ),
                        html.P(
                            "Plateforme de gestion académique centralisée pour étudiants, "
                            "enseignants et responsables de filière.",
                            style={
                                "fontSize"  : "0.88rem",
                                "color"     : "rgba(255,255,255,0.78)",
                                "lineHeight": "1.65",
                                "maxWidth"  : "400px",
                                "margin"    : "0",
                            }
                        ),
                    ]
                ),
            ]
        ),

        # ══════════════════════════════════════════════════════
        #  PANNEAU DROIT — Formulaire de connexion
        # ══════════════════════════════════════════════════════
        html.Div(
            style={
                "width"          : "460px",
                "flexShrink"     : "0",
                "background"     : "#ffffff",
                "display"        : "flex",
                "flexDirection"  : "column",
                "justifyContent" : "center",
                "padding"        : "56px 48px",
                "boxShadow"      : "-8px 0 48px rgba(0,0,0,0.08)",
                "position"       : "relative",
                "zIndex"         : "10",
            },
            children=[

                # Logo + titre
                html.Div(
                    style={"marginBottom": "40px"},
                    children=[
                        html.Img(
                            src="/assets/img/logo_ensae.png",
                            style={
                                "height"      : "60px",
                                "width"       : "auto",
                                "objectFit"   : "contain",
                                "display"     : "block",
                                "marginBottom": "22px",
                            }
                        ),
                        html.H3(
                            "Bienvenue",
                            style={
                                "fontFamily" : "'Montserrat', sans-serif",
                                "fontWeight" : "800",
                                "color"      : "#111827",
                                "fontSize"   : "1.8rem",
                                "margin"     : "0 0 6px",
                            }
                        ),
                        html.P(
                            "Connectez-vous à votre espace SGA ENSAE",
                            style={
                                "color"     : "#6b7280",
                                "fontSize"  : "0.88rem",
                                "margin"    : "0",
                            }
                        ),
                    ]
                ),

                # ── Champ identifiant ────────────────────────
                html.Div(style={"marginBottom": "20px"}, children=[
                    html.Label("Identifiant", style={
                        "fontWeight"  : "600",
                        "fontSize"    : "0.84rem",
                        "color"       : "#374151",
                        "marginBottom": "8px",
                        "display"     : "block",
                    }),
                    html.Div(style={"position": "relative"}, children=[
                        html.Span("person", className="material-symbols-outlined", style={
                            "position"     : "absolute",
                            "left"         : "14px",
                            "top"          : "50%",
                            "transform"    : "translateY(-50%)",
                            "fontSize"     : "18px",
                            "color"        : "#9ca3af",
                            "zIndex"       : "1",
                            "pointerEvents": "none",
                        }),
                        dbc.Input(
                            id="login-email",
                            type="text",
                            placeholder="Email ou matricule étudiant",
                            style={
                                "borderRadius": "10px",
                                "border"      : "1.5px solid #e5e7eb",
                                "padding"     : "12px 14px 12px 46px",
                                "fontSize"    : "0.9rem",
                                "background"  : "#f9fafb",
                                "width"       : "100%",
                            }
                        ),
                    ]),
                ]),

                # ── Champ mot de passe ───────────────────────
                html.Div(style={"marginBottom": "6px"}, children=[
                    html.Label("Mot de passe", style={
                        "fontWeight"  : "600",
                        "fontSize"    : "0.84rem",
                        "color"       : "#374151",
                        "marginBottom": "8px",
                        "display"     : "block",
                    }),
                    html.Div(style={"position": "relative"}, children=[
                        html.Span("lock", className="material-symbols-outlined", style={
                            "position"     : "absolute",
                            "left"         : "14px",
                            "top"          : "50%",
                            "transform"    : "translateY(-50%)",
                            "fontSize"     : "18px",
                            "color"        : "#9ca3af",
                            "zIndex"       : "1",
                            "pointerEvents": "none",
                        }),
                        dbc.Input(
                            id="login-password",
                            type="password",
                            placeholder="••••••••",
                            style={
                                "borderRadius": "10px",
                                "border"      : "1.5px solid #e5e7eb",
                                "padding"     : "12px 14px 12px 46px",
                                "fontSize"    : "0.9rem",
                                "background"  : "#f9fafb",
                                "width"       : "100%",
                            }
                        ),
                    ]),
                ]),

                # Hint matricule
                html.P(
                    "💡 Étudiants : votre matricule est votre identifiant",
                    style={
                        "fontSize"  : "0.74rem",
                        "color"     : "#9ca3af",
                        "margin"    : "6px 0 22px",
                        "fontStyle" : "italic",
                    }
                ),

                # Message d'erreur
                html.Div(
                    id="login-error",
                    style={
                        "color"       : "#ef4444",
                        "fontSize"    : "0.82rem",
                        "marginBottom": "14px",
                        "minHeight"   : "20px",
                        "display"     : "flex",
                        "alignItems"  : "center",
                        "gap"         : "6px",
                    }
                ),

                # Bouton connexion
                html.Button(
                    [
                        html.Span("login", className="material-symbols-outlined",
                                  style={"fontSize": "18px", "marginRight": "8px",
                                         "verticalAlign": "middle"}),
                        "Se connecter",
                    ],
                    id="login-btn",
                    n_clicks=0,
                    style={
                        "width"          : "100%",
                        "padding"        : "13px",
                        "background"     : f"linear-gradient(135deg, {BLEU} 0%, #0047b3 100%)",
                        "color"          : "white",
                        "border"         : "none",
                        "borderRadius"   : "10px",
                        "fontFamily"     : "'Montserrat', sans-serif",
                        "fontWeight"     : "700",
                        "fontSize"       : "0.95rem",
                        "cursor"         : "pointer",
                        "letterSpacing"  : "0.4px",
                        "boxShadow"      : "0 6px 20px rgba(0,53,128,0.32)",
                        "display"        : "flex",
                        "alignItems"     : "center",
                        "justifyContent" : "center",
                        "transition"     : "opacity 0.2s",
                    }
                ),

                dcc.Location(id="login-redirect", refresh=True),

                # ── Chips rôles ──────────────────────────────
                html.Div(
                    style={
                        "marginTop"  : "36px",
                        "paddingTop" : "24px",
                        "borderTop"  : "1px solid #f3f4f6",
                    },
                    children=[
                        html.P("Accès selon votre rôle", style={
                            "fontSize"     : "0.72rem",
                            "color"        : "#9ca3af",
                            "fontWeight"   : "600",
                            "margin"       : "0 0 12px",
                            "textTransform": "uppercase",
                            "letterSpacing": "0.06em",
                        }),
                        html.Div(
                            style={"display": "flex", "gap": "8px", "flexWrap": "wrap"},
                            children=[
                                _role_chip("Admin",         "manage_accounts", BLEU),
                                _role_chip("Resp. Filière", "school",          VERT),
                                _role_chip("Délégué",       "groups",          OR),
                                _role_chip("Étudiant",      "person",          "#8b5cf6"),
                            ]
                        ),
                    ]
                ),

                # Footer
                html.Div(
                    style={
                        "position" : "absolute",
                        "bottom"   : "20px",
                        "left"     : "48px",
                        "right"    : "48px",
                        "textAlign": "center",
                    },
                    children=[
                        html.P(
                            "© 2024-2025 ENSAE Dakar — Tous droits réservés",
                            style={
                                "color"    : "#d1d5db",
                                "fontSize" : "0.68rem",
                                "margin"   : "0",
                            }
                        )
                    ]
                ),
            ]
        ),
    ]
)


# ============================================================
#  CALLBACKS
# ============================================================

@callback(
    Output("session-store",  "data"),
    Output("login-redirect", "pathname"),
    Output("login-error",    "children"),
    Input("login-btn",       "n_clicks"),
    State("login-email",     "value"),
    State("login-password",  "value"),
    prevent_initial_call=True
)
def handle_login(n_clicks, identifiant, password):
    if not identifiant or not password:
        return dash.no_update, dash.no_update, [
            html.Span("error", className="material-symbols-outlined",
                      style={"fontSize": "15px"}),
            "Veuillez remplir tous les champs."
        ]

    session = login(identifiant, password)

    if session:
        return session, "/dashboard", ""

    return dash.no_update, dash.no_update, [
        html.Span("error", className="material-symbols-outlined",
                  style={"fontSize": "15px"}),
        "Identifiant ou mot de passe incorrect."
    ]
