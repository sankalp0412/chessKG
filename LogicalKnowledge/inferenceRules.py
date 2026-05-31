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
    ?player a chess:FederationTopPlayer .
}
WHERE {
    {
        SELECT ?player (COUNT(?better) AS ?rank)
        WHERE {
            ?player a chess:Player ;
                    chess:standardRating ?rating ;
                    chess:federation ?federation .
            OPTIONAL {
                ?better a chess:Player ;
                        chess:standardRating ?betterRating ;
                        chess:federation ?federation .
                FILTER (?betterRating > ?rating)
            }
        }
        GROUP BY ?player ?rating ?federation
    }
    FILTER (?rank < 5)
}
"""

OPENING_SPECIALIST = """
PREFIX chess: <https://ChessGameKG.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

INSERT {
    ?player a chess:OpeningSpecialist .
    ?player chess:specializes ?opening .
}
WHERE {
    {
        SELECT ?player ?opening 
               (COUNT(?game) AS ?totalGames) 
               (COUNT(?win) AS ?wins)
        WHERE {
            ?player a chess:Player .
            {
                ?game chess:whitePlayer ?player ;
                      chess:openingPlayed ?opening .
                OPTIONAL {
                    FILTER(?result = "1-0")
                    ?game chess:result ?result .
                    BIND(?game AS ?win)
                }
            } UNION {
                ?game chess:blackPlayer ?player ;
                      chess:openingPlayed ?opening .
                OPTIONAL {
                    FILTER(?result = "0-1")
                    ?game chess:result ?result .
                    BIND(?game AS ?win)
                }
            }
        }
        GROUP BY ?player ?opening
    }
    FILTER (
        ?totalGames >= 10 &&
        (xsd:decimal(?wins) / xsd:decimal(?totalGames)) >= 0.50
    )
}
"""

ENDGAME_SPECIALIST = """
PREFIX chess: <https://ChessGameKG.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

INSERT {
    ?player a chess:EndgameSpecialist .
}
WHERE {
    {
        SELECT ?player 
               (COUNT(?game) AS ?totalLongGames) 
               (COUNT(?win) AS ?wins)
               (COUNT(?draw) AS ?draws)
        WHERE {
            ?player a chess:Player .
            {
                ?game chess:whitePlayer ?player ;
                      chess:movesPlayed ?moves .
                OPTIONAL { FILTER(?result = "1-0") ?game chess:result ?result . BIND(?game AS ?win) }
                OPTIONAL { FILTER(?result = "1/2-1/2") ?game chess:result ?result . BIND(?game AS ?draw) }
            } UNION {
                ?game chess:blackPlayer ?player ;
                      chess:movesPlayed ?moves .
                OPTIONAL { FILTER(?result = "0-1") ?game chess:result ?result . BIND(?game AS ?win) }
                OPTIONAL { FILTER(?result = "1/2-1/2") ?game chess:result ?result . BIND(?game AS ?draw) }
            }
            BIND((STRLEN(?moves) - STRLEN(REPLACE(?moves, " ", ""))) / 2 AS ?fullMoves)
            FILTER (?fullMoves > 40)
        }
        GROUP BY ?player
    }
    FILTER (
        ?totalLongGames >= 200 &&
        (xsd:decimal(?wins) + 0.5 * xsd:decimal(?draws)) / xsd:decimal(?totalLongGames) >= 0.50
    )
}
"""

UNDERDOG = """
PREFIX chess: <https://ChessGameKG.org/>

INSERT {
    ?player a chess:Underdog .
}
WHERE {
    {
        SELECT ?player
               (SUM(?isWin) AS ?wins)
               (SUM(?isDraw) AS ?draws)
               (COUNT(?game) AS ?total)
        WHERE {
            ?opponent a chess:Player ;
                      chess:title "GM" .

            OPTIONAL { ?player chess:title ?title }
            FILTER (!BOUND(?title) || ?title IN ("FM", "CM", "WFM", "WIM", "WGM"))

            {
                ?game chess:whitePlayer ?player ;
                      chess:blackPlayer ?opponent ;
                      chess:result ?res .
                BIND(IF(?res = "1-0", 1, 0) AS ?isWin)
                BIND(IF(?res = "1/2-1/2", 1, 0) AS ?isDraw)
            } UNION {
                ?game chess:blackPlayer ?player ;
                      chess:whitePlayer ?opponent ;
                      chess:result ?res .
                BIND(IF(?res = "0-1", 1, 0) AS ?isWin)
                BIND(IF(?res = "1/2-1/2", 1, 0) AS ?isDraw)
            }
        }
        GROUP BY ?player
    }
    FILTER (
        ?wins >= 3 &&
        ROUND(100 * (?wins + 0.5 * ?draws) / ?total) >= 50
    )
}
"""


DECISIVE_PLAYER = """
PREFIX chess: <https://ChessGameKG.org/>

