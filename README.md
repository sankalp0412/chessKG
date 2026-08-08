#  ChessKG — An Intelligent Chess Knowledge Graph

> A semantically rich knowledge graph over chess games, players, and openings — built from real PGN data, enriched with OWL/SHACL logical inference, embedded with PyKEEN, and served through a GraphDB + FAISS + LLM RAG agent.

**Grade:** S1 (top mark) — TU Wien *Knowledge Graphs* mini-project, 2026S

---

## Why

Tools like ChessBase are powerful but are, at their core, flat databases: great at filtering and retrieval, unable to reason. They can't answer questions like *"which opening will this player likely use, given stylistic similarity to others?"* or automatically classify a player as an opening specialist based on their game history.

ChessKG builds a real knowledge graph on top of chess data instead — one that supports semantic querying (SPARQL), automatic logical inference (OWL/SHACL), and learned similarity via embeddings (PyKEEN).

| | ChessBase | ChessKG |
|---|---|---|
| Data model | Proprietary flat format, no semantic layer | RDF/OWL ontology with typed relationships |
| Querying | Keyword / filter search | SPARQL — expressive semantic queries |
| Reasoning | None | OWL/SHACL rules infer new facts automatically |
| Similarity / prediction | Not supported | KG embeddings (TransE / RotatE) + FAISS similarity search |
| Interoperability | Closed ecosystem | Open RDF standard |

---

## Architecture

\`\`\`
PGN files (OTB + Lichess)
        │
        ▼
  Postgres (staging / validation layer)
        │
        ▼
  RDF triples (rdflib, chess: namespace + schema.org)
        │
        ▼
     GraphDB  ◄──────────────┐
   (OWL ontology +           │
   SPARQL CONSTRUCT/INSERT   │
   inference rules)          │
        │                    │
        ▼                    │
  PyKEEN (TransE / RotatE)   │
        │                    │
        ▼                    │
  FAISS similarity index     │
        │                    │
        ▼                    │
  LangChain RAG agent ───────┘
  (query_chess_graph + search_similar_entities tools)
        │
        ▼
  Streamlit chat frontend
\`\`\`

**Stack**

| Component | Tool |
|---|---|
| Data source | Lichess open database + OTB PGN archives |
| Staging | PostgreSQL |
| KG store | GraphDB (OWL reasoning + SPARQL) |
| Embeddings | PyKEEN — TransE & RotatE |
| Vector search | FAISS |
| Logical layer | OWL + SPARQL CONSTRUCT/INSERT rules |
| Application layer | LangChain RAG agent (GraphDB facts + FAISS similarity) |
| Frontend | Streamlit |
| Hosting | AWS EC2 (GraphDB + agent), AWS S3 (embeddings/index/ontology) |
| Automation | GitHub Actions (monthly ratings refresh) |

---

## The Knowledge Graph

**Scale:** ~89k merged & deduplicated games → ~1.1M RDF triples, ~6,800 unique players, ~440 unique openings across 492 ECO codes.

**Core ontology** (`chess:` namespace): `Player`, `Game`, `Opening`, `EcoCode`, `Termination`, linked via properties like `whitePlayer`, `blackPlayer`, `openingPlayed`, `ecoCode`, `termination`, `standardRating`, `federation`, `title`.

### Inferred classes (OWL subclass + SPARQL rule pipeline)

| Class | Rule |
|---|---|
| `OpeningSpecialist` | ≥10 games with an opening, ≥50% win rate |
| `ElitePlayer` | Standard rating ≥ 2650 |
| `SuperGM` | Standard rating ≥ 2700 (subclass of `ElitePlayer`) |
| `FederationTopPlayer` | Top 5 rated players per federation |
| `EndgameSpecialist` | Score% ≥ 50% across ≥200 games longer than 40 moves |
| `Underdog` | Untitled/FM/CM/WFM/WIM/WGM with ≥3 wins vs. GMs and ≥50% score against them |
| `DecisivePlayer` | (wins + losses) / total ≥ 75% across ≥50 games |

### Inferred relationships

`dominates`, `rivals` (symmetric), `preferredOpeningAsWhite` / `preferredOpeningAsBlack`, `mostPlayedAgainst`, `evenlyMatches` (symmetric), `stylesSimilarTo` (symmetric — shared preferred openings as both colors).

Validated against real chess knowledge, e.g. endgame score%: Bacrot 68%, Carlsen 65.5%, Kramnik 57% — all match known player reputations.

---

## Embeddings & Similarity

| Model | Loss | MRR |
|---|---|---|
| TransE | 0.0512 | 0.038 |
| RotatE | 0.0219 | **0.105** |

RotatE outperforms TransE by 2.7x and is used for all downstream similarity work (since the graph is complete by construction, embeddings here drive *player/opening similarity clustering*, not link prediction).

- t-SNE projection shows elite players and SuperGMs clustering tightly, with underdogs forming a distinct separate cluster — playing style emerges from graph structure alone, without label supervision.
- FAISS (`IndexFlatL2`, 400-dim real+imaginary RotatE vectors) powers nearest-neighbor similarity search — e.g. querying Carlsen returns Caruana, Nepomniachtchi, Nakamura, Aronian.

---

## RAG Agent

A LangChain agent sits on top of the graph with two tools:
- **`query_chess_graph`** — generates and runs SPARQL against GraphDB for exact factual queries
- **`search_similar_entities`** — FAISS similarity search over RotatE embeddings

The agent decides which tool(s) to call per question and can combine both in a single answer (e.g. *"who plays a similar style to the highest-rated Uzbek blitz player?"* pulls a live rating fact + an embedding similarity lookup). It also has a `get_latest_ratings` tool pulling live FIDE ratings from the Lichess API, and cites which tools it used in its response.

---

## KG Evolution

The graph isn't static — player ratings update monthly:
- `evolution.py` fetches current FIDE/Lichess ratings for all ~6,260 players (threaded, ~32 min)
- SPARQL `DELETE`/`INSERT` pushes updated `standardRating`, `rapidRating`, `blitzRating` into GraphDB (~55s)
- A GitHub Actions workflow (`.github/workflows/update_ratings.yml`) runs this automatically on the 1st of every month against the hosted GraphDB endpoint

---

## Deployment

- GraphDB + the RAG agent run on an AWS EC2 instance
- Embeddings, FAISS index, and the ontology TTL are stored in S3 and pulled at runtime via `boto3`
- Streamlit provides the chat frontend, pointing at the EC2 GraphDB endpoint

---

## Learning Outcomes Coverage

Built for the TU Wien *Knowledge Graphs* course (6 ECTS). Deep focus on **KG Embeddings** and **Logical Knowledge in KGs**; basic proficiency across architectures, KG creation, scalable reasoning, KG evolution, real-world applications, services, and KG/AI/ML connections. Financial KGs touched lightly via tournament data; Graph Neural Networks explicitly out of scope.

**Result: S1** 🎉

---

## Data Sources

- [Lichess open database](https://database.lichess.org/) (PGN)
- [AJ-OTB-000](https://ajedrezdata.com/databases/otb/over-the-board-database-aj-otb-000/) — over-the-board games archive
- [Lichess FIDE API](https://lichess.org/api) — live ratings, titles, federations
