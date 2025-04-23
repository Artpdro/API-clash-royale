import requests
import json
from urllib.parse import quote
from pymongo import MongoClient
import time
from datetime import datetime, timezone

CLAN_TAG     = "#QYGYYPYC"
MONGO_URI    = "mongodb+srv://-:-@cluster0.sargdmz.mongodb.net/"
RATE_LIMIT   = 1.0
BATTLE_LIMIT = 3

headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer --'
}

URL_CLAN_MEMBERS = 'https://api.clashroyale.com/v1/clans/{tag}/members'
URL_PLAYER       = 'https://api.clashroyale.com/v1/players/{tag}'
URL_BATTLELOG    = 'https://api.clashroyale.com/v1/players/{tag}/battlelog'
URL_CARDS        = 'https://api.clashroyale.com/v1/cards'

def connect_db(uri):
    client = MongoClient(uri)
    db = client['clashroyale']
    return client, db

def fetch_clan_members(tag):
    resp = requests.get(URL_CLAN_MEMBERS.format(tag=quote(tag, safe='')), headers=headers)
    resp.raise_for_status()
    return resp.json().get('items', [])


def fetch_player_battlelog(tag):
    resp = requests.get(URL_BATTLELOG.format(tag=quote(tag, safe='')), headers=headers)
    resp.raise_for_status()
    return resp.json()[:BATTLE_LIMIT]


def fetch_all_cards():
    resp = requests.get(URL_CARDS, headers=headers)
    resp.raise_for_status()
    return resp.json().get('items', [])

def process_battle(battle, player_tag):
    dt = datetime.fromisoformat(battle['battleTime'].replace('Z', '+00:00'))

    formatted_date = dt.strftime('%Y/%m/%d')
    epoch_seconds = int(dt.replace(tzinfo=timezone.utc).timestamp())

    team_list = battle.get('team', [])
    opp_list = battle.get('opponent', [])
    team = team_list[0] if isinstance(team_list, list) and team_list else {}
    opp = opp_list[0] if isinstance(opp_list, list) and opp_list else {}

    trophies_player = team.get('startingTrophies', 0)
    trophies_opponent = opp.get('startingTrophies', 0)
    trophy_diff = abs(trophies_player - trophies_opponent)

    crowns_player = team.get('crowns', 0)
    crowns_opponent = opp.get('crowns', 0)

    if crowns_player > crowns_opponent:
        winner = player_tag
    elif crowns_player < crowns_opponent:
        winner = opp.get('tag')
    else:
        winner = None
        
        
        
    battle['date'] = formatted_date
    battle['timestampSeconds'] = epoch_seconds
    battle['trophyDifference'] = trophy_diff
    battle['towersDestroyed'] = crowns_player
    battle['winner'] = winner
    battle['playerTag'] = player_tag
    return battle

def save_cards(db):
    col_cards = db['cards']
    col_cards.create_index('id', unique=True)
    cards = fetch_all_cards()
    for card in cards:
        col_cards.replace_one({'id': card['id']}, card, upsert=True)
    print(f"✔️ {len(cards)} cartas salvas na coleção 'cards'.")




def save_data(clan_tag):
    client, db = connect_db(MONGO_URI)

    print("Coletando e salvando cartas...")
    save_cards(db)

    col_battles = db['battles']
    col_battles.create_index([('battleTime', 1), ('playerTag', 1)], unique=True)

    members = fetch_clan_members(clan_tag)
    print(f"Encontrados {len(members)} membros no clã {clan_tag}")

    for m in members:
        tag = m['tag']
        print(f"Processando batalhas de {tag}...")
        try:
            battles = fetch_player_battlelog(tag)
            processed = [process_battle(b, tag) for b in battles]

            for b in processed:
                col_battles.replace_one(
                    {'battleTime': b['battleTime'], 'playerTag': tag},
                    b,
                    upsert=True
                )
            print(f"✔️ {len(processed)} batalhas salvas para {tag}")
        except Exception as e:
            print(f"Erro ao processar {tag}: {e}")
        time.sleep(RATE_LIMIT)

    client.close()
    print("Concluído.")

if __name__ == '__main__':
    save_data(CLAN_TAG)
