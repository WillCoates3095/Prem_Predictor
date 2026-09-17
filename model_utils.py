from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier

from api_utils import *

def get_previous_game_data():
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
            return match_df
        else:
            print("No previous games found to populate match_data.")
            match_df = pd.DataFrame(columns=["team_stat", "opponent_stat", "result"])
            return match_df
    else:
        print("Failed to fetch team stats.")
        match_df = pd.DataFrame(columns=["team_stat", "opponent_stat", "result"])
        return match_df



def generate_prediction(match_df):
    leeds_team_id = fetch_team_stats()
    WINDOW = 4
    if match_df.empty:
        print("No historical match data available.")
        return {
            "prediction": "N/A",
            "probabilities": {},
            "average_leeds_goals": 0,
            "average_opponent_goals": 0,
            "btts_percentage": 0,
            "over_under_stats": {},
            "leeds_points": 0,
            "opponent_points": 0,
            "points_difference": 0,
            "accuracy": 0,
            "feature_importance": {}
        }
    match_df = match_df.iloc[::-1].reset_index(drop=True)
    leeds_points = fetch_season_points()
    opponent = None
    if leeds_team_id:
        next_game_details = fetch_next_game_details(leeds_team_id)
        if next_game_details:
            opponent = next_game_details[1]
    if opponent:
        opponent_points = fetch_opponent_points(opponent)
    else:
        opponent_points = 0
    points_difference = leeds_points - opponent_points

    def calculate_features(previous_games):
        total_games = len(previous_games)
        if total_games == 0:
            return {
                "avg_goals_scored": 0,
                "avg_goals_conceded": 0,
                "win_percentage": 0,
                "draw_percentage": 0,
                "loss_percentage": 0,
                "btts_percentage": 0,
                "over_1_5_percentage": 0,
                "under_1_5_percentage": 0,
                "over_2_5_percentage": 0,
                "under_2_5_percentage": 0
            }
        wins = len(previous_games[previous_games["result"] == 1])
        draws = len(previous_games[previous_games["result"] == 2])
        losses = len(previous_games[previous_games["result"] == 0])
        btts_games = len(previous_games[(previous_games["team_stat"] > 0) & (previous_games["opponent_stat"] > 0)])
        total_goals = (previous_games["team_stat"] + previous_games["opponent_stat"])
        over_1_5_games = len(total_goals[total_goals > 1.5])
        under_1_5_games = len(total_goals[total_goals < 1.5])
        over_2_5_games = len(total_goals[total_goals > 2.5])
        under_2_5_games = len(total_goals[total_goals < 2.5])
        return {
            "avg_goals_scored": previous_games["team_stat"].mean(),
            "avg_goals_conceded": previous_games["opponent_stat"].mean(),
            "win_percentage": (wins / total_games) * 100,
            "draw_percentage": (draws / total_games) * 100,
            "loss_percentage": (losses / total_games) * 100,
            "btts_percentage": (btts_games / total_games) * 100,
            "over_1_5_percentage": (over_1_5_games / total_games) * 100,
            "under_1_5_percentage": (under_1_5_games / total_games) * 100,
            "over_2_5_percentage": (over_2_5_games / total_games) * 100,
            "under_2_5_percentage": (under_2_5_games / total_games) * 100
        }

    training_rows = []
    for i in range(1, len(match_df)):
        start_index = max(0, i - WINDOW)
        previous_games = match_df.iloc[start_index:i]
        current_game = match_df.iloc[i]
        features = calculate_features(previous_games)
        training_rows.append({
            "avg_goals_scored": features["avg_goals_scored"],
            "avg_goals_conceded": features["avg_goals_conceded"],
            "win_percentage": features["win_percentage"],
            "draw_percentage": features["draw_percentage"],
            "loss_percentage": features["loss_percentage"],
            "btts_percentage": features["btts_percentage"],
            "over_1_5_percentage": features["over_1_5_percentage"],
            "under_1_5_percentage": features["under_1_5_percentage"],
            "over_2_5_percentage": features["over_2_5_percentage"],
            "under_2_5_percentage": features["under_2_5_percentage"],
            "leeds_points": leeds_points,
            "opponent_points": opponent_points,
            "points_difference": points_difference,
            "result": current_game["result"]
        })
    training_df = pd.DataFrame(training_rows)
    print("Training Data:")
    print(training_df)
    print(f"Training rows: {len(training_df)}")
    # Feature columns for the Random Forest model
    feature_columns = [
        "avg_goals_scored",
        "avg_goals_conceded",
        "win_percentage",
        "draw_percentage",
        "loss_percentage",
        "btts_percentage",
        "over_1_5_percentage",
        "under_1_5_percentage",
        "over_2_5_percentage",
        "under_2_5_percentage",
        "leeds_points",
        "opponent_points",
        "points_difference"
    ]

    if len(training_df) < 2:
        print("Not enough historical data to train the Random Forest. Training rows: {len(training_df)}")
        return {
            "prediction": "N/A",
            "probabilities": {},
            "average_leeds_goals": match_df["team_stat"].mean(),
            "average_opponent_goals": match_df["opponent_stat"].mean(),
            "btts_percentage": calculate_features(match_df)["btts_percentage"],
            "over_under_stats": {
                "over_1.5": calculate_features(match_df)["over_1_5_percentage"],
                "under_1.5": calculate_features(match_df)["under_1_5_percentage"],
                "over_2.5": calculate_features(match_df)["over_2_5_percentage"],
                "under_2.5": calculate_features(match_df)["under_2_5_percentage"]
            },
            "leeds_points": leeds_points,
            "opponent_points": opponent_points,
            "points_difference": points_difference,
            "accuracy": 0,
            "feature_importance": {}
        }

    X = training_df[feature_columns]
    y = training_df["result"]
    model = RandomForestClassifier(n_estimators=200,random_state=42,max_depth=5,min_samples_split=2,min_samples_leaf=1)
    model.fit(X, y)
    training_predictions = model.predict(X)
    accuracy = accuracy_score(y, training_predictions) * 100
    print(f"Random Forest Training Accuracy: {accuracy:.2f}%")

    recent_games = match_df.tail(WINDOW)
    current_features = calculate_features(recent_games)
    prediction_data = pd.DataFrame([{
        "avg_goals_scored": current_features["avg_goals_scored"],
        "avg_goals_conceded": current_features["avg_goals_conceded"],
        "win_percentage": current_features["win_percentage"],
        "draw_percentage": current_features["draw_percentage"],
        "loss_percentage": current_features["loss_percentage"],
        "btts_percentage": current_features["btts_percentage"],
        "over_1_5_percentage": current_features["over_1_5_percentage"],
        "under_1_5_percentage": current_features["under_1_5_percentage"],
        "over_2_5_percentage": current_features["over_2_5_percentage"],
        "under_2_5_percentage": current_features["under_2_5_percentage"],
        "leeds_points": leeds_points,
        "opponent_points": opponent_points,
        "points_difference": points_difference
    }])
    prediction_value = model.predict(prediction_data)[0]
    class_probabilities = model.predict_proba(prediction_data)[0]
    probabilities = {}
    for class_value, probability in zip(
        model.classes_,
        class_probabilities
    ):
        if class_value == 1:
            result_name = "Win"
        elif class_value == 2:
            result_name = "Draw"
        elif class_value == 0:
            result_name = "Loss"
        else:
            result_name = str(class_value)
        probabilities[result_name] = round(
            probability * 100,
            2
        )
    if prediction_value == 1:
        prediction = "Win"
    elif prediction_value == 2:
        prediction = "Draw"
    elif prediction_value == 0:
        prediction = "Loss"
    else:
        prediction = str(prediction_value)
    # How important each feature is for the prediction
    feature_importance = dict(zip(feature_columns,model.feature_importances_))
    feature_importance = {key: round(value * 100, 2) for key, value in feature_importance.items()}
    over_under_stats = {
        "over_1.5": current_features["over_1_5_percentage"],
        "under_1.5": current_features["under_1_5_percentage"],
        "over_2.5": current_features["over_2_5_percentage"],
        "under_2.5": current_features["under_2_5_percentage"]
    }
    print(f"Prediction: {prediction}")
    print(f"Probabilities: {probabilities}")
    print(f"Feature Importance: {feature_importance}")
    return {
        "prediction": prediction,
        "probabilities": probabilities,
        "average_leeds_goals": current_features["avg_goals_scored"],
        "average_opponent_goals": current_features["avg_goals_conceded"],
        "btts_percentage": current_features["btts_percentage"],
        "over_under_stats": over_under_stats,
        "leeds_points": leeds_points,
        "opponent_points": opponent_points,
        "points_difference": points_difference,
        "accuracy": accuracy,
        "feature_importance": feature_importance
    }