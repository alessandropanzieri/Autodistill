import pandas as pd

def double(df_matches):
    df_matches_winner = df_matches.copy()
    df_matches_loser = df_matches.copy()
    df_matches_winner["Round"] = df_matches_winner["Round"].replace("The Final", "Champion")
    df_matches_winner = df_matches_winner.rename(columns = {"Winner": "Player"}).drop("Loser", axis = 1)
    df_matches_loser = df_matches_loser.rename(columns = {"Loser": "Player"}).drop("Winner", axis = 1)

    df_doubled = pd.concat([df_matches_winner, df_matches_loser], ignore_index=True )
    return df_doubled

def weighted_average(row, col_name):
    current_year_value = row[col_name]
    previous_year_value = row[col_name + "_previous_year"]
    # if both values are not null, calculate the weighted average
    if pd.notnull(current_year_value) and pd.notnull(previous_year_value):
        if isinstance(current_year_value, str):
            current_year_value = float(current_year_value.replace("%", ""))/100
            previous_year_value = float(previous_year_value.replace("%", ""))/100
            return row["weight_current_year"] *  current_year_value + \
                row["weight_previous_year"] * previous_year_value/100
        else:
            return row["weight_current_year"] * current_year_value + row["weight_previous_year"] * previous_year_value
    # if current year value is null, use the previous year value
    elif pd.isnull(current_year_value):
        if isinstance(previous_year_value, str):
            return round(float(previous_year_value.replace("%", ""))/100,3)
        else:
            return previous_year_value
    # if previous year value is null, use the current year value
    elif pd.isnull(previous_year_value):
        if isinstance(current_year_value, str):
            return round(float(current_year_value.replace("%", ""))/100,3)
        else:
            return current_year_value

def merge_winner(df_matches, df_to_merge):
    df_to_merge_winner = df_to_merge.copy()
    df_to_merge_winner.columns = [str(col) + "_winner" if col not in ["name", "time_frame", "surface"] else col for col in df_to_merge.columns]
    df_matches = df_matches.merge(df_to_merge_winner, left_on = ["Winner", "Year", "Surface"], right_on = ["name", "time_frame", "surface"], how = "left")
    df_matches.drop(["name", "time_frame", "surface"], axis=1, inplace = True)

    df_to_merge_winner["time_frame"] = df_to_merge_winner["time_frame"].apply(lambda x: str(int(x) + 1) if x != "52Week" else x)
    df_matches = df_matches.merge(df_to_merge_winner, left_on = ["Winner", "Year", "Surface"], right_on = ["name", "time_frame", "surface"], how = "left", suffixes = ("", "_previous_year"))
    df_matches.drop(["name", "time_frame", "surface"], axis=1, inplace = True)

    #print(df_to_merge_winner.dtypes)
    for column in df_to_merge_winner.columns:
        if column not in ["name", "time_frame", "surface"]:
            df_matches[column] = df_matches.apply(lambda row: weighted_average(row, column), axis=1)
    df_matches[df_matches.columns.drop(list(df_matches.filter(regex="_previous_year$")))]
    return df_matches

def merge_loser(df_matches, df_to_merge):
    df_to_merge_loser = df_to_merge.copy()
    df_to_merge_loser.columns = [str(col) + "_loser" if col not in ["name", "time_frame", "surface"] else col for col in df_to_merge.columns]
    df_matches = df_matches.merge(df_to_merge_loser, left_on = ["Loser", "Year", "Surface"], right_on = ["name", "time_frame", "surface"], how = "left")
    df_matches.drop(["name", "time_frame", "surface"], axis=1, inplace = True)

    df_to_merge_loser["time_frame"] = df_to_merge_loser["time_frame"].apply(lambda x: str(int(x) + 1) if x!= "52Week" else x)
    df_matches = df_matches.merge(df_to_merge_loser, left_on = ["Loser", "Year", "Surface"], right_on = ["name", "time_frame", "surface"], how = "left", suffixes = ("", "_previous_year"))
    df_matches.drop(["name", "time_frame", "surface"], axis=1, inplace = True)

    for column in df_to_merge_loser.columns:
        if column not in ["name", "time_frame", "surface"]:
            df_matches[column] = df_matches.apply(lambda row: weighted_average(row, column), axis=1)
    df_matches[df_matches.columns.drop(list(df_matches.filter(regex="_previous_year$")))]
    return df_matches

