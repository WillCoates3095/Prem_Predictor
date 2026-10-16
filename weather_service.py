import csv
import requests

CSV_FILE = 'team_venues.csv'

def get_venue_coordinates(opponent):
    with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
        for row in csv.DictReader(csvfile):
            if row.get('Team Name') == opponent:
                try:
                    return float(row['Latitude']), float(row['Longitude'])
                except (KeyError, TypeError, ValueError) as error:
                    raise ValueError(
                        f'No valid coordinates found for {opponent}.'
                    ) from error
    raise ValueError(f'No venue found for opponent: {opponent}.')

def get_weather_for_date(date, time, opponent):
    latitude, longitude = get_venue_coordinates(opponent)
    start_date = date
    end_date = date

    url = (
        'https://archive-api.open-meteo.com/v1/archive'
        f'?latitude={latitude}&longitude={longitude}'
        f'&start_date={start_date}&end_date={end_date}'
        '&hourly=temperature_2m,relativehumidity_2m,windspeed_10m,weathercode'
        '&timezone=Europe%2FLondon'
    )

    response = requests.get(url, timeout=15)
    response.raise_for_status()
    data = response.json()

    hourly_data = data["hourly"]
    requested_time = f"{date}T{time}"
    try:
        hour_index = hourly_data["time"].index(requested_time)
    except ValueError:
        print(f"Time {requested_time} not found in the data.")
        return data
    weather_code = hourly_data["weathercode"][hour_index]
    wind_speed = hourly_data["windspeed_10m"][hour_index]

    is_sunny = weather_code == 0
    is_cloudy = weather_code in {1, 2, 3}
    is_windy = wind_speed >= 20

    print(f"Cloudy: {is_cloudy}")
    print(f"Sunny: {is_sunny}")
    print(f"Windy: {is_windy} ({wind_speed} km/h)")
    return data