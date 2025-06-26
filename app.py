import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from collections import Counter
import plotly.graph_objects as go

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
    html.H1("🏆 Winalyze 🏆", className="text-center my-4"),

    dbc.Row([
        dbc.Col(dbc.Input(id="game-name", placeholder="Nom Riot ID", type="text"), width=6),
        dbc.Col(dbc.Input(id="tag-line", placeholder="Tagline (ex: EUW)", type="text"), width=3),
        dbc.Col(dbc.Button("Analyser", id="submit", color="primary", className="w-100"), width=3)
    ], className="mb-4"),

    dcc.Loading(
        id="loading-analyse",
        type="default",
        children=[
            html.Div(id="main-content"),
            html.Div(id="stats-output")
        ],
        style={"width": "100%"}
    ),
    html.Div(id="stats-output"),

    dcc.Store(id="all-stats"),
    dcc.Store(id="current-page", data=1),
    dcc.Store(id="selected-rank", data="Gold")
], fluid=True)

# === Callback pour charger les données ===
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
    match_ids = get_match_ids(account["puuid"], count=50)
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

# === Contenu principal (match history + stats) ===
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
        dbc.Col(html.Div(id="stats-output"), width=7)
    ])

# === Sélection de rang pour comparaison ===
@app.callback(
    Output("selected-rank", "data"),
    Input("rank-selector", "value"),
    prevent_initial_call=True
)
def update_rank(rank):
    return rank

