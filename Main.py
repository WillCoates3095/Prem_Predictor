import os
import glob
import requests
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier

#API key and Base URL
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
            fetch_next_game(leeds_team_id)

        else:
            print("No team found.")
    else:
        print(f"Error: {response.status_code}")

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
                print(f"Leeds United Next Game: {next_game['strEvent']} on {next_game['dateEvent']} at {next_game['strVenue']}\n\n\n")

                print("Fetching previous games agaist:", opponent)
                fetch_previous_games(opponent)
            else:
                print("No upcoming games found.")
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
    else:
        print(f"Error fetching team aliases: {response.status_code}")
def fetch_previous_games(opponent):
    print(f"\nFetching aliases for {opponent}...")
    aliases = fetch_team_aliases(opponent)
    aliases.append(opponent.split()[0])
    print(f"Aliases found: {aliases}")

    print(f"\nSearching CSV files for all Leeds vs {opponent} matches...")

    # Find all CSV files in the seasons folder
    csv_files = glob.glob("seasons/*.csv")

    all_matches = []

    for file in csv_files:
        print(f"Checking: {file}")
        try:
            season_df = pd.read_csv(file)
        except Exception as e:
            print(f"Could not read {file}: {e}")
            continue

        # Ensure required columns exist
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

        # Convert team columns to strings
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
        return None

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
    for _, match in all_matches_df.iterrows():
        print(
            f"{match['strTimestamp'].date()} | "
            f"{match['Home Team']} "
            f"{match['Home Score']} - "
            f"{match['Away Score']} "
            f"{match['Away Team']}"
        )
    return all_matches_df
#Player Stats for last 5 games
data = {
    'player_id' : [1,1,1,1,1],
    'game_id' : [101,102,103,104,105],
    'fouls' : [1,1,1,0,1],
    'goals' : [0, 1, 0, 0,1]
}

df = pd.DataFrame(data)

# Calculate states for last 5 games
df['foul_percentage'] = df['fouls'].rolling(5).mean() * 100
df['goal_percentage'] = df['goals'].rolling(5).mean() * 100

print(df)

#Match Stats
match_data = {
    'team_stat': [1,2,3,4,5],
    'opponent_stat': [5,4,3,2,1],
    'result': [0,1,1,0,1]  # 0 = loss, 1 = win
}
match_df = pd.DataFrame(match_data)

#Split data into features and target variable
X = match_df[['team_stat', 'opponent_stat']]
Y = match_df['result']

#Train/test split
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

#Combine player stats and match stats
player_stats = df[['foul_percentage', 'goal_percentage']].iloc[-1]
team_stats = {'team_stat':3, 'opponent_stat':2}  # Example team stats for the upcoming match
combined_stats = {**team_stats, **player_stats.to_dict()}
print("Combined Stats", combined_stats)

#Visualisation
plt.bar(['Fouls','Goals'], [combined_stats['foul_percentage'], combined_stats['goal_percentage']])
plt.title("Player Stats for Last 5 Games")
plt.ylabel("Percentage")
#plt.show()

#Train a Random Forest Classifier
model = RandomForestClassifier(random_state=42)
model.fit(X_train, Y_train)

#Make predictions
Y_pred = model.predict(X_test)

#Evaluate the model
accuracy = accuracy_score(Y_test, Y_pred)
print(f"Model Accuracy: {accuracy * 100:.2f}%")

# Predict the outcome for a new match
new_match = pd.DataFrame({'team_stat': [3], 'opponent_stat': [1]})
predicted_result = model.predict(new_match)

print("Predicted Result for New Match:", "Win" if predicted_result[0] == 1 else "Loss")

fetch_team_stats()