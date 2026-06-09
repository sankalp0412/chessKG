from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from SPARQLWrapper import SPARQLWrapper, JSON, POST
import time
import requests
from typing import Dict

SPARQL_ENDPOINT = "http://localhost:7200/repositories/ChessKG"
SPARQL_UPDATE = "http://localhost:7200/repositories/ChessKG/statements"

sparql = SPARQLWrapper(endpoint=SPARQL_ENDPOINT, returnFormat=JSON)


def fetch_all_players_fide_id() -> list[str]:
    sparql.setQuery(
        """
        PREFIX chess: <https://ChessGameKG.org/>
        SELECT DISTINCT ?fideId
        WHERE {
            ?p a chess:Player ;
               chess:fideId ?fideId .
        }
        """
    )

    res = sparql.queryAndConvert()
    fide_ids = [p["fideId"]["value"] for p in res["results"]["bindings"]]
    return fide_ids
    # return ["35009192", "1503014"]


def get_updated_ratings() -> list[Dict]:
    fide_ids = fetch_all_players_fide_id()
    updated_player_info = []

    def fetch_single(fide_id):
        url = f"https://lichess.org/api/fide/player/{fide_id}"
        try:
            time.sleep(0.5)
            response = requests.get(url, timeout=10)
            if not response.text.strip():
                return None
            data = response.json()
            if data:
                return {
                    "fideId": fide_id,
                    "standardRating": data.get("standard", None),
                    "rapid": data.get("rapid", None),
                    "blitz": data.get("blitz", None),
                }
        except Exception as e:
            print(e)
            return None

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(fetch_single, fide_id): fide_id for fide_id in fide_ids
        }
        for future in tqdm(
            as_completed(futures), total=len(fide_ids), desc="Fetching ratings"
        ):
            result = future.result()
            if result:
                updated_player_info.append(result)

    return updated_player_info


def update_graph(updated_info: list[Dict]):
    sparql = SPARQLWrapper(
        endpoint=SPARQL_ENDPOINT, updateEndpoint=SPARQL_UPDATE, returnFormat=JSON
    )
    sparql.setMethod(POST)

    for player in tqdm(updated_info, desc="Updating graph"):
        fide_id = player["fideId"]

        delete_insert = f"""
        PREFIX chess: <https://ChessGameKG.org/>
        DELETE {{
            ?player chess:standardRating ?oldStandard .
            ?player chess:rapidRating ?oldRapid .
            ?player chess:blitzRating ?oldBlitz .
        }}
        INSERT {{
            {f'?player chess:standardRating {player["standardRating"]} .' if player["standardRating"] else ''}
            {f'?player chess:rapidRating {player["rapid"]} .' if player["rapid"] else ''}
            {f'?player chess:blitzRating {player["blitz"]} .' if player["blitz"] else ''}
        }}
        WHERE {{
            ?player chess:fideId {fide_id} .
            OPTIONAL {{ ?player chess:standardRating ?oldStandard }}
            OPTIONAL {{ ?player chess:rapidRating ?oldRapid }}
            OPTIONAL {{ ?player chess:blitzRating ?oldBlitz }}
        }}
        """

        try:
            sparql.setQuery(delete_insert)
            sparql.query()
        except Exception as e:
            print(f"Failed to update player {fide_id}: {e}")


def update_ratings():
    updated_info = get_updated_ratings()
    update_graph(updated_info)


if __name__ == "__main__":
    update_ratings()
