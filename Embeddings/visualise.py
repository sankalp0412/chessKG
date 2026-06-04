import numpy as np
import json
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
import pandas as pd
from collections import defaultdict

# Load embeddings and entity mapping
embeddings = np.load("entity_embeddings.npy")
with open("entity_to_id.json", "r") as f:
    entity_to_id = json.load(f)

# Flip to id -> entity
id_to_entity = {v: k for k, v in entity_to_id.items()}

# Filter only player entities
player_indices = [idx for uri, idx in entity_to_id.items() if "player_" in uri]
player_uris = [id_to_entity[idx] for idx in player_indices]
player_embeddings = np.concatenate(
    [embeddings[player_indices].real, embeddings[player_indices].imag], axis=1
)

print(f"Found {len(player_indices)} players")

# Run t-SNE
tsne = TSNE(n_components=2, random_state=42, perplexity=30)
player_2d = tsne.fit_transform(player_embeddings)

# Load player classes
classes_df = pd.read_csv(
    "player_classes.tsv", sep="\t", header=0, names=["player", "class"]
)
classes_df["player"] = classes_df["player"].str.strip("<>")
classes_df["class"] = (
    classes_df["class"].str.strip("<>").str.replace("https://ChessGameKG.org/", "")
)

# Map player URI -> list of classes
player_class_map = defaultdict(list)
for _, row in classes_df.iterrows():
    player_class_map[row["player"]].append(row["class"])

# Assign colours
colors = {
    "ElitePlayer": "red",
    "SuperGM": "darkred",
    "OpeningSpecialist": "blue",
    "AggressivePlayer": "orange",
    "EndgameSpecialist": "green",
    "Underdog": "purple",
    "DecisivePlayer": "brown",
    "FederationTopPlayer": "pink",
}

# Combined plot
plt.figure(figsize=(14, 9))

unclassified_idx = [
    i for i, uri in enumerate(player_uris) if uri not in player_class_map
]
plt.scatter(
    player_2d[unclassified_idx, 0],
    player_2d[unclassified_idx, 1],
    c="lightgrey",
    alpha=0.2,
    s=8,
    label="Unclassified",
)

for cls, color in colors.items():
    idx = [
        i for i, uri in enumerate(player_uris) if cls in player_class_map.get(uri, [])
    ]
    if idx:
        plt.scatter(
            player_2d[idx, 0], player_2d[idx, 1], c=color, alpha=0.8, s=20, label=cls
        )

plt.title("Player Embeddings — t-SNE (coloured by class)")
plt.legend(loc="best", fontsize=8)
plt.savefig("player_tsne_coloured.png", dpi=150)
plt.show()
print("Saved player_tsne_coloured.png")

# Individual plots per class
for cls, color in colors.items():
    idx = [
        i for i, uri in enumerate(player_uris) if cls in player_class_map.get(uri, [])
    ]
    if not idx:
        continue

    plt.figure(figsize=(14, 9))
    plt.scatter(
        player_2d[unclassified_idx, 0],
        player_2d[unclassified_idx, 1],
        c="lightgrey",
        alpha=0.2,
        s=8,
    )
    plt.scatter(
        player_2d[idx, 0], player_2d[idx, 1], c=color, alpha=0.9, s=40, label=cls
    )
    plt.title(f"Player Embeddings — {cls}")
    plt.legend(fontsize=10)
    plt.savefig(f"tsne_{cls}.png", dpi=150)
    plt.close()
    print(f"Saved tsne_{cls}.png")
