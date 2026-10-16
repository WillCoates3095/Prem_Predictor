import api_utils
import time
import csv
import os

CSV_FILE = 'team_venues.csv'
CSV_HEADERS = ['Team Name', 'Venue Location', 'City', 'Latitude', 'Longitude']
SEASON_FILE = os.path.join('Seasons', '2026-2027.csv')
REQUEST_DELAY = 12
RATE_LIMIT_DELAY = 60
TEAM_LOCATION_FALLBACKS = {
    'Arsenal': 'Holloway, London, England',
}
REQUEST_STATS = {
    'total': 0,
    'successful': 0,
    'rate_limited': 0,
    'other_errors': 0,
}

def ensure_csv_exists():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(CSV_HEADERS)
        return

    with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        if reader.fieldnames == CSV_HEADERS:
            return
        rows = list(reader)

    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, '') for header in CSV_HEADERS})

def append_to_csv(team_name, venue, city, latitude, longitude):
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([team_name, venue, city, latitude, longitude])

def update_coordinates(team_name, latitude, longitude):
    with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
        rows = list(csv.DictReader(csvfile))

    for row in rows:
        if row.get('Team Name') == team_name:
            row['Latitude'] = latitude
            row['Longitude'] = longitude
            break

    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(rows)

def get_existing_teams():
    with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
        return {
            row['Team Name']
            for row in csv.DictReader(csvfile)
            if row.get('Team Name') and row.get('Latitude') and row.get('Longitude')
        }

def get_existing_locations():
    with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
        return {
            row['Team Name']: row
            for row in csv.DictReader(csvfile)
            if row.get('Team Name')
        }

def get_premier_league_teams():
    with open(SEASON_FILE, newline='', encoding='utf-8-sig') as csvfile:
        teams = set()
        for row in csv.DictReader(csvfile):
            teams.add(row['Home Team'].strip())
            teams.add(row['Away Team'].strip())
        return sorted(teams)

def get_team_details(team_name):
    search_url = f'{api_utils.BASE_URL}/{api_utils.API_KEY}/searchteams.php'
    REQUEST_STATS['total'] += 1
    print(f"API call {REQUEST_STATS['total']}: looking up {team_name}")
    response = api_utils.requests.get(
        search_url,
        params={'t': team_name},
        timeout=15,
    )
    if response.status_code == 200:
        REQUEST_STATS['successful'] += 1
        team_data = response.json()
        if team_data.get('teams'):
            team = team_data['teams'][0]
            venue = team.get('strStadium')
            city = team.get('strLocation') or TEAM_LOCATION_FALLBACKS.get(team_name)
            latitude = team.get('strStadiumLat') or team.get('strLatitude')
            longitude = team.get('strStadiumLon') or team.get('strLongitude')
            if venue and city:
                if not latitude or not longitude:
                    latitude, longitude = geocode_location(city, venue)
                if latitude and longitude:
                    return venue, city, latitude, longitude
            print(f'Incomplete location data for {team_name}; nothing saved.')
    elif response.status_code == 429:
        REQUEST_STATS['rate_limited'] += 1
        print(f'Rate limit reached while looking up {team_name}.')
    else:
        REQUEST_STATS['other_errors'] += 1
        print(f'Error looking up {team_name}: {response.status_code}')
    return None

def geocode_location(*locations):
    candidates = []
    for location in locations:
        candidates.append(location)
        candidates.extend(
            part.strip()
            for part in reversed(location.split(','))
            if part.strip() and part.strip().lower() not in {'england', 'uk', 'united kingdom'}
        )

    for location in candidates:
        response = api_utils.requests.get(
            'https://geocoding-api.open-meteo.com/v1/search',
            params={
                'name': location,
                'count': 1,
                'language': 'en',
                'format': 'json',
                'countryCode': 'GB',
            },
            headers={'User-Agent': 'Prem-Predictor/1.0'},
            timeout=15,
        )
        if response.status_code != 200:
            print(f'Could not geocode {location}: {response.status_code}')
            continue

        results = response.json().get('results') or []
        if results:
            return results[0].get('latitude'), results[0].get('longitude')

    print(f'No coordinates found for {", ".join(locations)}.')
    return None, None

def collect_team_venues():
    REQUEST_STATS.update({
        'total': 0,
        'successful': 0,
        'rate_limited': 0,
        'other_errors': 0,
    })
    ensure_csv_exists()
    existing_teams = get_existing_teams()
    existing_locations = get_existing_locations()
    premier_league_teams = get_premier_league_teams()
    started_at = time.monotonic()
    added = 0
    skipped = 0

    for index, team_name in enumerate(premier_league_teams):
        existing_location = existing_locations.get(team_name)
        if existing_location and existing_location.get('Venue Location') and existing_location.get('City'):
            latitude, longitude = geocode_location(
                existing_location['City'],
                existing_location['Venue Location'],
            )
            if latitude and longitude:
                update_coordinates(team_name, latitude, longitude)
                existing_teams.add(team_name)
                added += 1
                print(f'Added coordinates for {team_name}: ({latitude}, {longitude})')
            elif team_name in existing_teams:
                skipped += 1
                print(f'Skipping {team_name}; it is already in {CSV_FILE}.')
            else:
                print(f'No coordinates found for {team_name}; retry it later.')
            continue

        rate_limited_before_request = REQUEST_STATS['rate_limited']
        details = get_team_details(team_name)
        if details:
            venue, city, latitude, longitude = details
            if venue and city and latitude and longitude:
                append_to_csv(team_name, venue, city, latitude, longitude)
                existing_teams.add(team_name)
                added += 1
                print(f'Added {team_name}: {venue} ({city}, {latitude}, {longitude})')
            else:
                print(f'No complete venue data found for {team_name}; retry it later.')

        if index < len(premier_league_teams) - 1:
            delay = (
                RATE_LIMIT_DELAY
                if REQUEST_STATS['rate_limited'] > rate_limited_before_request
                else REQUEST_DELAY
            )
            print(f'Waiting {delay} seconds before the next API call.')
            time.sleep(delay)

    elapsed_minutes = (time.monotonic() - started_at) / 60
    calls_per_minute = (
        REQUEST_STATS['total'] / elapsed_minutes
        if elapsed_minutes > 0 else 0
    )
    print(
        f"Run summary: {REQUEST_STATS['total']} API calls, "
        f"{REQUEST_STATS['successful']} successful, "
        f"{REQUEST_STATS['rate_limited']} rate-limited, "
        f"{REQUEST_STATS['other_errors']} other errors, "
        f"{added} added, {skipped} skipped, "
        f"{calls_per_minute:.1f} calls/minute."
    )

if __name__ == '__main__':
    collect_team_venues()