import api_utils
import time
import csv
import os

CSV_FILE = 'team_venues.csv'
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
            writer.writerow(['Team Name', 'Venue Location', 'City'])

def append_to_csv(team_name, venue, city):
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([team_name, venue, city])

def get_existing_teams():
    with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
        return {
            row['Team Name']
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
            if venue and city:
                return venue, city
            print(f'Incomplete location data for {team_name}; nothing saved.')
    elif response.status_code == 429:
        REQUEST_STATS['rate_limited'] += 1
        print(f'Rate limit reached while looking up {team_name}.')
    else:
        REQUEST_STATS['other_errors'] += 1
        print(f'Error looking up {team_name}: {response.status_code}')
    return None

def collect_team_venues():
    REQUEST_STATS.update({
        'total': 0,
        'successful': 0,
        'rate_limited': 0,
        'other_errors': 0,
    })
    ensure_csv_exists()
    existing_teams = get_existing_teams()
    premier_league_teams = get_premier_league_teams()
    started_at = time.monotonic()
    added = 0
    skipped = 0

    for index, team_name in enumerate(premier_league_teams):
        if team_name in existing_teams:
            skipped += 1
            print(f'Skipping {team_name}; it is already in {CSV_FILE}.')
            continue

        rate_limited_before_request = REQUEST_STATS['rate_limited']
        details = get_team_details(team_name)
        if details:
            venue, city = details
            if venue and city:
                append_to_csv(team_name, venue, city)
                existing_teams.add(team_name)
                added += 1
                print(f'Added {team_name}: {venue} ({city})')
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