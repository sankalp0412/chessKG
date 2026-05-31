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
                "standardRating": data[0].get("standard", None),
                "fideName": data[0].get("name"),
                "federation": data[0].get("federation", "FIDE"),
                "title": data[0].get("title", "Untitled"),
                "gender": data[0].get("gender", None),
                "rapid": data[0].get("rapid", None),
                "blitz": data[0].get("blitz", None),
            }
    except Exception as e:
        print(f"Failed to fetch for player: {player} : {e}")
    return player, None


def getFideId():
    with open("../AllGames_merged_clean.json") as file:
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


def collect_fide_conflicts(player_data: dict) -> list[dict]:
    """Return groups where one fideId is linked to multiple player names."""
    by_fide_id: dict[int, list[dict]] = {}

    for player_name, details in player_data.items():
        fide_id = details.get("fideId")
        if fide_id is None:
            continue

        by_fide_id.setdefault(fide_id, []).append(
            {
                "playerName": player_name,
                "fideName": details.get("fideName", None),
                "standardRating": details.get("standardRating", None),
                "federation": details.get("federation", None),
                "title": details.get("title", None),
                "gender": details.get("gender", None),
                "rapid": details.get("rapid", None),
                "blitz": details.get("blitz", None),
            }
        )

    conflicts: list[dict] = []
    for fide_id, players in by_fide_id.items():
        if len(players) > 1:
            conflicts.append(
                {
                    "fideId": fide_id,
                    "playerCount": len(players),
                    "players": sorted(players, key=lambda x: x["playerName"]),
                }
            )

    conflicts.sort(key=lambda x: x["playerCount"], reverse=True)
    return conflicts


if __name__ == "__main__":
    getFideId()
    with open("fideIds.json", "w") as file:
        json.dump(playerDict, file, indent=4)

    conflict_groups = collect_fide_conflicts(playerDict)
    with open("fideId_conflicts.json", "w") as file:
        json.dump(conflict_groups, file, indent=4)

    print(f"Saved {len(playerDict)} player mappings to fideIds.json")
    print(
        f"Detected {len(conflict_groups)} conflicting FIDE IDs. "
        "Details saved to fideId_conflicts.json"
    )
