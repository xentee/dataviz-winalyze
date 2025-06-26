import os
import requests
from dotenv import load_dotenv
import urllib.parse

load_dotenv()
RIOT_API_KEY = os.getenv("RIOT_API_KEY")
HEADERS = {"X-Riot-Token": "RGAPI-b4245b8c-00fb-4bca-bd86-da1dbcb20849"}


def get_account_by_riot_id(game_name, tag_line):
    # Encode les espaces et caractères spéciaux
    game_name_enc = urllib.parse.quote(game_name)
    tag_line_enc = urllib.parse.quote(tag_line)

    url = f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name_enc}/{tag_line_enc}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        print(f"Erreur RiotID ({r.status_code}) → {r.text}")
        return None
    return r.json()


def get_summoner_by_puuid(puuid):
    url = f"https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        print(f"Erreur Summoner ({r.status_code}) → {r.text}")
        return None
    return r.json()


def get_match_ids(puuid, start=0, count=10):
    url = f"https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        print(f"Erreur MatchList ({r.status_code}) → {r.text}")
        return []
    return r.json()


def get_match_data(match_id):
    url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        print(f"Erreur MatchDetail ({r.status_code}) → {r.text}")
        return None
    return r.json()

def get_league_by_summoner_id(summoner_id):
    url = f"https://euw1.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        print(f"Erreur LeagueEntry ({r.status_code}) → {r.text}")
        return []
    return r.json()