# === Affichage des statistiques ===
@app.callback(
    Output("stats-output", "children"),
    Input("all-stats", "data"),
    Input("selected-rank", "data")
)
def display_stats(data, selected_rank):
    if not data:
        return ""
    if isinstance(data, dict) and data.get("error"):
        return dbc.Alert(data["error"], color="danger")

    # Calculs principaux
    total = len(data)
    wins = sum(p["win"] for p in data)
    avg_kda = sum((p["kills"] + p["assists"]) / max(1, p["deaths"]) for p in data) / total
    total_cs = sum(p["totalMinionsKilled"] + p["neutralMinionsKilled"] for p in data)
    total_minutes = sum(p.get("gameDuration", 0) for p in data) / 60
    avg_cs = total_cs / total
    farming_per_min = total_cs / max(1, total_minutes)
    avg_vision_per_min = sum(p["visionScore"] / max(1, p.get("gameDuration", 0) / 60) for p in data) / total
    avg_objectives = sum(p.get("dragonKills", 0) + p.get("heraldKills", 0) + p.get("baronKills", 0) for p in data) / total

    # Références par rang
    rank_avg_stats = {
        "Iron":       {"KDA":2.0, "CS/min":5.0, "Vision/min":0.1, "Objectifs/game":0.3},
        "Bronze":     {"KDA":2.2, "CS/min":5.5, "Vision/min":0.2, "Objectifs/game":0.4},
        "Silver":     {"KDA":2.5, "CS/min":6.0, "Vision/min":0.4, "Objectifs/game":0.45},
        "Gold":       {"KDA":2.8, "CS/min":6.5, "Vision/min":0.7, "Objectifs/game":0.5},
        "Platinum":   {"KDA":3.0, "CS/min":7.0, "Vision/min":0.8, "Objectifs/game":0.6},
        "Emeraude":   {"KDA":3.2, "CS/min":7.2, "Vision/min":0.9, "Objectifs/game":0.7},
        "Diamond":    {"KDA":3.5, "CS/min":7.5, "Vision/min":1.1, "Objectifs/game":0.7},
        "Master":     {"KDA":4.0, "CS/min":8.0, "Vision/min":1.5, "Objectifs/game":0.8},
        "Grandmaster":{"KDA":4.5, "CS/min":8.5, "Vision/min":1.6, "Objectifs/game":0.9},
        "Challenger": {"KDA":5.0, "CS/min":9.0, "Vision/min":1.7, "Objectifs/game":1.0},
    }
    metric_max = {"KDA":10, "CS/min":10, "Vision/min":3, "Objectifs/game":3}
    avg_ref = rank_avg_stats.get(selected_rank, rank_avg_stats["Gold"] )

    # Dropdown comparatif
    dropdown = html.Div([
        html.Label("Comparer au rang :", style={"fontWeight":"bold"}),
        dcc.Dropdown(
            id="rank-selector",
            options=[{"label": r, "value": r} for r in rank_avg_stats],
            value=selected_rank,
            clearable=False,
            style={"marginTop":"8px"}
        )
    ], style={"marginBottom":"20px", "width":"60%"})

    # Radar
    categories = ["KDA","CS/min","Vision/min","Objectifs/game"]
    normalized_player = [
        min(10, avg_kda/metric_max["KDA"]*10),
        min(10, farming_per_min/metric_max["CS/min"]*10),
        min(10, avg_vision_per_min/metric_max["Vision/min"]*10),
        min(10, avg_objectives/metric_max["Objectifs/game"]*10)
    ]
    ref_vals = [avg_ref[k] for k in categories]
    normalized_ref = [
        min(10, ref_vals[0]/metric_max["KDA"]*10),
        min(10, ref_vals[1]/metric_max["CS/min"]*10),
        min(10, ref_vals[2]/metric_max["Vision/min"]*10),
        min(10, ref_vals[3]/metric_max["Objectifs/game"]*10)
    ]
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(r=normalized_player, theta=categories, fill='toself', name='Vous', line=dict(color='blue')))
    fig_radar.add_trace(go.Scatterpolar(r=normalized_ref,    theta=categories, fill='toself', name='Moyenne', line=dict(color='gray')))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,10])), showlegend=True,
                            height=300, margin=dict(t=30,b=30,l=30,r=30),
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    radar = html.Div([dcc.Graph(figure=fig_radar, config={"displayModeBar":False}, style={"height":"300px"})], style={"marginBottom":"20px"})

    # Carte Winrate
    winrate_pct = wins/total*100
    wins_losses_txt = f"{wins} W - {total-wins} L"
    fig_gauge = go.Figure(go.Indicator(mode="gauge+number", value=winrate_pct,
        number={'suffix':'%','font':{'size':22,'color':'#003366'}},
        gauge={'shape':'angular','axis':{'range':[0,100],'visible':False},
               'bar':{'color':'#007bff','thickness':0.3}, 'bgcolor':'rgba(0,0,0,0)',
               'steps':[{'range':[0,winrate_pct],'color':'#007bff'},{'range':[winrate_pct,100],'color':'#ff4d4d'}]},
        title={'text':wins_losses_txt,'font':{'size':22,'color':'#003366','family':'Arial'}}
    ))
    fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',margin=dict(t=20,b=10,l=10,r=10))
    metric_row = dbc.Row([
    # -- Carte Winrate --
    dbc.Col(
        dbc.Card([
            dbc.CardHeader(
                "Winrate",
                style={"textAlign": "center", "fontWeight": "bold", "fontSize": "1.4rem"}
            ),
            dbc.CardBody(
                dcc.Graph(
                    figure=fig_gauge,
                    config={"displayModeBar": False},
                    style={"height": "150px", "marginTop": "10px"}  # on remet marginTop et 150px
                ),
                style={
                    "padding": "0.75rem",
                    "height": "150px",              # même hauteur que les autres cartes
                    "display": "flex",
                    "flexDirection": "column",      # header en haut, graph en dessous
                    "justifyContent": "flex-start"  # pousse le graph vers le bas via marginTop
                }
            )
        ]),
        width=3
    ),

    # -- KDA moyen --
    dbc.Col(
        dbc.Card([
            dbc.CardHeader("KDA moyen", style={"fontSize": "1.4rem"}),
            dbc.CardBody(
                html.H2(f"{avg_kda:.2f}", style={
                    "fontWeight": "bold",
                    "textAlign": "center",
                    "margin": "auto",
                    "color": "#dc3545" if avg_kda < avg_ref["KDA"] else "#28a745"
                }),
                style={
                    "height": "150px",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "center"
                }
            )
        ]),
        width=3
    ),

    # -- CS moyen --
    dbc.Col(
        dbc.Card([
            dbc.CardHeader("CS moyen", style={"fontSize": "1.4rem"}),
            dbc.CardBody(
                html.H2(f"{avg_cs:.1f}", style={
                    "fontWeight": "bold",
                    "textAlign": "center",
                    "margin": "auto",
                    "color": "#dc3545" if avg_cs < avg_ref["CS/min"] else "#28a745"
                }),
                style={
                    "height": "150px",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "center"
                }
            )
        ]),
        width=3
    ),

    # -- Vision par min --
    dbc.Col(
        dbc.Card([
            dbc.CardHeader("Vision par min", style={"fontSize": "1.4rem"}),
            dbc.CardBody(
                html.H2(f"{avg_vision_per_min:.2f}", style={
                    "fontWeight": "bold",
                    "textAlign": "center",
                    "margin": "auto",
                    "color": "#dc3545" if avg_vision_per_min < avg_ref["Vision/min"] else "#28a745"
                }),
                style={
                    "height": "150px",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "center"
                }
            )
        ]),
        width=3
    ),
], className="mb-4")


    # === Deux colonnes champions ===
    played_counts = Counter(p["championName"] for p in data)
    top_played = []
    for champ, count in played_counts.most_common(3):
        wins_c = sum(1 for p in data if p["championName"] == champ and p["win"])
        winrate_c = wins_c / count if count else 0
        top_played.append((champ, count, wins_c, winrate_c))
    winrate_list = [
        (
            champ,
            count,
            sum(1 for p in data if p["championName"] == champ and p["win"]),
            sum(1 for p in data if p["championName"] == champ and p["win"]) / count
        )
        for champ, count in played_counts.items() if count >= 3
    ]
    top_winrate = sorted(winrate_list, key=lambda x: x[3], reverse=True)[:3]

    champions_section = dbc.Row([
        dbc.Col([
            html.H4("Top 3 – Plus joués", className="text-center"),
            html.Div([
                html.Div([
                    html.Img(src=f"https://ddragon.leagueoflegends.com/cdn/14.12.1/img/champion/{champ}.png",
                             width="36", style={"marginRight":"10px","borderRadius":"4px"}),
                    html.Span(f"{champ} — {wins_c}W/{count}J ({winrate_c*100:.1f}%)")
                ], style={"display":"flex","alignItems":"center","marginBottom":"8px"})
                for champ, count, wins_c, winrate_c in top_played
            ])
        ], width=6),
        dbc.Col([
            html.H4("Top 3 – Meilleur winrate", className="text-center"),
            html.Div([
                html.Div([
                    html.Img(src=f"https://ddragon.leagueoflegends.com/cdn/14.12.1/img/champion/{champ}.png",
                             width="36", style={"marginRight":"10px","borderRadius":"4px"}),
                    html.Span(f"{champ} — {wins_c}W/{count}J ({winrate_c*100:.1f}%)")
                ], style={"display":"flex","alignItems":"center","marginBottom":"8px"})
                for champ, count, wins_c, winrate_c in top_winrate
            ])
        ], width=6)
    ])

    return [
        html.Div(metric_row, style={"marginBottom": "20px"}),
        dropdown,
        radar,
        champions_section
    ]

