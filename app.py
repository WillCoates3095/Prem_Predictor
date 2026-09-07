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

    print(previous_encounters, last_game_details)
    for match in previous_encounters:
        print(f"Home Team: {match.get('Home Team', 'N/A')}")
    previous_encounters_str = "\n".join([
        f"Leeds: {match.get('team_stat', 'N/A')} | {match.get('opponent_stat', 'N/A')}"
        f" : {opponent} |{'H' if match.get('home_team', 'N/A').strip().lower() in ['leeds united', 'leeds'] else 'A'}| Result: {match.get('result', 'N/A')}"
        for match in previous_encounters
    ])
    last_game_str = (
        f"{last_game_details.get('dateEvent', 'N/A')} | {last_game_details.get('strHomeTeam', 'N/A')} {last_game_details.get('intHomeScore', '-')} - {last_game_details.get('intAwayScore', '-')} {last_game_details.get('strAwayTeam', 'N/A')} at {last_game_details.get('strVenue','N/A')}" if last_game_details else "No last game details available."
    )

    return render_template_string('''
        <h1>Leeds United Match Prediction</h1>
        <h2>Next Game Details:</h2>
        <pre>{{ next_game_str }} </pre>
        <h2>Previous Encounters:</h2>
        <pre>{{ previous_encounters_str }}</pre>
        <h2>Prediction for Next Game:</h2>
        <pre>Prediction: {{ prediction }}</pre>
        <h2>Last Game Details:</h2>
        <pre>{{ last_game_str }}</pre>
    ''', prediction=prediction, next_game_str=next_game_str, previous_encounters_str=previous_encounters_str, last_game_str=last_game_str)

if __name__ == '__main__':
    app.run(debug=True)