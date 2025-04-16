import requests
import json
from urllib.parse import quote
from pymongo import MongoClient
import time

CLAN_TAG     = "#QYGYYPYC"            
MONGO_URI    = "mongodb+srv://admin:-@cluster0.sargdmz.mongodb.net/"  
RATE_LIMIT   = 1.0                      
BATTLE_LIMIT = 3                        

headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ='
}

URL_CLAN_MEMBERS = 'https://api.clashroyale.com/v1/clans/{tag}/members'
URL_PLAYER       = 'https://api.clashroyale.com/v1/players/{tag}'
URL_BATTLELOG    = 'https://api.clashroyale.com/v1/players/{tag}/battlelog'

client = MongoClient(MONGO_URI)
db = client['clashroyale']
col_players = db['players']
col_battles = db['battles']

col_players.create_index('tag', unique=True)
col_battles.create_index([('battleTime', 1), ('playerTag', 1)], unique=True)

def fetch_clan_members(clan_tag):
    tag_enc = quote(clan_tag, safe='')
    resp = requests.get(URL_CLAN_MEMBERS.format(tag=tag_enc), headers=headers)
    resp.raise_for_status()
    return resp.json().get('Items', [])

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


def save_all_data():
    members = fetch_clan_members(CLAN_TAG)
    print(f"Encontrados {len(members)} membros no clã {CLAN_TAG}")

    for m in members:
        tag = m['tag']
        profile = fetch_player_profile(tag)
        profile['playerTag'] = tag
        col_players.replace_one({'tag': tag}, profile, upsert=True)

        battles = fetch_player_battlelog(tag)[:BATTLE_LIMIT]
        for battle in battles:
            battle['playerTag'] = tag
            col_battles.replace_one(
                {'battleTime': battle['battleTime'], 
                 'playerTag': tag},
                battle,
                upsert=True
            )
        print(f"Dados salvos para {tag}: perfil + {len(battles)} ultimas batalhas.")
        time.sleep(RATE_LIMIT)

    client.close()

if __name__ == '__main__':
    save_all_data()
