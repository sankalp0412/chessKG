import requests

AUTH = ("admin", "root")
SHACL_GRAPH = "http://rdf4j.org/schema/rdf4j#SHACLShapeGraph"


def upload_shacl_shapes(shapes_path: str):
    with open(shapes_path, "rb") as f:
        response = requests.put(
            f"http://localhost:7200/repositories/ChessKG/rdf-graphs/service",
            params={"graph": SHACL_GRAPH},
            headers={"Content-Type": "text/turtle"},
            data=f,
            auth=AUTH,
        )
    if response.status_code in (200, 204):
        print("✅ SHACL shapes uploaded")
    else:
        with open("Output.txt", "w") as outputfile:
            outputfile.write(response.text)
        print(f"❌ Failed: {response.status_code} Saved to Output.txt")


upload_shacl_shapes("shacl-shapes.ttl")
