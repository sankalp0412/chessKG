import requests

SPARQL_UPDATE = "http://localhost:7200/repositories/ChessKG/statements"
AUTH = ("admin", "root")


def run_update(query: str, rule_name: str):
    response = requests.post(
        SPARQL_UPDATE,
        headers={"Content-Type": "application/sparql-update"},
        data=query,
        auth=AUTH,
    )
    if response.status_code == 204:
        print(f"✅ {rule_name} — done")
    else:
        print(f"❌ {rule_name} — failed: {response.status_code} {response.text}")


# ── Rule 1: ElitePlayer ───────────────────────────────────────────
# Player with StandardRating ≥ 2650
ELITE_PLAYER = """
PREFIX chess: <https://ChessGameKG.org/>

INSERT {
    ?player a chess:ElitePlayer .
}
WHERE {
    ?player a chess:Player ;
            chess:standardRating ?rating .
    FILTER (?rating >= 2650)
}
"""

# ── Rule 2: SuperGM ───────────────────────────────────────────────
# Player with StandardRating ≥ 2700 — subclass of ElitePlayer
SUPER_GM = """
PREFIX chess: <https://ChessGameKG.org/>

INSERT {
    ?player a chess:SuperGM .
}
WHERE {
    ?player a chess:Player ;
            chess:standardRating ?rating .
    FILTER (?rating >= 2700)
}
"""

FEDERATION_TOP_PLAYER = """
PREFIX chess: <https://ChessGameKG.org/>

INSERT {
    ?player a chess: FederationTopPlayer
}
    
WHERE {
    ?player
}



"""


if __name__ == "__main__":
    run_update(ELITE_PLAYER, "ElitePlayer")
    run_update(SUPER_GM, "SuperGM")
