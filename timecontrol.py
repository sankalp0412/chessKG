import json
from collections import Counter
import csv
import pandas as pd
from tqdm import tqdm


# def getNullOpening():

#     with open("AllGames_2000_2023_v2_2200ELO_Min_20kGamesPerYear.json") as f:
#         data = json.load(f)

#     reader = csv.DictReader(open("big_elo_map.csv"))

#     result = {}
#     for row in reader:
#         result[row["code"]] = row["name"]

#     codes = []
#     for game in tqdm(data):
#         if game["eco_code"] not in result:
#             codes.append(game["eco_code"])

#     print(codes)


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


# def fn():
#     with open("AllGames_2000_2023_v2_2200ELO_Min_20kGamesPerYearV2_17May.json") as f:
#         data = json.load(f)

#     players = set()
#     for game in data:
#         players.add(game["white"])
#         players.add(game["black"])

#     with open("unique_players.txt", "w") as f:
#         for p in sorted(players):
#             f.write(p + "\n")

#     print(f"Exported {len(players)} unique players to unique_players.txt")
import chess.pgn
from tqdm import tqdm
from collections import Counter


# def get_unique_tournaments(pgn_path: str):
#     tournaments = Counter()

#     with open(pgn_path) as pgn:
#         pbar = tqdm(desc="Reading headers")
#         while True:
#             headers = chess.pgn.read_headers(pgn)
#             if headers is None:
#                 break
#             event = headers.get("Event", "").strip()
#             if event:
#                 tournaments[event] += 1
#             pbar.update(1)
#         pbar.close()

#     # sort by frequency
#     with open("unique_tournaments.txt", "w") as f:
#         for name, count in tournaments.most_common():
#             f.write(f"{count:6d}  {name}\n")

#     print(f"Found {len(tournaments)} unique tournaments")
#     print(f"Exported to unique_tournaments.txt")
#     print("\nTop 20:")
#     for name, count in tournaments.most_common(20):
#         print(f"  {count:6d}  {name}")


def get_map():
    df = pd.read_csv("big_elo_map.csv")
    mapping = dict(zip(df["code"], df["name"]))
    return mapping


def audit_missing_eco_codes(pgn_path: str) -> None:
    """
    Scan PGN and find all ECO codes not in big_elo_map.csv.
    """
    # Load map
    opening_map = get_map()

    missing = {}
    found = {}
    eco_counts = {}

    with open(pgn_path, encoding="utf-8", errors="ignore") as pgn:
        pbar = tqdm(desc=f"Auditing ECO codes in {pgn_path}")

        while True:
            headers = chess.pgn.read_headers(pgn)
            if headers is None:
                break

            eco_code = headers.get("ECO", "").strip()

            if eco_code:
                eco_counts[eco_code] = eco_counts.get(eco_code, 0) + 1

                if eco_code in opening_map:
                    found[eco_code] = found.get(eco_code, 0) + 1
                else:
                    missing[eco_code] = missing.get(eco_code, 0) + 1

            pbar.update(1)

        pbar.close()

    # Report
    print(f"\n📊 ECO Audit Results for {pgn_path}:")
    print(f"  Total unique ECO codes: {len(eco_counts)}")
    print(f"  Found in map: {len(found)}")
    print(f"  Missing from map: {len(missing)}")

    if missing:
        print(f"\n❌ Missing ECO codes (sorted by frequency):")
        for eco, count in sorted(missing.items(), key=lambda x: -x[1]):
            print(f"    {eco}: {count} occurrences")
    else:
        print(f"\n✅ All ECO codes are in the map!")


# Run it
if __name__ == "__main__":
    audit_missing_eco_codes("AllGames.pgn")  # change filename as needed
