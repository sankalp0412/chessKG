from rdflib.contrib.graphdb.client import GraphDBClient
from rdflib import URIRef, Literal, Graph, Namespace, RDF, XSD, Dataset
from rdflib.namespace import SDO
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
import json
from rdflib import ConjunctiveGraph
from tqdm import tqdm
import hashlib
import requests
import unicodedata
import re
from pathlib import Path

CHESS = Namespace("https://ChessGameKG.org/")
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
# GAME_INSERT_LIMIT = 100

store = SPARQLUpdateStore(
    query_endpoint="http://localhost:7200/repositories/ChessKG",
    update_endpoint="http://localhost:7200/repositories/ChessKG/statements",
    auth=("admin", "root"),
)

graph = Dataset()
graph.bind("chess", CHESS)


def getGames():
    games_path = PROJECT_ROOT / "WCSince21.json"
    with games_path.open("r") as file:
        data = json.load(file)

    return data


def clean_uri(value: str) -> str:
    # Normalize unicode → converts ü→u, é→e, ñ→n etc.
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    # Remove anything that's not alphanumeric or underscore
    value = re.sub(r"[^\w]", "_", value)
    # Clean up multiple consecutive underscores
    value = re.sub(r"_+", "_", value)
    return value.strip("_")


def createGraph():
    games: list[dict] = getGames()
    output_ttl_path = PROJECT_ROOT / "chess_kg.ttl"
    # if GAME_INSERT_LIMIT is not None:
    #     games = games[:GAME_INSERT_LIMIT]
    #     print(f"Processing {len(games)} games (limit={GAME_INSERT_LIMIT})")

    fide_ids_path = PROJECT_ROOT / "additionalDataScripts" / "fideIds.json"
    with fide_ids_path.open("r") as f:
        fideData = json.load(f)

    try:
        graph.bind("chess", CHESS)
        for game in tqdm(games):
            event_name = game["event"]
            site = game["site"]
            date = game["date"].replace(".", "-")
            game_round = game["round"]
            black_name = game["black"]
            white_name = game["white"]
            result = game["result"]  # Relate to game
            white_elo = game["white_elo"]  # related to player
            black_elo = game["black_elo"]  # related to player
            eco_code = game.get("eco_code")  # related to game, and independent uri
            opening = game.get("opening")  # related to game, and independent uri

            # skip if no eco code, becasue some same games are duplicated
            if not eco_code or not opening:
                continue

            termination = game["termination"]  # related to game
            moves = " ".join(game["moves"])  # relate to game

            white_fide_data = fideData.get(white_name, {})
            black_fide_data = fideData.get(black_name, {})

            whiteFideId = white_fide_data.get("fideId")
            blackFideId = black_fide_data.get("fideId")

            whiteFideRating = white_fide_data.get("standardRating")
            blackFideRating = black_fide_data.get("standardRating")

            whiteFideName = white_fide_data.get("fideName")
            blackFideName = black_fide_data.get("fideName")

            whiteFederation = white_fide_data.get("federation")
            blackFederation = black_fide_data.get("federation")

            whiteGender = white_fide_data.get("gender")
            blackGender = black_fide_data.get("gender")

            whiteTitle = white_fide_data.get("title")
            blackTitle = black_fide_data.get("title")

            whiteRapidRating = white_fide_data.get("rapid")
            blackRapidRating = black_fide_data.get("rapid")

            whiteBlitzRating = white_fide_data.get("blitz")
            blackBlitzRating = black_fide_data.get("blitz")

            game_id = hashlib.md5(
                f"{event_name}_{date}_{white_name}_{black_name}_{game_round}".encode(
                    "utf-8"
                )
            ).hexdigest()

            game_uri = CHESS[f"game_{game_id}"]

            # Convert strings -> URIs (spaces replaced with underscores)
            event_uri = CHESS[f"event_{clean_uri(event_name)}_{date[:4]}"]
            white_player_key = whiteFideName if whiteFideName else white_name
            black_player_key = blackFideName if blackFideName else black_name
            white_uri = CHESS[f"player_{clean_uri(white_player_key)}"]
            black_uri = CHESS[f"player_{clean_uri(black_player_key)}"]
            eco_code_uri = CHESS[f"eco_{clean_uri(eco_code)}"]
            opening_uri = CHESS[f"opening_{clean_uri(opening)}"]
            termination_uri = CHESS[f"termination_{clean_uri(termination)}"]

            # Game ID and round and date
            graph.add((game_uri, RDF.type, CHESS.Game))
            graph.add(
                (game_uri, CHESS.gameRound, Literal(game_round, datatype=XSD.string))
            )
            graph.add((game_uri, SDO.startDate, Literal(date, datatype=XSD.date)))

            # Event related tuples
            graph.add((event_uri, RDF.type, SDO.Event))
            graph.add((event_uri, SDO.name, Literal(event_name)))
            graph.add((event_uri, SDO.location, Literal(site, datatype=XSD.string)))

            # Connect game → event
            graph.add((game_uri, CHESS.playedAtEvent, event_uri))

            # Player
            graph.add((white_uri, RDF.type, CHESS.Player))
            graph.add((black_uri, RDF.type, CHESS.Player))

            # White player properties
            if whiteFideId is not None:
                graph.add(
                    (
                        white_uri,
                        CHESS.fideId,
                        Literal(whiteFideId, datatype=XSD.integer),
                    )
                )
            if whiteFideRating is not None:
                graph.add(
                    (
                        white_uri,
                        CHESS.standardRating,
                        Literal(whiteFideRating, datatype=XSD.integer),
                    )
                )
            if whiteRapidRating is not None:
                graph.add(
                    (
                        white_uri,
                        CHESS.rapidRating,
                        Literal(whiteRapidRating, datatype=XSD.integer),
                    )
                )
            if whiteBlitzRating is not None:
                graph.add(
                    (
                        white_uri,
                        CHESS.blitzRating,
                        Literal(whiteBlitzRating, datatype=XSD.integer),
                    )
                )
            if whiteTitle is not None:
                graph.add(
                    (white_uri, CHESS.title, Literal(whiteTitle, datatype=XSD.string))
                )
            if whiteFederation is not None:
                graph.add(
                    (
                        white_uri,
                        CHESS.federation,
                        Literal(whiteFederation, datatype=XSD.string),
                    )
                )
            if whiteGender is not None:
                graph.add(
                    (white_uri, CHESS.gender, Literal(whiteGender, datatype=XSD.string))
                )

            if whiteFideName is not None:
                graph.add(
                    (
                        white_uri,
                        SDO.name,
                        Literal(whiteFideName, datatype=XSD.string),
                    )
                )

            # Black player properties (same pattern)

            if blackFideRating is not None:
                graph.add(
                    (
                        black_uri,
                        CHESS.standardRating,
                        Literal(blackFideRating, datatype=XSD.integer),
                    )
                )
            if blackRapidRating is not None:
                graph.add(
                    (
                        black_uri,
                        CHESS.rapidRating,
                        Literal(blackRapidRating, datatype=XSD.integer),
                    )
                )
            if blackBlitzRating is not None:
                graph.add(
                    (
                        black_uri,
                        CHESS.blitzRating,
                        Literal(blackBlitzRating, datatype=XSD.integer),
                    )
                )
            if blackTitle is not None:
                graph.add(
                    (black_uri, CHESS.title, Literal(blackTitle, datatype=XSD.string))
                )
            if blackFederation is not None:
                graph.add(
                    (
                        black_uri,
                        CHESS.federation,
                        Literal(blackFederation, datatype=XSD.string),
                    )
                )
            if blackGender is not None:
                graph.add(
                    (black_uri, CHESS.gender, Literal(blackGender, datatype=XSD.string))
                )
            if blackFideName is not None:
                graph.add(
                    (
                        black_uri,
                        SDO.name,
                        Literal(blackFideName, datatype=XSD.string),
                    )
                )
            if blackFideId is not None:
                graph.add(
                    (
                        black_uri,
                        CHESS.fideId,
                        Literal(blackFideId, datatype=XSD.integer),
                    )
                )

            # Adding elo to game
            graph.add(
                (
                    game_uri,
                    CHESS.whiteRating,
                    Literal(white_elo, datatype=XSD.decimal),
                )
            )
            graph.add(
                (
                    game_uri,
                    CHESS.blackRating,
                    Literal(black_elo, datatype=XSD.decimal),
                )
            )

            # Link players to the game
            graph.add((game_uri, CHESS.whitePlayer, white_uri))
            graph.add((game_uri, CHESS.blackPlayer, black_uri))

            # Opening Related

            graph.add((opening_uri, RDF.type, CHESS.Opening))
            graph.add((eco_code_uri, RDF.type, CHESS.EcoCode))

            # Connect Opening and ECO

            graph.add((opening_uri, CHESS.ecoCode, eco_code_uri))

            # Connect opening and ECO to game

            graph.add((game_uri, CHESS.openingPlayed, opening_uri))

            # Connect result to game

            graph.add((game_uri, CHESS.result, Literal(result, datatype=XSD.string)))

            # Connect termination to game

            graph.add((termination_uri, RDF.type, CHESS.Termination))

            graph.add((game_uri, CHESS.termination, termination_uri))

            # Connect Moves to game

            graph.add(
                (game_uri, CHESS.movesPlayed, Literal(moves, datatype=XSD.string))
            )
        graph.serialize(str(output_ttl_path), format="turtle")
        print(f"Serialized {len(graph)} triples to {output_ttl_path}")

    except Exception as e:
        print(f"Error: {e}")
        return

    try:
        with output_ttl_path.open("rb") as f:
            response = requests.post(
                "http://localhost:7200/repositories/ChessKG/statements",
                headers={"Content-Type": "text/turtle"},
                data=f,
                auth=("admin", "root"),
            )

        print(response.status_code)
    except Exception as e:
        print(f"Error while insert: {e}")


if __name__ == "__main__":
    createGraph()
