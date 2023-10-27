import csv, json, os, math, datetime
from datetime import datetime

with open('players.json', 'r') as players_file:
    players = json.load(players_file)

# my_players = set()
# with open('myplayers.csv', 'r') as my_players_file:
#     for row in csv.DictReader(my_players_file):
#         my_players.add(row['player'])

roster_data = None
with open('roster.json', 'r') as roster_file:
    roster_data = json.load(roster_file) 

players_data = []

player_position_map = {
    1: 'QB',
    2: 'RB',
    3: 'WR',
    4: 'TE',
    5: 'K'
}

players = [p for p in players if p['defaultPositionId'] in player_position_map.keys()]

scoring_period = 7
game_stats_map = {}
current_session_year = 2023

for player in players:
    
    roster_name = ''
    roster_abbrev = ''

    roster = [roster[1] for roster in list(roster_data.items()) if player['id'] in roster[1]['players']]

    if len(roster) > 0:
        roster_name = roster[0]['name']
        roster_abbrev = roster[0]['abbrev']
    if len(roster) > 1:
        raise Exception("can't be rostered > 1")

    playerId = player['id']

    position_label = player_position_map[player['defaultPositionId']]
    ownership = player['ownership']['percentOwned']

    player_info_path = f"./players/{playerId}/{current_session_year}/{scoring_period}/playerinfo.json"
    projection_path = f"./players/{playerId}/{current_session_year}/projections.json"
    game_log_path = f"./players/{playerId}/{current_session_year}/gamelog.json"

    projection_data = None
    if os.path.exists(projection_path):
        with open(projection_path, 'r') as projection_file:
            projection_data = json.load(projection_file)

    with open(player_info_path, 'r') as player_info_file:
        player_info = json.load(player_info_file)

    with open(game_log_path, 'r') as game_log_file:
        game_log = json.load(game_log_file)

    players_list = [p for p in player_info['players'] if p['id'] == playerId]

    if len(players_list) == 0:
        raise Exception("No player data")

    player_data = players_list[0]['player']

    ownership = player_data['ownership']
    for stat in player_data['stats']:
        if stat['seasonId'] not in game_stats_map:
            game_stats_map[stat['seasonId']] = {}
        game_stats_map[stat['seasonId']][stat['scoringPeriodId']] = stat

    player_row_data = {
        'position': position_label,
        'roster_abbrev': roster_abbrev,
        'name': player['fullName'],
        'id': playerId,
        'roster': roster_name, 
        'proTeamId': player['proTeamId'],
        'percentOwned': ownership['percentOwned'],
        'percentStarted': ownership['percentStarted'],
        'averageDraftPosition': ownership['averageDraftPosition']
    }

    for game in range(1, 8):
        player_row_data[f'game_{game}'] = round(game_stats_map[2023][game]['appliedTotal'], 2)
        player_row_data[f'proj_{game}'] = ''
        player_row_data[f'err_{game}'] = ''

        if projection_data is None or 'events' not in game_log:
            continue

        matched_events = [e[1] for e in list(iter(game_log['events'].items())) if e[1]['week'] == game]
        if len(matched_events) == 0:
            continue
        event = matched_events[0]
        # 2023-09-10T20:25:00.000+00:00
        game_date = datetime.strptime(event['gameDate'], '%Y-%m-%dT%H:%M:%S.000+00:00')
        # 2023-10-23 00:00:00.000000

        projection_dates = [p for p in projection_data if datetime.strptime(p['DATA_TIMESTAMP'], '%Y-%m-%d 00:00:00.000000') < game_date]
        
        # some players a missing projections for some dates ? ...
        if len(projection_dates) == 0:
            continue

        projection_before_game = projection_dates[len(projection_dates)-1]

        player_row_data[f'proj_{game}'] = round(projection_before_game['SCORE_PROJECTION'], 3)
        
        # error = (actual) - (projected)
        player_row_data[f'err_{game}'] = round(game_stats_map[2023][game]['appliedTotal'], 2) - round(projection_before_game['SCORE_PROJECTION'], 3)
        pass

    injuredStatus = 'ACTIVE'
    if 'injuryStatus' in player_data:
        injuredStatus = player_data['injuryStatus']

    player_row_data[f'week_{scoring_period}_status'] = injuredStatus
    player_row_data[f'week_{scoring_period}_injured'] = player_data['injured']

    players_data.append(player_row_data)

csv_writer = None
with open('players.csv', 'w') as players_file:
    for player in players_data:
        if csv_writer is None:
            csv_writer = csv.DictWriter(players_file, player.keys())
            csv_writer.writeheader()

        csv_writer.writerow(player)