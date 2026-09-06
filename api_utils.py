import requests
import glob
import pandas as pd
from django.db.models.expressions import result

API_KEY = '123'
BASE_URL = 'https://www.thesportsdb.com/api/v1/json'

def fetch_team_stats():
    # Example fetch team stats from the API
    team_name = 'Leeds United'
    search_team_url = f'{BASE_URL}/{API_KEY}/searchteams.php'
    response = requests.get(search_team_url, params={'t': team_name})

    if response.status_code == 200:
        team_data = response.json()
        if team_data['teams']:
            leeds_team_id = team_data['teams'][0]['idTeam']
            print(f"Leeds United Team ID: {leeds_team_id}")
            return leeds_team_id
        else:
            print("No team found.")
            return None
    else:
        print(f"Error: {response.status_code}")
        return None

def fetch_next_game(leeds_team_id):
    #Get Leeds next game
    if 'leeds_team_id' in locals():
        next_game_url = f'{BASE_URL}/{API_KEY}/eventsnext.php'
        response = requests.get(next_game_url, params={'id': leeds_team_id})

        if response.status_code == 200:
            next_game_data = response.json()
            print(next_game_data['events'][0])
            if next_game_data['events']:
                next_game = next_game_data['events'][0]
                opponent = next_game['strAwayTeam'] if next_game['idHomeTeam'] == leeds_team_id else next_game['strHomeTeam']
                fetch_last_game(leeds_team_id)
                print(f"Leeds United Next Game: {next_game['strEvent']} on {next_game['dateEvent']} at {next_game['strVenue']}\n")
                print("Fetching previous games agaist:", opponent)
                return fetch_previous_games(opponent)
            else:
                print("No upcoming games found.")
                return []
        else:
            print(f"Error: {response.status_code}")
            return  []

def fetch_last_game(leeds_team_id):
    #Get Leeds last game
    if 'leeds_team_id' in locals():
        last_game_url = f'{BASE_URL}/{API_KEY}/eventslast.php'
        response = requests.get(last_game_url, params={'id': leeds_team_id})

        if response.status_code == 200:
            last_game_data = response.json()
            if last_game_data['results']:
                last_game = last_game_data['results'][0]
                opponent = last_game['strAwayTeam'] if last_game['idHomeTeam'] == leeds_team_id else last_game['strHomeTeam']
                home_score = last_game['intHomeScore']
                away_score = last_game['intAwayScore']
                print(f"\nLeeds United Last Game: {last_game['strEvent']} on {last_game['dateEvent']} "
                      f"at {last_game['strVenue']} \nThe fulltime score was {home_score} - {away_score}")
            else:
                print("No previous games found.")
        else:
            print(f"Error: {response.status_code}")

def fetch_team_aliases(team_name):
    url = f"{BASE_URL}/{API_KEY}/searchteams.php"
    response = requests.get(url, params={"t": team_name})

    if response.status_code == 200:
        data = response.json()
        if data and "teams" in data and data["teams"]:
            team_info = data["teams"][0]
            aliases = [team_info["strTeam"]]
            if team_info.get("strAlternate"):
                aliases.extend(team_info["strAlternate"].split(", "))
            return aliases
        else:
            print(f"No team found.")
            return []
    else:
        print(f"Error fetching team aliases: {response.status_code}")

def fetch_previous_games(opponent):
    print(f"\nFetching aliases for {opponent}...")
    aliases = fetch_team_aliases(opponent)
    aliases.append(opponent.split()[0])
    print(f"Aliases found: {aliases}")
    print(f"Searching CSV files for all Leeds vs {opponent} matches...")
    csv_files = glob.glob("seasons/*.csv")

    all_matches = []
    for file in csv_files:
        print(f"Checking: {file}")
        try:
            season_df = pd.read_csv(file)
        except Exception as e:
            print(f"Could not read {file}: {e}")
            continue
        required_columns = [
            "strTimestamp",
            "Home Team",
            "Home Score",
            "Away Team",
            "Away Score"
        ]
        missing_columns = [
            column for column in required_columns
            if column not in season_df.columns
        ]
        if missing_columns:
            print(f"Skipping {file} - missing columns: {missing_columns}")
            continue
        home = season_df["Home Team"].astype(str)
        away = season_df["Away Team"].astype(str)
        # Search for matches using aliases
        matches = season_df[
            (
                home.str.contains("Leeds", case=False, na=False)
                &
                away.str.contains('|'.join(aliases), case=False, na=False)
            )
            |
            (
                home.str.contains('|'.join(aliases), case=False, na=False)
                &
                away.str.contains("Leeds", case=False, na=False)
            )
        ]
        if not matches.empty:
            print(f"Found {len(matches)} match(es) in {file}")
            all_matches.append(matches)

    if not all_matches:
        print(f"\nNo historical matches found between Leeds United and {opponent} in the CSV files.")
        return []
    all_matches_df = pd.concat(
        all_matches,
        ignore_index=True
    )
    # Convert timestamp to datetime
    all_matches_df["strTimestamp"] = pd.to_datetime(
        all_matches_df["strTimestamp"],
        errors="coerce"
    )
    # Remove rows with invalid dates
    all_matches_df = all_matches_df.dropna(
        subset=["strTimestamp"]
    )
    all_matches_df = all_matches_df.sort_values(
        "strTimestamp",
        ascending=False
    )
    match_data_list = []
    print()
    for _, match in all_matches_df.iterrows():
        team_stat = match['Home Score'] if match['Home Team'] == 'Leeds United' or match["Home Team"] == "Leeds" else match['Away Score']
        opponent_stat = match['Away Score'] if match['Home Team'] == 'Leeds United' or match["Home Team"] == "Leeds" else match['Home Score']
        if opponent_stat == team_stat:
            result = 2
        elif team_stat > opponent_stat:
            result = 1 #Win
        else:
            result = 0
        match_data_list.append({
            "team_stat": team_stat,
            "opponent_stat": opponent_stat,
            "result": result
        })
        print(
            f"{match['strTimestamp'].date()} | "
            f"{match['Home Team']} "
            f"{match['Home Score']} - "
            f"{match['Away Score']} "
            f"{match['Away Team']}"
        )
    print()
    return match_data_list
    #return all_matches_df
