import pandas as pd
from pykeen.triples import TriplesFactory

# # Load and clean
# df = pd.read_csv("chesskg_triples.tsv", sep="\t", header=0, names=["h", "r", "t"])
# df = df.apply(lambda col: col.str.strip("<>"))

# # Save cleaned version
# df.to_csv("chesskg_triples_clean.tsv", sep="\t", index=False, header=False)

# Load into PyKEEN
tf = TriplesFactory.from_path("chesskg_triples_clean.tsv")


# Split
training, testing, validation = tf.split([0.8, 0.1, 0.1], random_state=42)

# Train TransE
from pykeen.pipeline import pipeline

result = pipeline(
    training=training,
    testing=testing,
    validation=validation,
    model="TransE",
    epochs=5,
    random_seed=42,
)

print(result.metric_results.to_df())
