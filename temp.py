import json


def fn():
    with open("AllGames_merged_clean.json") as file:
        games = json.load(file)
        allPlayers = set()

        for game in games:
            allPlayers.add(game.get("black"))
            allPlayers.add(game.get("white"))
        print(len(allPlayers))
        res = json.dumps(list(allPlayers), indent=2, ensure_ascii=False)

        with open("AllPlayers.json", "w") as output_file:
            output_file.write(res)


if __name__ == "__main__":
    fn()
