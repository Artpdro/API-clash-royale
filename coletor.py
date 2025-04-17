import requests
import json
from urllib.parse import quote
from pymongo import MongoClient
import time

CLAN_TAG     = "#QYGYYPYC"
MONGO_URI    = "mongodb+srv://admin:admin@cluster0.sargdmz.mongodb.net/"
RATE_LIMIT   = 1.0
BATTLE_LIMIT = 3

headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjAxZDFiZjA2LTQxMzgtNDMwNy04Y2EzLTgzZTk1NWRmZDQyMSIsImlhdCI6MTc0NDkyNjg2MCwic3ViIjoiZGV2ZWxvcGVyLzJhNzRiOWNhLTUzMTEtNzZkNi01ZDlkLWUxZTZhOTdkY2I5NSIsInNjb3BlcyI6WyJyb3lhbGUiXSwibGltaXRzIjpbeyJ0aWVyIjoiZGV2ZWxvcGVyL3NpbHZlciIsInR5cGUiOiJ0aHJvdHRsaW5nIn0seyJjaWRycyI6WyIxNDMuMjA4LjEyOC4xMTYiXSwidHlwZSI6ImNsaWVudCJ9XX0.O6KN6B21CuFGF3ioF5b4-_ka-sUov3p7bjmjD_Qpwf6GqeVn45ToShBBxHTooFTJXZMxgJWIUjMoq2lOsemSWQ'
}

# ENDPOINTS
URL_CLAN_MEMBERS = 'https://api.clashroyale.com/v1/clans/{tag}/members'
URL_PLAYER        = 'https://api.clashroyale.com/v1/players/{tag}'
URL_BATTLELOG     = 'https://api.clashroyale.com/v1/players/{tag}/battlelog'
URL_CARDS         = 'https://api.clashroyale.com/v1/cards'

client = MongoClient(MONGO_URI)
db = client['clashroyale']
col_players = db['players']
col_battles = db['battles']
col_cards   = db['cards']

col_players.create_index('tag', unique=True)
col_battles.create_index([('battleTime', 1), ('playerTag', 1)], unique=True)
col_cards.create_index('id', unique=True)


def fetch_clan_members(clan_tag):
    tag_enc = quote(clan_tag, safe='')
    resp = requests.get(URL_CLAN_MEMBERS.format(tag=tag_enc), headers=headers)
    resp.raise_for_status()
    return resp.json().get('items', [])

def fetch_player_profile(player_tag):
    tag_enc = quote(player_tag, safe='')
    resp = requests.get(URL_PLAYER.format(tag=tag_enc), headers=headers)
    resp.raise_for_status()
    return resp.json()

def fetch_player_battlelog(player_tag):
    tag_enc = quote(player_tag, safe='')
    resp = requests.get(URL_BATTLELOG.format(tag=tag_enc), headers=headers)
    resp.raise_for_status()
    return resp.json()

def fetch_all_cards():
    resp = requests.get(URL_CARDS, headers=headers)
    resp.raise_for_status()
    return resp.json().get('items', [])


def save_all_data():
    print("coletando cartas...")
    cards = fetch_all_cards()
    print("Resposta da API (primeiras 2 cartas):")
    print(cards[:2]) 

    if cards:
        for card in cards:
            col_cards.replace_one({'id': card['id']}, card, upsert=True)
        print(f"✅ {len(cards)} cartas salvas na coleção 'cards'.")
    else:
        print("⚠️ Nenhuma carta recebida da API.")

    members = fetch_clan_members(CLAN_TAG)
    print(f"\n🔍 {len(members)} membros encontrados no clã {CLAN_TAG}")

    for m in members:
        tag = m['tag']
        print(f"\n📥 Coletando dados do jogador {tag}...")

        profile = fetch_player_profile(tag)
        profile['playerTag'] = tag
        col_players.replace_one({'tag': tag}, profile, upsert=True)

        battles = fetch_player_battlelog(tag)[:BATTLE_LIMIT]
        for battle in battles:
            battle['playerTag'] = tag
            col_battles.replace_one(
                {'battleTime': battle['battleTime'], 'playerTag': tag},
                battle,
                upsert=True
            )
        print(f"✅ {len(battles)} batalhas salvas para {tag}")
        time.sleep(RATE_LIMIT)

    client.close()
    print("\n Finalizado com sucesso.")

if __name__ == '__main__':
    save_all_data()
