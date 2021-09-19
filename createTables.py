# import libraries
import pandas as pd
import numpy as np
import re


# load data 
git_repo = "https://raw.githubusercontent.com/rivergrove/Join-the-dark-side-of-chess/master/python_2021/"
file = "lichess_rivergrove_2021-08-09.csv"
user_name = "rivergrove"
df = pd.read_csv(git_repo + file, delimiter = "\t", header=None, names = ['col'])
df.head()


# start row is every row with [Event...]
start_row = df[df['col'].str.contains('[Event ', regex=False)].index


# create games table
if 'games' in globals():
    del games
    
for i in range(1,len(start_row)):
    
    if 'games' in globals():
        
        if "Horde" in df.iloc[start_row[i-1],0]:
            # skip Horde Games
            pass
        elif "Casual" in df.iloc[start_row[i-1],0]:
            temp = df.iloc[start_row[i-1]:start_row[i-1]+10,0]
            temp.loc[len(temp.index)] = [""] 
            temp.loc[len(temp.index)] = [""]
            temp = pd.DataFrame(temp).append(df.iloc[start_row[i-1]+10:start_row[i]]).T
            temp.columns = games.columns
            games = games.append(temp)
            pass
        elif len(games.columns) != (start_row[i]-start_row[i-1]):
            # skip error games
            print("row " + str(i-1) + ": column count does not align. There are " + str(len(games.columns)) + " in games and " + str(start_row[i]-start_row[i-1]) + " in temp.")
        else:
            temp = pd.DataFrame(df.iloc[start_row[i-1]:start_row[i],0]).T
            temp.columns = games.columns
            games = games.append(temp)
        
    else:
        
        if "Casual" in df.iloc[start_row[i-1],0]:
            temp = df.iloc[0:10,0]
            temp = temp.append([""])
            temp = temp.append([""])
            temp = temp.append(df.iloc[10:start_row[i]])
            games = pd.DataFrame(temp).T
        else: 
            games = pd.DataFrame(df.iloc[0:start_row[i],0]).T


# rename columns
games = games.rename(columns = {0: 'game_type', 1: 'url', 2:'date_utc', 3:'temp_white', 4:'temp_black', 5:'result', 7:'time_utc',8:'white_rating',9:'black_rating',10:'white_rating_diff',11:'black_rating_diff',12:'variant',13:'time_control',14:'opening_code',15:'opening_name',16:'termination_type',17:'moves'}, inplace = False)


# Pull value for game type
games['game_type'] = games['game_type'].str.split().str[-2]

# remove [], "", heading from values
def clean(text):
    return text.str.split(' ', 1).str[1].str.replace(']','').str.replace('"','')

games.iloc[:,1:17] = games.iloc[:,1:17].apply(clean)

# remove column 6
games.drop(columns=[6])

# reset index
games = games.reset_index(drop=True)

# create my/opp columns
user_name = 'rivergrove'
games['white'] = games['temp_white'] == user_name
# if 'white' == True, then opp_name = username else opp_name = temp_black
games['opp_name'] = np.where(games['white']==True, games['temp_black'], games['temp_white'])
# remove temp_black, temp_white, result
# result
games['outcome'] = np.select([(games['white']==True) & (games['result']=="1-0"), (games['white']==False) & (games['result']=="0-1"), games['result']=="1/2-1/2", (games['white']==False) & (games['result']=="1-0"), (games['white']==True) & (games['result']=="0-1")], ["win", "win", "draw", "loss", "loss"], default="error")
# opponent rating vs my rating
games['my_rating'] = np.where(games['white']==True, games['white_rating'], games['black_rating'])
games['opp_rating'] = np.where(games['white']==True, games['black_rating'], games['white_rating'])
games['my_rating_diff'] = np.where(games['white']==True, games['white_rating_diff'].str.replace('+','',regex=False), games['black_rating_diff'].str.replace('+','',regex=False))
games['opp_rating_diff'] = np.where(games['white']==True, games['black_rating_diff'].str.replace('+','',regex=False), games['white_rating_diff'].str.replace('+','',regex=False))

# remove extra date column
games = games.drop(6, 1)

# remove extra columns
games.drop(['temp_white', 'temp_black','result','white_rating','black_rating','white_rating_diff','black_rating_diff'], axis=1, inplace=True)

# add seconds and increment
# remove [], "", heading from values
def clean_seconds(text):
    return str(text).split('+', 1)[0]
