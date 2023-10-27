import requests
import os
import json
import concurrent.futures
import csv

players = []
players_gamelog_map = {}

# delete players.json to refresh players
if not os.path.exists('players.json'):
    headers = {
        'X-Fantasy-Filter': '{"filterActive":{"value":true}}'
    }
    players_data = requests.get('https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2023/players?scoringPeriodId=0&view=players_wl', headers=headers).json()
    with open('players.json', 'w') as players_file:
        json.dump(players_data, players_file)

with open('players.json', 'r') as players_file:
    players = json.load(players_file)

my_players = set()
with open('myplayers.csv', 'r') as my_players_file:
    for row in csv.DictReader(my_players_file):
        my_players.add(row['player'])


# Positions
POS_QB = 1
POS_RB = 2
POS_WR = 3
POS_TE = 4
POS_K = 5

POS_COACH = 14

# how many seasons to search
seaons_lookback = 2

players = [p for p in players if p['defaultPositionId'] in [POS_QB, POS_RB, POS_WR, POS_TE, POS_K]]

player_count = len(players)
scoringPeriodId = 7

def fetch_player_game_log(player, i, total):
    try:
        position = player['defaultPositionId']
        # filter only QBs for now
        # if position != POS_QB:
        #     continue

        playerId = player['id']
        playerName = player['fullName']
        if playerName != "Deon Jackson":
            return

        # if playerName not in my_players:
        #     return

        print(f"[{i}/{player_count}] Fetching gamelog for player {playerId} {playerName} pos {position}")

        current_session = 2023
        for sessions_back in range(0, seaons_lookback):
            seasion  = current_session - sessions_back
            player_game_log_dir = f'./players/{playerId}/{seasion}/{scoringPeriodId}'
            os.makedirs(player_game_log_dir, exist_ok=True)

            game_log_path = f'./players/{playerId}/{seasion}/gamelog.json'
            if not os.path.exists(game_log_path):
                game_log_res = requests.get(f'https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/{playerId}/gamelog?region=us&lang=en&contentorigin=espn&season={seasion}', timeout=20)
                
                # players with less than the look back session count, will not have data
                if game_log_res.status_code != 200:
                    print(f"Game log info Neg status {game_log_res.status_code}")
                    break

                with open(game_log_path, 'w') as player_game_log_file:
                    json.dump(game_log_res.json(), player_game_log_file)

            game_log_path = f'./players/{playerId}/{seasion}/{scoringPeriodId}/playerinfo.json'
            if not os.path.exists(game_log_path):
                headers = {
                    'X-Fantasy-Filter': f'{{"players":{{"filterIds":{{"value":[{playerId}]}}}}}}'
                }
                game_log_res = requests.get(f'https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{seasion}/segments/0/leaguedefaults/3?view=kona_player_info', headers=headers, timeout=20)
                
                # players with less than the look back session count, will not have data
                if game_log_res.status_code != 200:
                    print(f"Player info Neg status {game_log_res.status_code}")
                    break

                with open(game_log_path, 'w') as player_game_log_file:
                    json.dump(game_log_res.json(), player_game_log_file)
            
            player_projection_log_path = f'./players/{playerId}/{seasion}/projections.json'
            if not os.path.exists(player_projection_log_path):
                # https://watsonfantasyfootball.espn.com/espnpartner/dallas/projections/projections_4360438_ESPNFantasyFootball_2023.json
                projections_res = requests.get(f'https://watsonfantasyfootball.espn.com/espnpartner/dallas/projections/projections_{playerId}_ESPNFantasyFootball_{seasion}.json')

                # players with less than the look back session count, will not have data
                if projections_res.status_code != 200:
                    print(f"Proj Neg status {projections_res.status_code}")
                    break

                with open(player_projection_log_path, 'w') as player_game_log_file:
                    projections = projections_res.json()
                    for projection in projections:
                        if 'SCORE_DISTRIBUTION' in projection:
                            projection['SCORE_DISTRIBUTION'] = None
                    
                    json.dump(projections, player_game_log_file)
            
    
        player_news_path = f'./players/{playerId}/{current_session}/news.json'
        if not os.path.exists(player_news_path):
            news_res = requests.get(f'https://site.api.espn.com/apis/fantasy/v2/games/ffl/news/players?days=180&playerId={playerId}')

            # players with less than the look back session count, will not have data
            if news_res.status_code != 200:
                print(f"News Neg status {news_res.status_code}")
                return

            with open(player_news_path, 'w') as player_news_file:
                news_feed = news_res.json()

                news_feed['feed'] = [n for n in news_feed['feed'] if n['type'] == 'Rotowire']

                json.dump(news_feed, player_news_file)
    
    except Exception as ex:
        print(ex)


# with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
#     futures = []
#     for i, player in enumerate(players):
#         futures.append(executor.submit(fetch_player_game_log, player=player, i=i, total=player_count))
#     for future in concurrent.futures.as_completed(futures):
#         future.result()

# must specify espn s2 cookie for league data
espn_s2 = 'AEAzfc0hgQc8YWbnkw0SDuM18ImHQi32dZM71CIN16daGGUsUpKPs9h0QDY37TKOgt92I1tW78gQAunZE%2FIXwagXu%2FuOr6E4kWeVkREpfdpetKm8QztfUODW3L1BYkXNzh7FM8TOwNeOYBXVq9LfSGCU9ILBOLsAcJSNgGHtx6CmuIYJ9M0nyuLjqsdfbeiw5Fhq8msJzK7JtA5LOwyi3TEFU8kLpJLYXrMPtTiaPTNe7C0vy2Qz%2Fueg9Har4Owre06t5qM2tivB%2BaNrJWGUfMeI2QfmSV3f3e43JvkmZECMOBAXPoPdkQdw9tY84%2BescUnjn%2BegT0jWx5BnJxgOm%2B07'
league_id = 1633152111 

cookies = {
    'espn_s2': espn_s2
}

league_res = requests.get(f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2023/segments/0/leagues/{league_id}?view=mSettings&view=mRoster&view=mTeam&view=modular&view=mNav", cookies=cookies)



if (league_res.status_code != 200):
    print(f"League Neg status {league_res.status_code}")
else:
    teamRoster = {}
    leagueData = league_res.json()
    for team in leagueData['teams']:
        teamRoster[team['name'].strip()] = { 'name': team['name'].strip(), 'abbrev': team['abbrev'], 'players': []}
        for rostered_player in team['roster']['entries']:
            teamRoster[team['name'].strip()]['players'].append(rostered_player['playerId'])

    with open('roster.json', 'w') as roster_file:
        json.dump(teamRoster, roster_file)