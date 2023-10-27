import requests
import json, os

if not os.path.exists('players_info.json'):
    headers = {
        'X-Fantasy-Filter': '{"players":{"value":true}}'
    }
    players_data = requests.get('https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2023/segments/0/leaguedefaults/3?view=kona_player_info').json()
    with open('players_info.json', 'w') as players_file:
        json.dump(players_data, players_file)

# with open('players_info.json', 'r') as players_file:
#     players = json.load(players_file)