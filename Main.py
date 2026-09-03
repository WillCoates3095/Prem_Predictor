import requests
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier

#API key and Base URL
API_KEY = '123'
BASE_URL = 'https://www.thesportsdb.com/api/v1/json'

# Example fetch team stats from the API
team_name = 'Leeds United'
search_team_url = f'{BASE_URL}/{API_KEY}/searchteams.php'
response = requests.get(search_team_url, params={'t': team_name})

if response.status_code == 200:
    team_data = response.json()
    if team_data['teams']:
        leeds_team_id = team_data['teams'][0]['idTeam']
        print(f"Leeds United Team ID: {leeds_team_id}")

    else:
        print("No team found.")
else:
    print(f"Error: {response.status_code}")

#Get Leeds next game
if 'leeds_team_id' in locals():
    next_game_url = f'{BASE_URL}/{API_KEY}/eventsnext.php'
    response = requests.get(next_game_url, params={'id': leeds_team_id})

    if response.status_code == 200:
        next_game_data = response.json()
        print(next_game_data['events'][0])
        if next_game_data['events']:
            next_game = next_game_data['events'][0]
            opponent = next_game['strAwayTeam'] if next_game['idHomeTeam'] == leeds_team_id else next_game['strHomeTeam']
            print(f"Leeds United Next Game: {next_game['strEvent']} on {next_game['dateEvent']} at {next_game['strVenue']}\n\n\n")
        else:
            print("No upcoming games found.")
    else:
        print(f"Error: {response.status_code}")



#Player Stats for last 5 games
data = {
    'player_id' : [1,1,1,1,1],
    'game_id' : [101,102,103,104,105],
    'fouls' : [1,1,1,0,1],
    'goals' : [0, 1, 0, 0,1]
}

df = pd.DataFrame(data)

# Calculate states for last 5 games
df['foul_percentage'] = df['fouls'].rolling(5).mean() * 100
df['goal_percentage'] = df['goals'].rolling(5).mean() * 100

print(df)

#Match Stats
match_data = {
    'team_stat': [1,2,3,4,5],
    'opponent_stat': [5,4,3,2,1],
    'result': [0,1,1,0,1]  # 0 = loss, 1 = win
}
match_df = pd.DataFrame(match_data)

#Split data into features and target variable
X = match_df[['team_stat', 'opponent_stat']]
Y = match_df['result']

#Train/test split
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

#Combine player stats and match stats
player_stats = df[['foul_percentage', 'goal_percentage']].iloc[-1]
team_stats = {'team_stat':3, 'opponent_stat':2}  # Example team stats for the upcoming match
combined_stats = {**team_stats, **player_stats.to_dict()}
print("Combined Stats", combined_stats)

#Visualisation
plt.bar(['Fouls','Goals'], [combined_stats['foul_percentage'], combined_stats['goal_percentage']])
plt.title("Player Stats for Last 5 Games")
plt.ylabel("Percentage")
#plt.show()

#Train a Random Forest Classifier
model = RandomForestClassifier(random_state=42)
model.fit(X_train, Y_train)

#Make predictions
Y_pred = model.predict(X_test)

#Evaluate the model
accuracy = accuracy_score(Y_test, Y_pred)
print(f"Model Accuracy: {accuracy * 100:.2f}%")

# Predict the outcome for a new match
new_match = pd.DataFrame({'team_stat': [3], 'opponent_stat': [1]})
predicted_result = model.predict(new_match)

print("Predicted Result for New Match:", "Win" if predicted_result[0] == 1 else "Loss")