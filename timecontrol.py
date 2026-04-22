import chess.pgn
from collections import Counter
from tqdm import tqdm

pgn_path = "AllGames.pgn"
total = 0
tc_counter = Counter()

with open(pgn_path) as pgn:
    pbar = tqdm(desc="Scanning games")
    while True:
        headers = chess.pgn.read_headers(pgn)
        if headers is None:
            break
        total += 1
        pbar.update(1)
        tc = headers.get("TimeControl", "").strip()
        if not tc or tc in ("-", "?"):
            tc_counter["missing"] += 1
        else:
            tc_counter[tc] += 1
    pbar.close()

print(f"Total games: {total}")
print(f"\nTop TimeControl values:")
for tc, count in tc_counter.most_common(20):
    print(f"  {tc!r}: {count}")
