import numpy as np
import faiss
import json


def main():

    data = np.load("entity_embeddings.npy")
    data = np.concatenate([data.real, data.imag], axis=1)

    index = faiss.IndexFlatL2(data.shape[1])
    index.add(data)
    print(index.ntotal)

    entity_to_id = json.load(open("entity_to_id.json"))
    id_to_entity = {str(v): k for k, v in entity_to_id.items()}
    print(list(id_to_entity.keys())[:3])

    carlsen_idx = entity_to_id["https://ChessGameKG.org/player_Carlsen_Magnus"]
    query_vector = data[carlsen_idx].reshape(1, -1)
    distances, indices = index.search(query_vector, 5)

    for idx in indices[0]:
        player_uri = id_to_entity[str(idx)]
        print(player_uri)

    faiss.write_index(index, "chesskg.index")


if __name__ == "__main__":
    main()
