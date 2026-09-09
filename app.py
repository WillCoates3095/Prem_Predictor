from flask import Flask, render_template_string
from model_utils import *
from api_utils import *

app = Flask(__name__)

@app.route('/')
def home():
    leeds_team_id = fetch_team_stats()
    prediction = generate_prediction(get_previous_game_data())
    next_game = None
    opponent = None
    previous_encounters =[]
    last_game_details = None
    if leeds_team_id:
        next_game, opponent = fetch_next_game_details(leeds_team_id)
        last_game_details=fetch_last_game(leeds_team_id)
        if opponent:
            previous_encounters = fetch_previous_games(opponent)
    next_game_str = (
        f"{next_game.get('strEvent', 'N/A')} on {next_game.get('dateEvent', 'N/A')} at {next_game.get('strVenue', 'N/A')}" if next_game else "No next game details available."
    )
    prediction_str = (f"Prediction: {prediction['prediction']} \nPercentages: "
                      f"\nWin: {prediction['probabilities']['Win']:.1f}% | Draw: {prediction['probabilities']['Draw']:.1f}% | Loss: {prediction['probabilities']['Loss']:.1f}%"
                      f"\nBTTS: {prediction['btts_percentage']}%\nOver 1.5 Goals: {prediction['over_under_stats']['over_1.5']}% "
                      f"| Under 1.5 Goals: {prediction['over_under_stats']['under_1.5']}% \nOver 2.5 Goals: {prediction['over_under_stats']['over_2.5']}%"
                      f" | Under 2.5 Goals: {prediction['over_under_stats']['under_2.5']}% ") \
        if prediction else "No prediction available."

    print(previous_encounters, last_game_details)
    for match in previous_encounters:
        print(f"Home Team: {match.get('Home Team', 'N/A')}")
    previous_encounters_str = "\n".join([
        f"Leeds: {match.get('team_stat', 'N/A')} | {match.get('opponent_stat', 'N/A')}"
        f" : {opponent} |{'H' if match.get('home_team', 'N/A').strip().lower() in ['leeds united', 'leeds'] else 'A'}| "
        f"Result: {'Win' if match.get('result', 'N/A') ==1 else 'Loss' if match.get('result', 'N/A') ==0 else 'Draw' if match.get('result', 'N/A') ==2 else 'N/A'}"
        for match in previous_encounters
    ])
    last_game_str = (
        f"{last_game_details.get('dateEvent', 'N/A')} | {last_game_details.get('strHomeTeam', 'N/A')} {last_game_details.get('intHomeScore', '-')} - {last_game_details.get('intAwayScore', '-')} {last_game_details.get('strAwayTeam', 'N/A')} at {last_game_details.get('strVenue', 'N/A')}"
        f"\nGoal Scorers: {last_game_details.get('goal_scorers', 'N/A')}" if last_game_details else "No last game details available."
    )
    table_standing_str = (
        f"Top 5 League Table:\n" + "\n".join(return_league_table())
        if return_league_table() else "No league table data available."
    )
    return render_template_string('''
        <h1>Leeds United Match Prediction</h1>
        <h2>Next Game Details:</h2>
        <pre>{{ next_game_str }} </pre>
        <h2>Previous Encounters:</h2>
        <pre>{{ previous_encounters_str }}</pre>
        <h2>Prediction for Next Game:</h2>
        <pre>{{ prediction }}</pre>
        <h2>Last Game Details:</h2>
        <pre>{{ last_game_str }}</pre>
        <h2>League Table Standing (Limited To Top 5):</h2>
        <pre>{{ table_standing_str }}</pre>
        <h2>Leeds Current Points:</h2>
        <pre>{{ leeds_current_points }}</pre>
    ''', prediction=prediction_str, next_game_str=next_game_str, previous_encounters_str=previous_encounters_str, last_game_str=last_game_str, table_standing_str=table_standing_str, leeds_current_points = fetch_season_points())

if __name__ == '__main__':
    app.run(debug=True)