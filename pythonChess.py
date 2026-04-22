import chess
import chess.pgn
import pandas as pd
import json
from tqdm import tqdm


def get_map():
    df = pd.read_csv("big_elo_map.csv")
    mapping = dict(zip(df["code"], df["name"]))
    return mapping


def get_termination(game: chess.pgn.Game) -> str:
    """Return 'Checkmate', 'Resignation', 'Draw', or 'Unknown' based on game end."""
    result = game.headers.get("Result", "*")
    termination_tag = game.headers.get("Termination", "").lower()

    # Walk to the final position
    board = game.end().board()

    if board.is_checkmate():
        return "Checkmate"

    if result in ("1-0", "0-1"):
        # Not checkmate -> must be resignation (or forfeit)
        return "Resignation"

    if result == "1/2-1/2":
        if board.is_stalemate():
            return "Stalemate"
        if board.is_insufficient_material():
            return "Draw - Insufficient Material"
        if board.is_seventyfive_moves():
            return "Draw - 75-Move Rule"
        if board.is_fivefold_repetition():
            return "Draw - Fivefold Repetition"
        return "Draw"

    return "Unknown"


from tqdm import tqdm
import chess.pgn

MAJOR_TOURNAMENTS = {
    "world championship",
    "candidates",
    "grand prix",
    "tata steel",
    "wijk aan zee",
    "linares",
    "morelia",
    "stavanger",
    "norway chess",
    "sinquefield cup",
    "saint louis",
    "london classic",
    "gashimov memorial",
    "shamkir",
    "zurich chess challenge",
    "olympiad",
    "grenke",
    "bad homburg",
    "superbet",
    "zagreb",
    "bucharest",
    "isle of man",
    "european championship",
    "world cup",
    "fide grand swiss",
    "tal memorial",
    "dortmund",
    "biel",
    "nh chess",
}


def process_pgn(opening_map: dict, pgn_path: str = "AllGames.pgn") -> list[dict]:
    games_data = []

    with open(pgn_path) as pgn:

        pbar = tqdm(desc="Processing games")

        while len(games_data) < 1000:
            # Fast header-only read to check filters before parsing moves
            offset = pgn.tell()
            headers = chess.pgn.read_headers(pgn)
            if headers is None:
                break

            # --- header filters (no move parsing yet) ---
            date_str = headers.get("Date", "").strip()
            if not date_str or "?" in date_str:
                continue
            try:
                if int(date_str.split(".")[0]) < 2010:
                    continue
            except ValueError:
                continue

            event = headers.get("Event", "").lower()
            if not any(t in event for t in MAJOR_TOURNAMENTS):
                continue

            try:
                white_elo = int(headers.get("WhiteElo", ""))
                black_elo = int(headers.get("BlackElo", ""))
            except (ValueError, TypeError):
                continue
            if not (2300 <= white_elo <= 3500) or not (2300 <= black_elo <= 3500):
                continue

            if headers.get("Result", "*") not in ("1-0", "0-1", "1/2-1/2"):
                continue

            # Headers passed — seek back and parse full game with moves
            pgn.seek(offset)
            game = chess.pgn.read_game(pgn)
            if game is None:
                break

            headers = game.headers
            eco_code = headers.get("ECO", "")
            opening_name = opening_map.get(eco_code, eco_code)

            white = headers.get("White", "").strip()
            black = headers.get("Black", "").strip()
            if not white or not black or white == "?" or black == "?":
                continue

            result = headers.get("Result", "*")
            termination = get_termination(game)

            moves = []
            board = game.board()
            for move in game.mainline_moves():
                moves.append(board.san(move))
                board.push(move)

            if not moves:
                continue

            game_dict = {
                "event": headers.get("Event", ""),
                "site": headers.get("Site", ""),
                "date": date_str,
                "round": headers.get("Round", ""),
                "white": white,
                "black": black,
                "result": result,
                "white_elo": white_elo,
                "black_elo": black_elo,
                "eco_code": eco_code,
                "opening": opening_name,
                "termination": termination,
                "moves": moves,
            }

            games_data.append(game_dict)
            pbar.update(1)

        pbar.close()

    return games_data


if __name__ == "__main__":
    opening_map = get_map()
    games = process_pgn(opening_map)

    output_path = "AllGames_test1000.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(games, f, indent=2, ensure_ascii=False)

    print(f"Exported {len(games)} games to {output_path}")

    # Quick termination summary
    from collections import Counter

    termination_counts = Counter(g["termination"] for g in games)
    print("\nTermination breakdown:")
    for term, count in termination_counts.most_common():
        print(f"  {term}: {count}")