INSERT {
    ?player a chess:DecisivePlayer .
}
WHERE {
    {
        SELECT ?player
               (SUM(?isDecisive) AS ?decisive)
               (COUNT(?game) AS ?total)
        WHERE {
            ?player a chess:Player .
            {
                ?game chess:whitePlayer ?player ;
                      chess:result ?res .
                BIND(IF(?res != "1/2-1/2", 1, 0) AS ?isDecisive)
            } UNION {
                ?game chess:blackPlayer ?player ;
                      chess:result ?res .
                BIND(IF(?res != "1/2-1/2", 1, 0) AS ?isDecisive)
            }
        }
        GROUP BY ?player
    }
    FILTER (
        ?total >= 50 &&
        ROUND(100 * ?decisive / ?total) >= 75
    )
}
"""


# ------------------------------------ Properties ------------------------------------

MOST_PLAYED_AGAINST = """
PREFIX chess: <https://ChessGameKG.org/>

INSERT {
    ?player chess:mostPlayedAgainst ?opponent .
}
WHERE {
    {
        SELECT ?player (MAX(?count) AS ?maxGames)
        WHERE {
            {
                SELECT ?player ?opponent (COUNT(?game) AS ?count)
                WHERE {
                    {
                        ?game chess:whitePlayer ?player ;
                              chess:blackPlayer ?opponent .
                    } UNION {
                        ?game chess:blackPlayer ?player ;
                              chess:whitePlayer ?opponent .
                    }
                    FILTER (?player != ?opponent)
                }
                GROUP BY ?player ?opponent
                HAVING (COUNT(?game) >= 5)
            }
        }
        GROUP BY ?player
    }
    {
        SELECT ?player ?opponent (COUNT(?game) AS ?count)
        WHERE {
            {
                ?game chess:whitePlayer ?player ;
                      chess:blackPlayer ?opponent .
            } UNION {
                ?game chess:blackPlayer ?player ;
                      chess:whitePlayer ?opponent .
            }
            FILTER (?player != ?opponent)
        }
        GROUP BY ?player ?opponent
        HAVING (COUNT(?game) >= 5)
    }
    FILTER (?count = ?maxGames)
}
"""

PREFERRED_OPENING_AS_WHITE = """
PREFIX chess: <https://ChessGameKG.org/>

INSERT {
    ?player chess:preferredOpeningAsWhite ?preferredOpening .
}
WHERE {
  # Step 1: Get the opening counts per player as White
  {
    SELECT ?player (COUNT(?game) AS ?gameCount) ?preferredOpening
    WHERE {
      ?game chess:whitePlayer ?player .
      ?game chess:openingPlayed ?preferredOpening .
    }
    GROUP BY ?player ?preferredOpening
  }

  # Step 2: Enforce the 30-game minimum threshold for White
  {
    SELECT ?player
    WHERE {
      ?game chess:whitePlayer ?player .
    }
    GROUP BY ?player
    HAVING (COUNT(?game) >= 30)
  }

  # Step 3: Strict Uniqueness Check (No ties allowed for 1st place)
  FILTER (NOT EXISTS {
    SELECT ?player ?otherOpening
    WHERE {
      ?game2 chess:whitePlayer ?player .
      ?game2 chess:openingPlayed ?otherOpening .
    }
    GROUP BY ?player ?otherOpening
    HAVING (?otherOpening != ?preferredOpening && COUNT(?game2) >= ?gameCount)
  })
}
"""

PREFERRED_OPENING_AS_BLACK = """
PREFIX chess: <https://ChessGameKG.org/>

INSERT {
    ?player chess:preferredOpeningAsBlack ?preferredOpening .
}
WHERE {
  # Step 1: Get the opening counts per player as Black
  {
    SELECT ?player (COUNT(?game) AS ?gameCount) ?preferredOpening
    WHERE {
      ?game chess:blackPlayer ?player .
      ?game chess:openingPlayed ?preferredOpening .
    }
    GROUP BY ?player ?preferredOpening
  }

  # Step 2: Enforce the 30-game minimum threshold for Black
  {
    SELECT ?player
    WHERE {
      ?game chess:blackPlayer ?player .
    }
    GROUP BY ?player
    HAVING (COUNT(?game) >= 30)
  }

  # Step 3: Strict Uniqueness Check (No ties allowed for 1st place)
  FILTER (NOT EXISTS {
    SELECT ?player ?otherOpening
    WHERE {
      ?game2 chess:blackPlayer ?player .
      ?game2 chess:openingPlayed ?otherOpening .
    }
    GROUP BY ?player ?otherOpening
    HAVING (?otherOpening != ?preferredOpening && COUNT(?game2) >= ?gameCount)
  })
}
"""


STYLES_SIMILAR_TO = """
PREFIX chess: <https://ChessGameKG.org/>

