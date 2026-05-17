import time
import requests
from tqdm import tqdm
from SPARQLWrapper import SPARQLWrapper, JSON, POST
from concurrent.futures import ThreadPoolExecutor, as_completed

SPARQL_ENDPOINT = "http://localhost:7200/repositories/ChessKG"
SPARQL_UPDATE = "http://localhost:7200/repositories/ChessKG/statements"


def get_players():
    sparql = SPARQLWrapper(endpoint=SPARQL_ENDPOINT, returnFormat=JSON)
    sparql.setQuery(
        """
        PREFIX chess: <https://ChessGameKG.org/>
        SELECT DISTINCT ?p ?fideID
        WHERE {
            ?p a chess:Player ;
               chess:fideID ?fideID .
        }
    """
    )
    ret = sparql.queryAndConvert()
    return [(r["p"]["value"], r["fideID"]["value"]) for r in ret["results"]["bindings"]]


def fetch_federation(player_uri, fide_id):
    url = f"https://lichess.org/api/fide/player/{fide_id}"
    try:
        time.sleep(0.5)
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "player_uri": player_uri,
                "federation": data.get("federation", None),
                "title": data.get("title", None),
            }
        else:
            print(f"Failed [{response.status_code}]: {fide_id}")
    except Exception as e:
        print(f"Error {fide_id}: {e}")
    return None


def insert_into_graph(player_uri, federation, title):
    sparql = SPARQLWrapper(
        endpoint=SPARQL_ENDPOINT,
        updateEndpoint=SPARQL_UPDATE,
        returnFormat=JSON,
    )
    sparql.setMethod(POST)

    triples = ""
    if federation:
        triples += f'<{player_uri}> chess:federation "{federation}" .\n'
    if title:
        triples += f'<{player_uri}> chess:title "{title}" .\n'

    if not triples:
        return

    sparql.setQuery(
        f"""
        PREFIX chess: <https://ChessGameKG.org/>
        INSERT DATA {{
            {triples}
        }}
    """
    )
    sparql.query()


def fn():
    players = get_players()
    print(f"Found {len(players)} players with FIDE IDs")
    inserted = 0

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(fetch_federation, uri, fide_id): (uri, fide_id)
            for uri, fide_id in players
        }
        for future in tqdm(as_completed(futures), total=len(futures)):
            result = future.result()
            if result:
                insert_into_graph(
                    result["player_uri"],
                    result["federation"],
                    result["title"],
                )
                inserted += 1

    print(f"Done. Inserted data for {inserted}/{len(players)} players.")


def fn():
    players = get_players()
    print(f"Found {len(players)} players with FIDE IDs")
    inserted = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(fetch_federation, uri, fide_id): (uri, fide_id)
            for uri, fide_id in players
        }
        with tqdm(total=len(futures)) as pbar:
            for future in as_completed(futures):
                result = future.result()
                if result:
                    insert_into_graph(
                        result["player_uri"],
                        result["federation"],
                        result["title"],
                    )
                    inserted += 1
                else:
                    failed += 1
                pbar.set_postfix(inserted=inserted, failed=failed)
                pbar.update(1)

    print(f"Done. {inserted} inserted, {failed} failed.")


if __name__ == "__main__":
    fn()