def clean_increment(text):
    return str(text).split('+', 1)[-1]

games['seconds'] = games.iloc[:,5].apply(clean_seconds)
games['increment'] = games.iloc[:,5].apply(clean_increment)

# add game_id as first column
games["id"] = games.index + 1

# reorder columns
games = games[["id","game_type","variant","date_utc","time_utc","seconds","increment","opening_code","opening_name","termination_type","url","white","opp_name","outcome","my_rating","opp_rating","my_rating_diff","opp_rating_diff","moves"]]

# take first row and make it into moves

# split game into moves
moves = pd.DataFrame(columns = ['game_id', 'move_number', 'white_move', 'white_eval','white_move_time','black_move','black_eval','black_move_time'])

for x in range(0,games.shape[0]):
    
    game_moves = len(games["moves"][x].split("}"))

    move_counter = 1
    
    if x%50==0:
        print(x)
    
    if 'eval' in games["moves"][x] or 'clk' in games["moves"][x]:

        for n in range(game_moves):
            
            if 'eval' in games["moves"][x].split("}")[n]:
                try:
                    eval_raw = re.search("\[\%eval (-*[0-9]+\.[0-9]+|\#-*[0-9]+)\]",games["moves"][x].split("}")[n]).group(0)
                except AttributeError:
                    print("x:",x,"n:",n)
                _eval = eval_raw.replace('[%eval ', '').replace(']','')
            else:
                _eval = ''
                
            if 'clk' in games["moves"][x].split("}")[n]:
                clk_raw = re.search("\[\%clk [0-9]+:[0-9]+:[0-9]+\]",games["moves"][x].split("}")[n]).group(0)
                clk = clk_raw.replace('[%clk ', '').replace(']','')
            else:
                clk = ''
            
            temp_move = games["moves"][x].split("}")[n].split(" ")

            if move_counter == 1:
                white_move = temp_move[1]
                white_eval = _eval
                white_move_time = clk
            elif len(temp_move) == 2:
                pass
            elif move_counter % 2 == 1:
                white_move = temp_move[2]
                white_eval = _eval
                white_move_time = clk
                if move_counter == game_moves:
                    black_move = ''
                    black_eval = ''
                    black_move_time = ''
                    moves = moves.append({'game_id': x+1, 'move_number': move_counter/2, 'white_move': white_move, 'white_eval': white_eval, 'white_move_time': white_move_time, 'black_move': black_move, 'black_eval': black_eval, 'black_move_time': black_move_time}, ignore_index=True)
            elif move_counter % 2 == 0:
                black_move = temp_move[2]
                black_eval = _eval
                black_move_time = clk
                moves = moves.append({'game_id': x+1, 'move_number': move_counter/2, 'white_move': white_move, 'white_eval': white_eval, 'white_move_time': white_move_time, 'black_move': black_move, 'black_eval': black_eval, 'black_move_time': black_move_time}, ignore_index=True)

            move_counter = move_counter + 1
    
    elif 'eval' not in games["moves"][x] and 'clk' not in games["moves"][x]:
               
        temp_move = games["moves"][x].split(".")
        
        for y in range(1, len(temp_move)):
            moves = moves.append({'game_id': x+1, 'move_number': y, 'white_move': temp_move[y].split(" ")[1], 'white_eval': '', 'white_move_time': '', 'black_move': temp_move[y].split(" ")[2], 'black_eval': '', 'black_move_time': ''}, ignore_index=True)

# set results in black_move to null values
moves.loc[(moves.black_move == '1/2-1/2') | (moves.black_move == '1-0') | (moves.black_move == '0-1'), "black_move"] = ''

# move number to int
moves.move_number = moves.move_number.astype(int)

# add moves to games table
move_count = moves.groupby(['game_id'])['game_id'].count().reset_index(name="move_count")
games = pd.merge(games, move_count, left_on='id', right_on='game_id')

# drop game_id and moves
games.drop(['game_id', 'moves'], axis = 1, inplace=True)

# add id to moves table
moves = moves.reset_index()

# change index to id
moves.rename({'index': 'id'}, axis=1, inplace=True)

# add 1 to every value
moves.id += 1

# change date column to date format
games.date_utc = games.date_utc.str.replace(".","-",regex=False)

normal_games = games[games.game_type.isin(['Rapid', 'Correspondence', 'Blitz', 'Bullet','Hyper', 'Classical'])]