INSERT {
    ?playerA chess:stylesSimilarTo ?playerB .
}
WHERE {
    # 1. Match both preferred openings for Player A
    ?playerA chess:preferredOpeningAsWhite ?whiteOpening ;
             chess:preferredOpeningAsBlack ?blackOpening .

    # 2. Match the exact same openings for Player B
    ?playerB chess:preferredOpeningAsWhite ?whiteOpening ;
             chess:preferredOpeningAsBlack ?blackOpening .

    # 3. Optimize: Prevent self-matching and eliminate duplicate inverted pairs
    FILTER (?playerA != ?playerB)
    FILTER (STR(?playerA) < STR(?playerB))
}
"""

DOMINATES = """
PREFIX chess: <https://ChessGameKG.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

INSERT {
    ?playerA chess:dominates ?playerB .
}
WHERE {
  {
    SELECT ?playerA ?playerB 
           (COUNT(?game) AS ?totalGames) 
           (SUM(?points) AS ?totalPointsA)
    WHERE {
      ?game chess:openingPlayed ?opening .
      
      {
        ?game chess:whitePlayer ?playerA ;
              chess:blackPlayer ?playerB ;
              chess:result ?result .
        BIND(IF(?result = "1-0", 1.0, IF(?result = "1/2-1/2", 0.5, 0.0)) AS ?points)
      }
      UNION
      {
        ?game chess:whitePlayer ?playerB ;
              chess:blackPlayer ?playerA ;
              chess:result ?result .
        BIND(IF(?result = "0-1", 1.0, IF(?result = "1/2-1/2", 0.5, 0.0)) AS ?points)
      }
    }
    GROUP BY ?playerA ?playerB
    HAVING (COUNT(?game) >= 10)
  }

  # Calculate the final percentage score for Player A
  BIND((xsd:decimal(?totalPointsA) / xsd:decimal(?totalGames)) AS ?scoreA)
  
  # Filter for the 60% dominance threshold
  FILTER (?scoreA >= 0.60)
}
"""

EVENLY_MATCHED = """
PREFIX chess: <https://ChessGameKG.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

INSERT {
    # Establish the symmetric relationship in the graph
    ?playerA chess:evenlyMatches ?playerB .
}
WHERE {
  {
    # Subquery: Aggregate direct wins and total games per player pair
    SELECT ?playerA ?playerB 
           (COUNT(?game) AS ?totalGames)
           (SUM(?isWinA) AS ?winsA)
           (SUM(?isWinB) AS ?winsB)
    WHERE {
      # Ensure we are only pulling valid game nodes
      ?game chess:openingPlayed ?opening . 
      
      {
        # Scenario 1: Player A played White, Player B played Black
        ?game chess:whitePlayer ?playerA ;
              chess:blackPlayer ?playerB ;
              chess:result ?result .
        BIND(IF(?result = "1-0", 1, 0) AS ?isWinA) # White wins -> Point to A
        BIND(IF(?result = "0-1", 1, 0) AS ?isWinB) # Black wins -> Point to B
      }
      UNION
      {
        # Scenario 2: Player B played White, Player A played Black
        ?game chess:whitePlayer ?playerB ;
              chess:blackPlayer ?playerA ;
              chess:result ?result .
        BIND(IF(?result = "0-1", 1, 0) AS ?isWinA) # Black wins -> Point to A
        BIND(IF(?result = "1-0", 1, 0) AS ?isWinB) # White wins -> Point to B
      }
    }
    GROUP BY ?playerA ?playerB
    # Criterion 1: Must have a deep history of at least 10 games played
    HAVING (COUNT(?game) >= 10)
  }

  # Criterion 2: Enforce string comparison symmetry to avoid redundant mirror triples.
  FILTER (STR(?playerA) < STR(?playerB))

  # Criterion 3: Both competitors must have won at least ONE game against the other.
  FILTER (?winsA > 0 && ?winsB > 0)

  # Criterion 4: The competitive gap constraint (win margin must be 0, 1, or 2 games).
  FILTER (ABS(?winsA - ?winsB) <= 2)
}
"""

if __name__ == "__main__":
    # run_update(ELITE_PLAYER, "ElitePlayer")
    # run_update(SUPER_GM, "SuperGM")
    # run_update(FEDERATION_TOP_PLAYER, "FederationTopPlayer")
    # run_update(OPENING_SPECIALIST, "OpeningSpecialist")
    # run_update(ENDGAME_SPECIALIST, "EndgameSpecialist")
    # run_update(UNDERDOG, "Underdog")
    # run_update(DECISIVE_PLAYER, "DecisivePlayer")

    # ## ------Properties

    # run_update(MOST_PLAYED_AGAINST, "mostPlayedAgainst")
    # run_update(PREFERRED_OPENING_AS_WHITE, "preferredOpeningAsWhite")
    # run_update(PREFERRED_OPENING_AS_BLACK, "preferredOpeningAsBlack")
    # run_update(STYLES_SIMILAR_TO, "stylesSimilarTo")
    # run_update(DOMINATES, "dominates")
    run_update(EVENLY_MATCHED, "evenlyMatched")
