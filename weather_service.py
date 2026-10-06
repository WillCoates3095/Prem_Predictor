import requests

def get_weather_for_date(date, time, location="London"):
    # Coordinates for London (default)
    latitude, longitude = 51.5074, -0.1278
    # Format date and time for API request
    start_date = date
    end_date = date
    # Construct API URL
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={latitude}&longitude={longitude}&start_date={start_date}&end_date={end_date}&hourly=temperature_2m,relativehumidity_2m,windspeed_10m,weathercode"
    # Make API request
    response = requests.get(url)
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

print(get_weather_for_date("2023-10-01", "15:00", "London"))