def merge_features(df_matches, df_serve_stats, df_return_stats, df_under_pressure_stats):
    df_matches = merge_winner(df_matches, df_serve_stats)
    df_matches = merge_loser(df_matches, df_serve_stats)
    df_matches = merge_winner(df_matches, df_return_stats)
    df_matches = merge_loser(df_matches, df_return_stats)
    df_matches = merge_winner(df_matches, df_under_pressure_stats)
    df_matches = merge_loser(df_matches, df_under_pressure_stats)
    return df_matches

def feature_previous_tournament(df_matches):
    df_doubled = double(df_matches)[["Player", "Tournament", "Date", "Year", "Round"]]
    df_doubled["rank_tournament"] = df_doubled.sort_values(["Date", "Round"], ascending = [False, True]).groupby(["Tournament", "Player", "Year"])["Date"].cumcount()+1
    df_rank1 = df_doubled.loc[df_doubled["rank_tournament"] == 1]
    df_doubled.drop(["rank_tournament", "Round"], axis = 1, inplace = True)
    df_doubled = df_doubled.merge(df_rank1[["Player", "Tournament", "Year", "Round"]], on = ["Player", "Tournament", "Year"])
    df_prev_year = df_doubled.copy()
    df_prev_year.drop_duplicates(subset=["Tournament", "Player", "Year"], inplace=True)
    df_prev_year["Round_Previous_Year"] = df_prev_year.sort_values("Year").groupby(["Tournament", "Player"])["Round"].shift(1)
    df_matches = df_matches.merge(df_prev_year[["Round_Previous_Year", "Tournament", "Player", "Year"]].rename(columns = {"Round_Previous_Year": "Round_Previous_Year_Winner"}), 
                                    left_on = ["Tournament", "Winner", "Year"], right_on = ["Tournament", "Player", "Year"]).drop("Player", axis = 1)
    df_matches = df_matches.merge(df_prev_year[["Round_Previous_Year", "Tournament", "Player", "Year"]].rename(columns = {"Round_Previous_Year": "Round_Previous_Year_Loser"}), 
                                    left_on = ["Tournament", "Loser", "Year"], right_on = ["Tournament", "Player", "Year"]).drop("Player", axis = 1)

    return df_matches

def rank_category(rank):
    if rank <= 10:
        return 1
    elif rank <= 20:
        return 2
    elif rank <= 50:
        return 3
    elif rank <= 100:
        return 4
    else:
        return 5

