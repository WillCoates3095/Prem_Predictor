import os
import glob
import requests
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier

from api_utils import *

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

#Main program execution starts here -- all of the above ideally another file
fetch_team_stats()