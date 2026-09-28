from flask import Flask, render_template_string, render_template
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
    last_five_details = last_five_games()
    if leeds_team_id:
        next_game, opponent = fetch_next_game_details(leeds_team_id)
        last_game_details=fetch_last_game(leeds_team_id)
        if opponent:
            previous_encounters = fetch_previous_games(opponent)
    next_game_str = (
        f"{next_game.get('strEvent', 'N/A')} on {next_game.get('dateEvent', 'N/A')} at {next_game.get('strVenue', 'N/A')}" if next_game else "No next game details available."
    )
    try:
        prediction_str = (f"Prediction: {prediction['prediction']} \nPercentages: "
                          f"\nWin: {prediction['probabilities']['Win']:.1f}% | Draw: {prediction['probabilities']['Draw']:.1f}% | Loss: {prediction['probabilities']['Loss']:.1f}%"
                          f"\nBTTS: {prediction['btts_percentage']}%\nOver 1.5 Goals: {prediction['over_under_stats']['over_1.5']}% "
                          f"| Under 1.5 Goals: {prediction['over_under_stats']['under_1.5']}% \nOver 2.5 Goals: {prediction['over_under_stats']['over_2.5']}%"
                          f" | Under 2.5 Goals: {prediction['over_under_stats']['under_2.5']}% ") \
            if prediction else "No prediction available."
    except Exception as e:
        prediction_str = f"Error generating prediction: {str(e)}"
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
    last_five_games_str = ("\n".join(
                           f"Opponent: {match.get('opponent', 'N/A')}"
                           f" | Result: {match.get('result', 'N/A')}" 
                           f" | Score: {match.get('score', 'N/A')}"
                           f"| {match.get('home', 'N/A')}"
                           for match in last_five_details
                           ))

    league_table = return_league_table() or []
    return render_template(
        'index.html',
         next_game_str=next_game_str,
         opponent = opponent,
         opponent_points = fetch_opponent_points(opponent) if opponent else None,
         previous_encounters_str = previous_encounters_str,
         prediction = prediction,
         last_game_str = last_game_str,
         league_table = league_table,
         leeds_current_points = fetch_season_points(),
         last_five_games_str = last_five_games_str,
 )

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html', error=error), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)