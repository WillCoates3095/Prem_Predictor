from flask import Flask, render_template_string, render_template
from model_utils import *
from api_utils import *

app = Flask(__name__)

def format_match_weather(weather, match_date):
    if not weather or 'hourly' not in weather:
        return None

    hourly = weather['hourly']
    if not hourly.get('time'):
        return None

    weather_index = 0
    if hasattr(match_date, 'strftime'):
        timestamp = match_date.strftime('%Y-%m-%dT%H:%M')
        if timestamp in hourly['time']:
            weather_index = hourly['time'].index(timestamp)

    weather_code = hourly.get('weathercode', [None])[weather_index]
    weather_labels = {
        0: 'Clear sky',
        1: 'Mainly clear',
        2: 'Partly cloudy',
        3: 'Overcast',
        45: 'Fog',
        48: 'Depositing rime fog',
        51: 'Light drizzle',
        53: 'Moderate drizzle',
        55: 'Dense drizzle',
        61: 'Light rain',
        63: 'Moderate rain',
        65: 'Heavy rain',
        71: 'Light snow',
        73: 'Moderate snow',
        75: 'Heavy snow',
        80: 'Rain showers',
        81: 'Moderate rain showers',
        82: 'Violent rain showers',
        95: 'Thunderstorm',
    }
    return {
        'temperature': hourly.get('temperature_2m', [None])[weather_index],
        'humidity': hourly.get('relativehumidity_2m', [None])[weather_index],
        'wind_speed': hourly.get('windspeed_10m', [None])[weather_index],
        'weather_code': weather_code,
        'weather_label': weather_labels.get(weather_code, 'Unknown conditions'),
    }

def prepare_match_details(match, summary):
    match_date = match.get('date')
    if hasattr(match_date, 'strftime'):
        match_date = match_date.strftime('%d %B %Y, %H:%M')

    details = dict(match)
    details['date_display'] = match_date or 'Date unavailable'
    details['summary'] = summary
    details['weather_display'] = format_match_weather(match.get('weather'), match.get('date'))
    return details

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
    previous_encounters_display = []
    for match in previous_encounters:
        summary = (
            f"Leeds: {match.get('team_stat', 'N/A')} | {match.get('opponent_stat', 'N/A')}"
            f" : {opponent} |{'H' if match.get('home_team', 'N/A').strip().lower() in ['leeds united', 'leeds'] else 'A'}| "
            f"Result: {'Win' if match.get('result', 'N/A') == 1 else 'Loss' if match.get('result', 'N/A') == 0 else 'Draw' if match.get('result', 'N/A') == 2 else 'N/A'}"
        )
        previous_encounters_display.append(prepare_match_details(match, summary))
    previous_encounters_str = "\n".join(match['summary'] for match in previous_encounters_display)
    last_game_str = (
        f"{last_game_details.get('dateEvent', 'N/A')} | {last_game_details.get('strHomeTeam', 'N/A')} {last_game_details.get('intHomeScore', '-')} - {last_game_details.get('intAwayScore', '-')} {last_game_details.get('strAwayTeam', 'N/A')} at {last_game_details.get('strVenue', 'N/A')}"
        f"\nGoal Scorers: {last_game_details.get('goal_scorers', 'N/A')}" if last_game_details else "No last game details available."
    )
    last_five_display = []
    for match in last_five_details:
        summary = (
            f"Opponent: {match.get('opponent', 'N/A')}"
            f" | Result: {match.get('result', 'N/A')}"
            f" | Score: {match.get('score', 'N/A')}"
            f"| {match.get('home', 'N/A')}"
        )
        last_five_display.append(prepare_match_details(match, summary))
    last_five_games_str = "\n".join(match['summary'] for match in last_five_display)

    league_table = return_league_table() or []
    return render_template(
        'index.html',
         next_game_str=next_game_str,
         opponent = opponent,
         opponent_points = fetch_opponent_points(opponent) if opponent else None,
         previous_encounters_str = previous_encounters_str,
         previous_encounters = previous_encounters_display,
         prediction = prediction,
         last_game_str = last_game_str,
         league_table = league_table,
         leeds_current_points = fetch_season_points(),
         last_five_games_str = last_five_games_str,
         last_five_games = last_five_display,
 )

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html', error=error), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)