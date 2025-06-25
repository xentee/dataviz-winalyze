import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from collections import Counter

from riot_api import (
    get_account_by_riot_id,
    get_summoner_by_puuid,
    get_match_ids,
    get_match_data
)

# === Initialisation de l'app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "Winalyze"

# === Layout principal
app.layout = dbc.Container([
    html.H1("\U0001F3C6 Winalyze", className="text-center my-4"),

    dbc.Row([
        dbc.Col([
            dbc.Input(id="game-name", placeholder="Nom Riot ID", type="text"),
        ], width=6),
        dbc.Col([
            dbc.Input(id="tag-line", placeholder="Tagline (ex: EUW)", type="text"),
        ], width=3),
        dbc.Col([
            dbc.Button("Analyser", id="submit", color="primary", className="w-100")
        ], width=3)
    ], className="mb-4"),

    dbc.Spinner(html.Div(id="main-content"), color="primary", fullscreen=False, type="border"),

    dcc.Store(id="all-stats"),
    dcc.Store(id="current-page", data=1)

], fluid=True)

@app.callback(
    Output("all-stats", "data"),
    Input("submit", "n_clicks"),
    State("game-name", "value"),
    State("tag-line", "value"),
    prevent_initial_call=True
)
def fetch_data(_, game_name, tag_line):
    if not game_name or not tag_line:
        return dash.no_update

    account = get_account_by_riot_id(game_name, tag_line)
    if not account:
        return {"error": "Joueur introuvable."}

    summoner = get_summoner_by_puuid(account["puuid"])
    if not summoner:
        return {"error": "Erreur Récup. Summoner"}

    match_ids = get_match_ids(account["puuid"], count=30)
    all_stats = []
    for match_id in match_ids:
        match = get_match_data(match_id)
        if not match:
            continue
        duration = match["info"].get("gameDuration", 0)
        for player in match["info"]["participants"]:
            if player["puuid"] == account["puuid"]:
                player["gameDuration"] = duration
                player["match_id"] = match_id
                all_stats.append(player)

    return all_stats if all_stats else {"error": "Aucun match trouvé."}

@app.callback(
    Output("main-content", "children"),
    Input("all-stats", "data")
)
def update_main_content(data):
    if not data or isinstance(data, dict):
        return ""

    return dbc.Row([
        dbc.Col([
            html.H4("Historique des matchs"),
            html.Div(id="match-history"),
            dbc.Row([
                dbc.Col(dbc.Button("⬅️", id="prev-page", color="secondary", className="w-100"), width=2),
                dbc.Col(html.Div(id="page-info", className="text-center"), width=8),
                dbc.Col(dbc.Button("➡️", id="next-page", color="secondary", className="w-100"), width=2),
            ], className="mt-3")
        ], width=5),

        dbc.Col([
            html.Div(id="stats-output")
        ], width=7)
    ])

@app.callback(
    Output("stats-output", "children"),
    Input("all-stats", "data")
)
def display_stats(data):
    if not data:
        return ""
    if isinstance(data, dict) and "error" in data:
        return dbc.Alert(data["error"], color="danger")

    total = len(data)
    wins = sum(p["win"] for p in data)
    avg_kda = sum((p["kills"] + p["assists"]) / max(1, p["deaths"]) for p in data) / total
    avg_cs = sum(p["totalMinionsKilled"] + p["neutralMinionsKilled"] for p in data) / total
    avg_vision = sum(p["visionScore"] for p in data) / total

    top_champs = Counter(p["championName"] for p in data).most_common(3)

    cards = dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Winrate"),
            dbc.CardBody(html.H5(f"{wins / total * 100:.1f}%"))
        ])),
        dbc.Col(dbc.Card([
            dbc.CardHeader("KDA moyen"),
            dbc.CardBody(html.H5(f"{avg_kda:.2f}"))
        ])),
        dbc.Col(dbc.Card([
            dbc.CardHeader("CS moyen"),
            dbc.CardBody(html.H5(f"{avg_cs:.1f}"))
        ])),
        dbc.Col(dbc.Card([
            dbc.CardHeader("Vision moyenne"),
            dbc.CardBody(html.H5(f"{avg_vision:.1f}"))
        ])),
    ], className="mb-4")

    champs = [
        html.Div([
            html.Img(src=f"https://ddragon.leagueoflegends.com/cdn/14.12.1/img/champion/{name}.png", width="36",
                     style={"marginRight": "10px", "borderRadius": "4px"}),
            html.Span(f"{name} ({count} games)")
        ], style={"display": "flex", "alignItems": "center", "marginBottom": "10px"})
        for name, count in top_champs
    ]

    return [cards, html.H4("Champions joués"), html.Div(champs)]

@app.callback(
    Output("match-history", "children"),
    Output("page-info", "children"),
    Input("all-stats", "data"),
    Input("current-page", "data")
)
def update_history(data, page):
    if not data or isinstance(data, dict):
        return "", ""

    per_page = 10
    total_pages = (len(data) + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    subset = data[start:end]

    blocks = []
    for p in subset:
        champ = p["championName"]
        champ_icon = f"https://ddragon.leagueoflegends.com/cdn/14.12.1/img/champion/{champ}.png"
        result = "Victoire" if p["win"] else "Défaite"
        result_color = "#4CAF50" if p["win"] else "#FF5555"
        kda = (p["kills"] + p["assists"]) / max(1, p["deaths"])
        cs = p["totalMinionsKilled"] + p["neutralMinionsKilled"]
        vision = p["visionScore"]
        duration = p.get("gameDuration", 0)
        duration_str = f"{duration // 60}m {duration % 60}s"
        duration_min = max(1, duration // 60)
        cs_per_min = cs // duration_min
        vision_per_min = vision // duration_min

        blocks.append(html.Div([
            html.Div([
                html.Img(src=champ_icon, style={"width": "48px", "marginRight": "12px", "borderRadius": "8px"}),
                html.Div([
                    html.Strong(f"{champ} — {result}", style={"color": result_color}),
                    html.Br(),
                    html.Span(f"KDA : {p['kills']}/{p['deaths']}/{p['assists']} ({kda:.2f})"), html.Br(),
                    html.Span(f"CS : {cs} ({cs_per_min}) | Vision : {vision} ({vision_per_min}) | Durée : {duration_str}")
                ])
            ], style={"display": "flex", "alignItems": "center"})
        ], style={"border": "1px solid #ddd", "borderRadius": "10px", "padding": "10px",
                  "marginBottom": "10px", "backgroundColor": "#fff"}))

    return blocks, f"Page {page} / {total_pages}"

@app.callback(
    Output("current-page", "data"),
    Input("prev-page", "n_clicks"),
    Input("next-page", "n_clicks"),
    State("current-page", "data"),
    State("all-stats", "data"),
    prevent_initial_call=True
)
def paginate(prev_clicks, next_clicks, current_page, data):
    ctx = dash.callback_context
    if not ctx.triggered or isinstance(data, dict):
        return current_page
    total_pages = (len(data) + 9) // 10

    if ctx.triggered_id == "prev-page" and current_page > 1:
        return current_page - 1
    elif ctx.triggered_id == "next-page" and current_page < total_pages:
        return current_page + 1
    return current_page

if __name__ == "__main__":
    app.run(debug=True)