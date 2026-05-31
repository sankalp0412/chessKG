import chess
import chess.pgn
import pandas as pd
import json
from tqdm import tqdm
import re


def get_map():
    df = pd.read_csv("big_elo_map.csv")
    mapping = dict(zip(df["code"], df["name"]))
    return mapping


def get_termination(game: chess.pgn.Game) -> str:
    result = game.headers.get("Result", "*")

    board = game.end().board()

    if board.is_checkmate():
        return "Checkmate"

    if result in ("1-0", "0-1"):
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


def clean_player_name(name: str) -> str:
    import unicodedata

    # Normalize Unicode (é→e, ñ→n, etc.)
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")

    # Remove trailing dots
    name = name.rstrip(".")

    # Remove (wh) and (bl) suffixes
    name = re.sub(r"\s*\(wh\)\s*$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*\(bl\)\s*$", "", name, flags=re.IGNORECASE)

    # Remove any remaining special/corrupted characters (like ?)
    name = re.sub(r"[^a-zA-Z0-9,.\s\-']", "", name)

    # Clean up whitespace
    name = " ".join(name.split()).strip()

    return name


def is_full_name(name: str) -> bool:
    """Return False if name has only an initial after the comma"""
    if "," in name:
        parts = name.split(",")
        firstname = parts[1].strip().rstrip(".")
        # reject single initial like "D" or "B H" or "B."
        if len(firstname) <= 2:
            return False
    elif len(name.split()) == 1:
        # single word no comma — likely just a surname
        return False
    return True


def normalize_event_name(event: str) -> str:
    # Remove year tokens like 2012, 2019-20, 2019/20, 2019-2020.
    cleaned = re.sub(
        r"(?<!\d)(?:19|20)\d{2}(?:\s*[-/]\s*(?:\d{2}|(?:19|20)\d{2}))?(?!\d)",
        " ",
        event,
    )
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip(" -_/,:;()[]")


MAJOR_TOURNAMENTS = {
    "world championship",
    "wch",
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
    "st louis",
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
    "bundesliga",
    "qatar masters",
    "reykjavik open",
    "sharjah masters",
}


def process_pgn(opening_map: dict, pgn_path: str) -> list[dict]:
    games_data = []
    skipped_names = 0
    from collections import defaultdict

    year_counts = defaultdict(int)
    YEAR_CAP = 10000

    with open(pgn_path, encoding="utf-8", errors="ignore") as pgn:
        pbar = tqdm(desc=f"Processing {pgn_path}")

        while True:
            offset = pgn.tell()
            headers = chess.pgn.read_headers(pgn)
            if headers is None:
                break

            date_str = headers.get("Date", "").strip()
            if not date_str or "?" in date_str:
                continue
            try:
                year = int(date_str.split(".")[0])
            except ValueError:
                continue
            if year < 2000 or year > 2024:
                continue
            if year_counts[year] >= YEAR_CAP:
                continue

            raw_event = headers.get("Event", "").strip()
            event_clean = normalize_event_name(raw_event)
            event_match = event_clean.lower()
            if not any(t in event_match for t in MAJOR_TOURNAMENTS):
                continue

            try:
                white_elo = int(headers.get("WhiteElo", ""))
                black_elo = int(headers.get("BlackElo", ""))
            except (ValueError, TypeError):
                continue
            if not (2200 <= white_elo <= 3500) or not (2200 <= black_elo <= 3500):
                continue

            if headers.get("Result", "*") not in ("1-0", "0-1", "1/2-1/2"):
                continue

            # clean and validate names before parsing moves
            white_raw = headers.get("White", "").strip()
            black_raw = headers.get("Black", "").strip()
            white = clean_player_name(white_raw)
            black = clean_player_name(black_raw)

            if not white or not black or white == "?" or black == "?":
                continue
            if re.search(r"\d", white) or re.search(r"\d", black):
                skipped_names += 1
                continue
            if not is_full_name(white) or not is_full_name(black):
                skipped_names += 1
                continue

            # headers passed — parse full game
            pgn.seek(offset)
            game = chess.pgn.read_game(pgn)
            if game is None:
                break

            headers = game.headers
            eco_code = headers.get("ECO", "")
            opening_name = opening_map.get(eco_code, eco_code)

            result = headers.get("Result", "*")
            termination = get_termination(game)

            moves = []
            board = game.board()
            for move in game.mainline_moves():
                moves.append(board.san(move))
                board.push(move)

            if not moves:
                continue

            games_data.append(
                {
                    "event": event_clean,
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
            )
            year_counts[year] += 1
            pbar.update(1)

        pbar.close()
        print(f"  Skipped {skipped_names} games due to incomplete player names")

    return games_data


if __name__ == "__main__":
    opening_map = get_map()

    print("--- Processing World Championship 2021 PGN ---")
    games1 = process_pgn(opening_map, "wch21.pgn")

    print("--- Processing World Championship 2023 PGN ---")
    games2 = process_pgn(opening_map, "wch23.pgn")

    print("--- Processing World Championship 2024 PGN ---")
    games3 = process_pgn(opening_map, "wch24.pgn")

    # merge and deduplicate by event+date+white+black+round
    seen = set()
    merged = []
    for game in games1 + games2 + games3:
        key = f"{game['event']}_{game['date']}_{game['white']}_{game['black']}_{game['round']}"
        if key not in seen:
            seen.add(key)
            merged.append(game)

    output_path = "WCSince21.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    print(f"\n✅ WCh2021: {len(games1)} games")
    print(f"✅ WCh2023: {len(games2)} games")
    print(f"✅ WCh2024: {len(games3)} games")
    print(f"✅ Merged + deduplicated: {len(merged)} games")
    print(f"✅ Exported to {output_path}")

    from collections import Counter

    termination_counts = Counter(g["termination"] for g in merged)
    print("\nTermination breakdown:")
    for term, count in termination_counts.most_common():
        print(f"  {term}: {count}")