def feature_current_tournament(df_matches):
    round_rank_mapping = {
    "1st Round": 1,
    "2nd Round": 2,
    "3rd Round": 3,
    "4th Round": 4,
    "Quarterfinals": 5,
    "Semifinals": 6,
    "The Final": 7
    }

    df_matches["rank_round"] = df_matches["Round"].map(round_rank_mapping)
    df_doubled = double(df_matches)
    df_doubled = df_doubled[["Player", "Tournament", "Date", "Year", "Round", "rank_round", "LRank","L1", "L2", "L3", "L4", "L5"]]
    #Smallest rank player defeated until this round (best player defeated)
    df_doubled["best_rank_player_defeated_until_t"] = df_doubled.sort_values(["Tournament", "Year", "Player", "rank_round"]).groupby(["Tournament", "Player", "Year"])["LRank"].cummin()
    
    #N. games won by the Loser during the current match
    df_doubled["games_won_loser"] = df_doubled[["L1", "L2", "L3", "L4", "L5"]].sum(axis=1)

    #N. games won by all the opponents until this round
    df_doubled["games_won_by_opponent_until_round"] = df_doubled.sort_values(["Tournament", "Year", "Player", "rank_round"]).groupby(["Tournament", "Player", "Year"])["games_won_loser"].cumsum()

    df_doubled["games_won_by_opponent_until_round"] = df_doubled.sort_values(["Tournament", "Year", "Player", "rank_round"]).groupby(["Tournament", "Player", "Year"])["games_won_by_opponent_until_round"].shift()
    
    df_matches = df_matches.merge(df_doubled[["games_won_by_opponent_until_round", "Tournament", "Player", "Year", "rank_round"]].rename(columns = {"games_won_by_opponent_until_round": "games_won_by_opponent_until_round_Winner"}), 
                                   left_on = ["Tournament", "Winner", "Year", "rank_round"], right_on = ["Tournament", "Player", "Year", "rank_round"]).drop("Player", axis = 1)
    df_matches = df_matches.merge(df_doubled[["games_won_by_opponent_until_round", "Tournament", "Player", "Year", "rank_round"]].rename(columns = {"games_won_by_opponent_until_round": "games_won_by_opponent_until_round_Loser"}), 
                                    left_on = ["Tournament", "Loser", "Year", "rank_round"], right_on = ["Tournament", "Player", "Year", "rank_round"]).drop("Player", axis = 1)

    df_matches["rank_category_Loser"] = df_matches["LRank"].apply(rank_category)
    df_matches["rank_category_Winner"] = df_matches["WRank"].apply(rank_category)

    # Now we can assign a weight to each category. For example:
    weights = {1: 1, 2: 0.8, 3: 0.6, 4: 0.4, 5: 0.2}

    df_matches["weighted_games_opponent_Winner"] = df_matches["games_won_by_opponent_until_round_Winner"] / df_matches["rank_category_Loser"].map(weights)
    df_matches["weighted_games_opponent_Loser"] = df_matches["games_won_by_opponent_until_round_Loser"] / df_matches["rank_category_Loser"].map(weights)

    return df_matches

all_matches_from_2020_2023 = pd.read_excel("./data/all_matches_from_2020_2023.xlsx")
all_matches_from_2020_2023["Winner"] = all_matches_from_2020_2023["Winner"].apply(lambda x: x.split(" ")[0])
all_matches_from_2020_2023["Loser"] = all_matches_from_2020_2023["Loser"].apply(lambda x: x.split(" ")[0])
all_matches_from_2020_2023["Year"] = all_matches_from_2020_2023["Date"].dt.year.astype(str)
all_matches_from_2020_2023["Month"] = all_matches_from_2020_2023["Date"].dt.month
all_matches_from_2020_2023["Weight_current_year"] = all_matches_from_2020_2023["Month"] / 12
all_matches_from_2020_2023["Weight_previous_year"] = 1 - all_matches_from_2020_2023["Weight_current_year"]

return_stats = pd.read_excel("./data/official_atp_site_stats.xlsx", sheet_name = "return")
serve_stats = pd.read_excel("./data/official_atp_site_stats.xlsx", sheet_name = "serve")
pressure_stats = pd.read_excel("./data/official_atp_site_stats.xlsx", sheet_name = "pressure")
return_stats["player_name"] = return_stats["player_name"].apply(lambda x: x.split(" ")[-1])
serve_stats["player_name"] = serve_stats["player_name"].apply(lambda x: x.split(" ")[-1])
pressure_stats["player_name"] = pressure_stats["player_name"].apply(lambda x: x.split(" ")[-1])

all_matches_from_2020_2023 = feature_previous_tournament(all_matches_from_2020_2023)
all_matches_from_2020_2023 = feature_current_tournament(all_matches_from_2020_2023)

merged_df = merge_features(all_matches_from_2020_2023, return_stats, serve_stats, pressure_stats)
merged_df.to_excel("all_stats_merged.xlsx")