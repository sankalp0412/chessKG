import json
import requests
import time
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

playerDict: dict = {}
url = "https://lichess.org/api/fide/player"


def fetchFideId(player: str):
    try:
        time.sleep(0.5)  # 500ms between requests
        response = requests.get(url, params={"q": player}, timeout=10)

        if not response.text.strip():
            return player, None

        data = response.json()
        if data:
            return player, {
                "fideId": data[0]["id"],
                "standardRating": data[0].get("standard", "Unknown"),
                "federation": data[0].get("federation", "FIDE"),
                "title": data[0].get("title", "Untitled"),
                "gender": data[0].get("gender", "Unknown"),
                "rapid": data[0].get("rapid", "Unknown"),
                "blitz": data[0].get("blitz", "Unknown"),
            }
    except Exception as e:
        print(f"Failed to fetch for player: {player} : {e}")
    return player, None


def getFideId():
    with open("AllGames_2000_2023_v2_2200ELO_Min_20kGamesPerYear.json") as file:
        data = json.load(file)

    players = set()
    for game in data:
        players.add(game["white"])
        players.add(game["black"])

    print(f"Fetching {len(players)} unique players...")

    with ThreadPoolExecutor(max_workers=2) as executor:  # reduced from 20 → 5
        futures = {executor.submit(fetchFideId, p): p for p in players}
        for future in tqdm(as_completed(futures), total=len(players)):
            player, result = future.result()
            if result:
                playerDict[player] = result


if __name__ == "__main__":
    getFideId()
    with open("fideIds.json", "w") as file:
        json.dump(playerDict, file, indent=4)
