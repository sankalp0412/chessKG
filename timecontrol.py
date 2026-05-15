import json
from collections import Counter
import csv
import pandas as pd
from tqdm import tqdm


def getNullOpening():

    with open("AllGames_2000_2023_v2_2200ELO_Min_20kGamesPerYear.json") as f:
        data = json.load(f)

    reader = csv.DictReader(open("big_elo_map.csv"))

    result = {}
    for row in reader:
        result[row["code"]] = row["name"]

    codes = []
    for game in tqdm(data):
        if game["eco_code"] not in result:
            codes.append(game["eco_code"])

    print(codes)


# Check for duplicate game IDs using current hash logic
# import hashlib

# seen = Counter()
# for game in data:
#     key = f"{game['event']}_{game['date']}_{game['white']}_{game['black']}"
#     game_id = hashlib.md5(key.encode("utf-8")).hexdigest()
#     seen[game_id] += 1

# duplicates = {k: v for k, v in seen.items() if v > 1}
# print(f"Total games: {len(data)}")
# print(f"Unique game IDs: {len(seen)}")
# print(f"Duplicate IDs: {len(duplicates)}")
# print(f"Games affected by collisions: {sum(duplicates.values())}")

# # Also check with round included
# seen_with_round = Counter()
# for game in data:
#     key = f"{game['event']}_{game['date']}_{game['white']}_{game['black']}_{game['round']}"
#     game_id = hashlib.md5(key.encode("utf-8")).hexdigest()
#     seen_with_round[game_id] += 1

# duplicates_with_round = {k: v for k, v in seen_with_round.items() if v > 1}
# print(f"\nWith round included:")
# print(f"Unique game IDs: {len(seen_with_round)}")
# print(f"Duplicate IDs: {len(duplicates_with_round)}")


if __name__ == "__main__":
    getNullOpening()
