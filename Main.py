import matplotlib.pyplot as plt
from model_utils import *
from api_utils import *

# Player Stats for last 5 games
data = {
    'player_id': [1, 1, 1, 1, 1],
    'game_id': [101, 102, 103, 104, 105],
    'fouls': [1, 1, 1, 0, 1],
    'goals': [0, 1, 0, 0, 1]
}

df = pd.DataFrame(data)

# Calculate stats for last 5 games
df['foul_percentage'] = df['fouls'].rolling(5).mean() * 100
df['goal_percentage'] = df['goals'].rolling(5).mean() * 100

#print(df)

# Visualization
plt.bar(['Fouls', 'Goals'], [df['foul_percentage'].iloc[-1], df['goal_percentage'].iloc[-1]])
plt.title("Player Stats for Last 5 Games")
plt.ylabel("Percentage")
# plt.show()

## MAIN STARTPOINT ##
generate_prediction(get_previous_game_data())