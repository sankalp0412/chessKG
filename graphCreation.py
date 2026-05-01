from rdflib.contrib.graphdb.client import GraphDBClient
from rdflib import URIRef, Literal, Graph, Namespace, RDF, XSD, Dataset
from rdflib.namespace import SDO
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
import json
from rdflib import ConjunctiveGraph
from tqdm import tqdm
import hashlib
import requests

CHESS = Namespace("https://ChessGameKG.org/")

store = SPARQLUpdateStore(
    query_endpoint="http://localhost:7200/repositories/ChessKG",
    update_endpoint="http://localhost:7200/repositories/ChessKG/statements",
    auth=("admin", "root"),
)

graph = Dataset(store=store)
graph.bind("chess", CHESS)


def getGames():
    with open("temp.json", "r") as file:
        data = json.load(file)

    return data


def clean_uri(value: str) -> str:
    return value.replace(" ", "_").replace(",", "").replace(".", "").replace("/", "_")


def createGraph():
    games: list[dict] = getGames()

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
            eco_code = game["eco_code"]  # related to game, and independent uri
            opening = game["opening"]  # related to game, and independent uri
            termination = game["termination"]  # related to game
            moves = " ".join(game["moves"])  # relate to game

            game_id = hashlib.md5(
                f"{event_name}_{date}_{white_name}_{black_name}".encode("utf-8")
            ).hexdigest()

            game_uri = CHESS[f"game_{game_id}"]

            # Convert strings -> URIs (spaces replaced with underscores)
            event_uri = CHESS[f"event_{clean_uri(event_name)}_{date[:4]}"]
            white_uri = CHESS[f"player_{clean_uri(white_name)}"]
            black_uri = CHESS[f"player_{clean_uri(black_name)}"]
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
        graph.serialize("chess_kg.ttl", format="turtle")
        print(f"Serialized {len(graph)} triples to chess_kg.ttl")

    except Exception as e:
        print(f"Error: {e}")

    try:
        with open("chess_kg.ttl", "rb") as f:
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
