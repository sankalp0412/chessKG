import json
import psycopg2
from tqdm import tqdm

# ---------- DB CONNECTION ----------
conn = psycopg2.connect(
    database="mydb", user="admin", password="admin", host="localhost", port=5432
)

cur = conn.cursor()

# ---------- LOAD JSON FILE ----------
file_path = "AllGames_2000_2023_v2_2200ELO_Min_20kGamesPerYear.json"

with open(file_path, "r") as f:
    games = json.load(f)

print(f"Loaded {len(games)} games")

# ---------- INSERT LOOP ----------
for idx, game in enumerate(tqdm(games, desc="Inserting games")):

    # Insert game metadata (moves stored as space-separated SAN string in a single column)
    cur.execute(
        """
        INSERT INTO games (
            event, site, game_date, round,
            white, black, result,
            white_elo, black_elo,
            eco_code, opening, termination,
            moves
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """,
        (
            game.get("event"),
            game.get("site"),
            game.get("date"),
            (
                int(float(r))
                if (r := str(game.get("round", "") or "")).replace(".", "", 1).isdigit()
                else 0
            ),
            game.get("white"),
            game.get("black"),
            game.get("result"),
            int(game.get("white_elo", 0)),
            int(game.get("black_elo", 0)),
            game.get("eco_code"),
            game.get("opening"),
            game.get("termination"),
            " ".join(game.get("moves", [])),
        ),
    )

    game_id = cur.fetchone()[0]

    # commit in batches (IMPORTANT for performance)
    if idx % 100 == 0:
        conn.commit()
        tqdm.write(f"Committed after {idx} games")

# final commit
conn.commit()

cur.close()
conn.close()

print("DONE")
