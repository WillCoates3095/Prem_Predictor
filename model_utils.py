from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier

from api_utils import *


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

    # Train a Random Forest Classifier
    model = RandomForestClassifier(random_state=42)
    model.fit(X_train, Y_train)

    # Make predictions
    Y_pred = model.predict(X_test)

    # Predict the outcome for a new match
    if leeds_team_id:
        next_game_stats = fetch_next_game(leeds_team_id)
        if next_game_stats:
            #Use stats from upcoming game
            opponent_stat = next_game_stats[0]["opponent_stat"]
            team_stat = next_game_stats[0]["team_stat"]
            new_match = pd.DataFrame({'team_stat': [team_stat], 'opponent_stat': [opponent_stat]})

            predicted_result = model.predict(new_match)
            print(
                f"Predicted Result for Next Match: {'Win' if predicted_result[0] == 1 else 'Draw' if predicted_result[0] == 2 else 'Loss'}")
        else:
            print("No upcoming game stats available for prediction.")
    else:
        print("No team ID available for prediction.")

    # Evaluate the model
    accuracy = accuracy_score(Y_test, Y_pred)
    print(f"Model Accuracy: {accuracy * 100:.2f}%")

else:
    print("No data available for training.")