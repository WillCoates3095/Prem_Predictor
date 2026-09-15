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
    if not match_df.empty:
        total_games = len(match_df)
        btts_games = len(match_df[(match_df['team_stat'] > 0) & (match_df['opponent_stat'] > 0)])
        btts_percentage = (btts_games / total_games) * 100
        leeds_wins = len(match_df[match_df['result'] == 1])
        draws = len(match_df[match_df['result'] == 2])
        leeds_losses = len(match_df[match_df['result'] == 0])
        average_leeds_goals = match_df['team_stat'].mean()
        average_opponent_goals = match_df['opponent_stat'].mean()
        leeds_points = fetch_season_points()
        opponent_points = fetch_opponent_points(fetch_next_game_details(leeds_team_id)[1])  # Fetch opponent points for the next game
        win_percentage = leeds_wins/total_games * 100
        draw_percentage = draws/total_games * 100
        loss_percentage = leeds_losses/total_games * 100
        over_15_percentage = (len(match_df[match_df['team_stat'] + match_df['opponent_stat'] > 1.5]) / total_games) * 100
        under_15_percentage = (len(match_df[match_df['team_stat'] + match_df['opponent_stat'] < 1.5]) / total_games) * 100
        over_25_percentage = (len(match_df[match_df['team_stat'] + match_df['opponent_stat'] > 2.5]) / total_games) * 100
        under_25_percentage = (len(match_df[match_df['team_stat'] + match_df['opponent_stat'] < 2.5]) / total_games) * 100

        over_under_stats = {
            "over_1.5": over_15_percentage,
            "under_1.5": under_15_percentage,
            "over_2.5": over_25_percentage,
            "under_2.5": under_25_percentage
        }

        print(f"Total Games: {total_games}\nLeeds Wins: {leeds_wins}\nDraws: {draws}\nLeeds Losses: {leeds_losses}")
        print(f"Average Leeds Goals: {average_leeds_goals}\nAverage Opponent Goals: {average_opponent_goals}")
        print(f"Win Percentage: {win_percentage:.2f}%\nDraw Percentage: {draw_percentage:.2f}%\nLoss Percentage: {loss_percentage:.2f}%")

        probabilites ={
            'Win': win_percentage + (leeds_points - opponent_points) * 1,  # 1% for every point difference in favor of Leeds
            'Draw': draw_percentage,
            'Loss': loss_percentage + (opponent_points - leeds_points) * 1  # 1% for every point difference in favor of the opponent
        }
        prediction = max(probabilites, key=probabilites.get)
        print(f"Predicted Outcome for Next Game: {prediction} with probabilities: {probabilites}")
        print("Prediction probabilities:")
        for outcome, probability in probabilites.items():
            print(f"{outcome}: {probability:.2f}%")

        return {
            "prediction": prediction, "probabilities": probabilites,"average_leeds_goals": average_leeds_goals,
            "average_opponent_goals": average_opponent_goals, "btts_percentage": btts_percentage, "over_under_stats": over_under_stats
        }
