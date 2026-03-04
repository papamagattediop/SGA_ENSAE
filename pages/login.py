# ============================================================
#  SGA ENSAE — pages/login.py
#  Page de connexion — Page par defaut "/"
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
#  LAYOUT
# ============================================================

layout = html.Div(
    style={
        "minHeight"      : "100vh",
        "background"     : f"linear-gradient(135deg, {BLEU} 0%, #001f4d 60%, {VERT} 100%)",
        "display"        : "flex",
        "alignItems"     : "center",
        "justifyContent" : "center",
        "fontFamily"     : "'Inter', sans-serif",
        "padding"        : "20px",
    },
    children=[
        html.Div(
            style={
                "background"   : "#ffffff",
                "borderRadius" : "16px",
                "padding"      : "48px 40px",
                "width"        : "100%",
                "maxWidth"     : "440px",
                "boxShadow"    : "0 24px 64px rgba(0,0,0,0.25)",
            },
            children=[

                # -- Header --
                html.Div(
                    style={"textAlign": "center", "marginBottom": "32px"},
                    children=[
                        html.Img(
                            src="/assets/img/logo_ensae.png",
                            style={
                                "height"      : "80px",
                                "width"       : "auto",
                                "objectFit"   : "contain",
                                "display"     : "block",
                                "margin"      : "0 auto 16px",
                                "borderRadius": "12px",
                                "padding"     : "6px",
                                "background"  : "#ffffff",
                                "boxShadow"   : "0 4px 20px rgba(0,53,128,0.15), 0 0 0 2px rgba(0,53,128,0.1)",
                            }
                        ),
                        html.H2(
                            "SGA ENSAE",
                            style={
                                "fontFamily"   : "'Montserrat', sans-serif",
                                "fontWeight"   : "800",
                                "color"        : BLEU,
                                "fontSize"     : "1.6rem",
                                "marginBottom" : "4px",
                            }
                        ),
                        html.P(
                            "Systeme de Gestion Academique",
                            style={"color": "#6b7280", "fontSize": "0.875rem", "margin": "0"}
                        ),
                        html.P(
                            "Ecole Nationale de la Statistique et de l'Analyse Economique",
                            style={"color": "#9ca3af", "fontSize": "0.72rem", "margin": "4px 0 0"}
                        ),
                    ]
                ),

                # -- Separateur --
                html.Hr(style={"borderColor": "#e5e7eb", "margin": "0 0 28px"}),

                # -- Formulaire --
                html.Div([

                    html.Label("Adresse email", style={
                        "fontWeight"   : "600",
                        "fontSize"     : "0.85rem",
                        "color"        : "#374151",
                        "marginBottom" : "6px",
                        "display"      : "block",
                        "fontFamily"   : "'Inter', sans-serif",
                    }),
                    dbc.Input(
                        id="login-email",
                        type="email",
                        placeholder="exemple@ensae.sn",
                        style={
                            "borderRadius" : "8px",
                            "border"       : "1.5px solid #d1d5db",
                            "padding"      : "10px 14px",
                            "fontSize"     : "0.9rem",
                            "marginBottom" : "20px",
                            "fontFamily"   : "'Inter', sans-serif",
                        }
                    ),

                    html.Label("Mot de passe", style={
                        "fontWeight"   : "600",
                        "fontSize"     : "0.85rem",
                        "color"        : "#374151",
                        "marginBottom" : "6px",
                        "display"      : "block",
                        "fontFamily"   : "'Inter', sans-serif",
                    }),
                    dbc.Input(
                        id="login-password",
                        type="password",
                        placeholder="••••••••",
                        style={
                            "borderRadius" : "8px",
                            "border"       : "1.5px solid #d1d5db",
                            "padding"      : "10px 14px",
                            "fontSize"     : "0.9rem",
                            "marginBottom" : "8px",
                            "fontFamily"   : "'Inter', sans-serif",
                        }
                    ),

                    # Message erreur
                    html.Div(
                        id="login-error",
                        style={
                            "color"        : "#ef4444",
                            "fontSize"     : "0.8rem",
                            "marginBottom" : "16px",
                            "minHeight"    : "20px",
                            "fontFamily"   : "'Inter', sans-serif",
                        }
                    ),

                    # Bouton
                    html.Button(
                        "Se connecter",
                        id="login-btn",
                        n_clicks=0,
                        style={
                            "width"        : "100%",
                            "padding"      : "12px",
                            "background"   : f"linear-gradient(135deg, {BLEU}, #0047b3)",
                            "color"        : "white",
                            "border"       : "none",
                            "borderRadius" : "8px",
                            "fontFamily"   : "'Montserrat', sans-serif",
                            "fontWeight"   : "700",
                            "fontSize"     : "0.95rem",
                            "cursor"       : "pointer",
                            "letterSpacing": "0.5px",
                            "boxShadow"    : "0 4px 16px rgba(0,53,128,0.3)",
                            "transition"   : "opacity 0.2s",
                        }
                    ),

                    dcc.Location(id="login-redirect", refresh=True),
                ]),

                # -- Footer --
                html.Div(
                    style={"textAlign": "center", "marginTop": "24px"},
                    children=[
                        html.Div(
                            style={
                                "display"        : "flex",
                                "alignItems"     : "center",
                                "justifyContent" : "center",
                                "gap"            : "8px",
                            },
                            children=[
                                html.Div(style={"width": "8px", "height": "8px", "borderRadius": "50%", "background": BLEU}),
                                html.Div(style={"width": "8px", "height": "8px", "borderRadius": "50%", "background": OR}),
                                html.Div(style={"width": "8px", "height": "8px", "borderRadius": "50%", "background": VERT}),
                            ]
                        ),
                        html.P(
                            "2024-2025 ENSAE Dakar — Tous droits reserves",
                            style={
                                "color"     : "#9ca3af",
                                "fontSize"  : "0.7rem",
                                "marginTop" : "8px",
                                "fontFamily": "'Inter', sans-serif",
                            }
                        )
                    ]
                )
            ]
        )
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
def handle_login(n_clicks, email, password):
    if not email or not password:
        return dash.no_update, dash.no_update, "Veuillez remplir tous les champs."

    session = login(email, password)

    if session:
        return session, "/dashboard", ""

    return dash.no_update, dash.no_update, "Email ou mot de passe incorrect."