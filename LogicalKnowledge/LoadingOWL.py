import requests


def main():
    with open("extended-ontology.ttl", "rb") as f:
        response = requests.post(
            "http://localhost:7200/repositories/ChessKG/statements",
            headers={"Content-Type": "text/turtle"},
            data=f,
            auth=("admin", "root"),
        )
    print(response.status_code)


if __name__ == "__main__":
    main()


# SELECT ?property ?domain ?range
# WHERE {
#   ?property rdfs:domain ?domain ;
#             rdfs:range  ?range .
#   FILTER(STRSTARTS(STR(?property), "https://ChessGameKG.org/"))
# }
# ORDER BY ?property
