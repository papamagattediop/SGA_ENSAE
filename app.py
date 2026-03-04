# ============================================================
#  SGA ENSAE — app.py
#  Point d'entree principal
#  Python 3.11 · Dash 2.17.0
# ============================================================

import dash
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
from database import init_db
from auth import create_admin

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&family=Inter:wght@300;400;500;600&display=swap",
        "https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200",
    ],
    suppress_callback_exceptions=True,
    title="SGA ENSAE"
)

server = app.server

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="session-store", storage_type="session"),
    html.Div(id="navbar-container"),
    html.Div(
        dash.page_container,
        style={"padding": "24px", "fontFamily": "'Inter', sans-serif"}
    )
], style={"background": "#F4F6F9", "minHeight": "100vh"})


@app.callback(
    Output("navbar-container", "children"),
    Input("session-store",     "data"),
    Input("url",               "pathname")
)
def update_navbar(session, pathname):
    # Ne pas afficher la navbar sur la page de login
    if pathname == "/" or not session or not session.get("user_id"):
        return html.Div()
    from components.navbar import create_navbar
    return create_navbar(session)


if __name__ == "__main__":
    init_db()
    create_admin(
        nom="Admin",
        prenom="SGA",
        email="admin@ensae.sn",
        password="admin123"
    )
    print("=" * 45)
    print("  SGA ENSAE - Demarrage")
    print("  http://127.0.0.1:8050")
    print("=" * 45)
    app.run(debug=True)