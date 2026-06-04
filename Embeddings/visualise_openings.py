import numpy as np
import json
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
import pandas as pd

# Load embeddings and entity mapping
embeddings = np.load("entity_embeddings.npy")
with open("entity_to_id.json", "r") as f:
    entity_to_id = json.load(f)

id_to_entity = {v: k for k, v in entity_to_id.items()}

# Filter only opening entities
opening_indices = [idx for uri, idx in entity_to_id.items() if "opening_" in uri]
opening_uris = [id_to_entity[idx] for idx in opening_indices]
opening_embeddings = np.concatenate(
    [embeddings[opening_indices].real, embeddings[opening_indices].imag], axis=1
)

print(f"Found {len(opening_indices)} openings")

# Run t-SNE
tsne = TSNE(n_components=2, random_state=42, perplexity=10)
opening_2d = tsne.fit_transform(opening_embeddings)

# Load ECO codes
eco_df = pd.read_csv("openings_eco.tsv", sep="\t", header=0, names=["opening", "eco"])
eco_df["opening"] = eco_df["opening"].str.strip("<>")
eco_df["eco"] = (
    eco_df["eco"].str.strip("<>").str.replace("https://ChessGameKG.org/eco_", "")
)

# Get first ECO code per opening, extract category (first letter)
eco_map = {}
for _, row in eco_df.iterrows():
    uri = row["opening"]
    if uri not in eco_map:
        eco_map[uri] = row["eco"][0]  # A, B, C, D, or E

# Colours per ECO category
colors = {"A": "blue", "B": "red", "C": "green", "D": "orange", "E": "purple"}
labels = {
    "A": "A (Flank openings)",
    "B": "B (Semi-open)",
    "C": "C (Open)",
    "D": "D (Closed)",
    "E": "E (Indian)",
}

# Plot
plt.figure(figsize=(14, 9))

for cat, color in colors.items():
    idx = [i for i, uri in enumerate(opening_uris) if eco_map.get(uri) == cat]
    if idx:
        plt.scatter(
            opening_2d[idx, 0],
            opening_2d[idx, 1],
            c=color,
            alpha=0.8,
            s=40,
            label=labels[cat],
        )

# Add opening name labels for a few points
for i, uri in enumerate(opening_uris[:20]):
    name = uri.replace("https://ChessGameKG.org/opening_", "").replace("_", " ")
    plt.annotate(name, (opening_2d[i, 0], opening_2d[i, 1]), fontsize=5, alpha=0.7)

plt.title("Opening Embeddings — t-SNE (coloured by ECO category)")
plt.legend(loc="best", fontsize=9)
plt.savefig("opening_tsne.png", dpi=150)
plt.show()
print("Saved opening_tsne.png")
