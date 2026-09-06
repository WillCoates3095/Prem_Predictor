import os
import glob
import requests
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier

from api_utils import *

# Player Stats for last 5 games
data = {
    'player_id': [1, 1, 1, 1, 1],
    'game_id': [101, 102, 103, 104, 105],
    'fouls': [1, 1, 1, 0, 1],
    'goals': [0, 1, 0, 0, 1]
}

df = pd.DataFrame(data)

# Calculate stats for last 5 games
df['foul_percentage'] = df['fouls'].rolling(5).mean() * 100
df['goal_percentage'] = df['goals'].rolling(5).mean() * 100

print(df)

# Fetch team stats from the API
leeds_team_id = fetch_team_stats()
if leeds_team_id:
    previous_games = fetch_next_game(leeds_team_id)

    if previous_games:
        # Populate match_data dynamically
        match_data = {
            "team_stat": [game["team_stat"] for game in previous_games],
            "opponent_stat": [game["opponent_stat"] for game in previous_games],
            "result": [game["result"] for game in previous_games]
        }
        match_df = pd.DataFrame(match_data)
        print("Match DataFrame populated with previous games:\n", match_df)
    else:
        print("No previous games found to populate match_data.")
        match_df = pd.DataFrame(columns=["team_stat", "opponent_stat", "result"])
else:
    print("Failed to fetch team stats.")
    match_df = pd.DataFrame(columns=["team_stat", "opponent_stat", "result"])

# Ensure match_df is defined before using it
if not match_df.empty:
    # Proceed with training and predictions
    X = match_df[['team_stat', 'opponent_stat']]
    Y = match_df['result']

    # Train/test split
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

    # Combine player stats and match stats
    player_stats = df[['foul_percentage', 'goal_percentage']].iloc[-1]
    team_stats = {'team_stat': 3, 'opponent_stat': 2}  # Example team stats for the upcoming match
    combined_stats = {**team_stats, **player_stats.to_dict()}
    print("Combined Stats", combined_stats)

    # Visualization
    plt.bar(['Fouls', 'Goals'], [combined_stats['foul_percentage'], combined_stats['goal_percentage']])
    plt.title("Player Stats for Last 5 Games")
    plt.ylabel("Percentage")
    # plt.show()

    # Train a Random Forest Classifier
    model = RandomForestClassifier(random_state=42)
    model.fit(X_train, Y_train)

    # Make predictions
    Y_pred = model.predict(X_test)

    # Evaluate the model
    accuracy = accuracy_score(Y_test, Y_pred)
    print(f"Model Accuracy: {accuracy * 100:.2f}%")

    # Predict the outcome for a new match
    new_match = pd.DataFrame({'team_stat': [3], 'opponent_stat': [1]})
    predicted_result = model.predict(new_match)

    print("Predicted Result for New Match:", "Win" if predicted_result[0] == 1 else "Loss")
else:
    print("No data available for training.")

# Main program execution starts here -- all of the above ideally another file
print(fetch_team_stats())
print(fetch_next_game(fetch_team_stats()))