@app.callback(
    Output("match-history", "children"),
    Output("page-info", "children"),
    Input("all-stats", "data"),
    Input("current-page", "data")
)
def update_history(data, page):
    # inchangé
    per_page = 10
    total_pages = (len(data) + per_page - 1) // per_page
    start = (page - 1) * per_page
    subset = data[start:start + per_page]
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
        duration_str = f"{duration//60}m {duration%60}s"
        duration_min = max(1, duration//60)
        cs_per_min = cs//duration_min
        vision_per_min = vision//duration_min
        blocks.append(html.Div([html.Div([html.Img(src=champ_icon, style={"width":"48px","marginRight":"12px","borderRadius":"8px"}), html.Div([html.Strong(f"{champ} — {result}", style={"color":result_color}), html.Br(), html.Span(f"KDA : {p['kills']}/{p['deaths']}/{p['assists']} ({kda:.2f})"), html.Br(), html.Span(f"CS : {cs} ({cs_per_min}) | Vision : {vision} ({vision_per_min}) | Durée : {duration_str}")])], style={"display":"flex","alignItems":"center"})], style={"border":"1px solid #ddd","borderRadius":"10px","padding":"10px","marginBottom":"10px","backgroundColor":"#fff"}))
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
    # inchangé
    ctx = dash.callback_context
    if not ctx.triggered or isinstance(data, dict):
        return current_page
    total_pages = (len(data) + 9) // 10
    if ctx.triggered_id == "prev-page" and current_page > 1:
        return current_page - 1
    if ctx.triggered_id == "next-page" and current_page < total_pages:
        return current_page + 1
    return current_page

if __name__ == "__main__":
    app.run(debug=True)
