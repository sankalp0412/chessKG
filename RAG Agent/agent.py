from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from rag import get_graph_db_chain
from langchain_core.prompts import PromptTemplate
from llms import llmGroq_gpt_oss_20b
import numpy as np
import json
import faiss
from typing import Dict
import requests
from dotenv import load_dotenv
import os
from prompts import agent_prompt

load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = "ChessKG"

index = faiss.read_index("../Embeddings/chesskg.index")
with open("../Embeddings/entity_to_id.json") as f:
    entity_to_id = json.load(f)
id_to_entity = {str(v): k for k, v in entity_to_id.items()}
embeddings = np.load("../Embeddings/entity_embeddings.npy")
embeddings_real = np.concatenate([embeddings.real, embeddings.imag], axis=1).astype(
    "float32"
)


@tool
def search_similar_entities(entity_name: str, entity_type: str = "") -> str:
    """Search for similar players or openings in the chess knowledge graph using embedding similarity.
    Use this for questions about similarity, style, recommendations, or clustering.

    The entity_name parameter should be a partial name that matches a player or opening URI.
    For players: pass the last name only (e.g., 'Carlsen', 'Nakamura', 'Nepomniachtchi')
    For openings: pass a keyword from the opening name (e.g., 'Sicilian', 'English', 'Caro')
    URIs are formatted as player_LastName_FirstName or opening_Name_Variation.

    Args:
        entity_name: partial name to search
        entity_type: optional filter — pass 'player_' for players, 'opening_' for openings.
                     Leave empty to search all entity types.
    """
    matches = [
        (uri, idx)
        for uri, idx in entity_to_id.items()
        if entity_type.lower() in uri.lower() and entity_name.lower() in uri.lower()
    ]
    if not matches:
        return f"Entity '{entity_name}' not found."

    uri, idx = matches[0]
    query_vector = embeddings_real[int(idx)].reshape(1, -1)
    distances, indices = index.search(query_vector, 6)

    results = []
    for i in indices[0]:
        entity = id_to_entity.get(str(int(i)))
        if not entity:
            continue
        if entity != uri:
            # Convert URI tail to a human-friendly canonical name.
            # player_Anand_Viswanathan -> Anand, Viswanathan
            tail = entity.split("/")[-1]
            if tail.startswith("player_"):
                parts = tail.replace("player_", "", 1).split("_", 1)
                if len(parts) == 2:
                    name = f"{parts[0]}, {parts[1]}"
                else:
                    name = tail.replace("_", " ")
            else:
                name = tail.replace("_", " ")
            results.append(name)
    return f"Entities most similar to {entity_name}: {', '.join(results)}"


@tool
def query_chess_graph(question: str) -> str:
    """Query the chess knowledge graph for factual information about players, games, openings,
    ratings, results, tournaments. Use for specific facts and statistics."""
    graphdb_chain = get_graph_db_chain()
    return graphdb_chain.invoke(question)["result"]


@tool
def get_latest_ratings(player_name: str) -> list[Dict] | Dict:
    """Fetches the latest FIDE ratings for a player from the Lichess FIDE API.

    Use this when the user asks for current/latest ratings or wants to update a player's rating.

    NOTE: The Lichess FIDE API searches by name substring and may return multiple close matches.
    Always verify the returned player matches the intended player before using the data.
    And dont spam the API.


    Args:
        player_name: Full or partial player name to search (e.g., "Carlsen" or "Magnus Carlsen")

    Returns:
        Dict containing matched players (top 5 matches) with their current standard, rapid and blitz ratings.
        Returns error message string if the API call fails or no player is found.
    """

    url = "https://lichess.org/api/fide/player"

    try:

        response = requests.get(url, params={"q": player_name}, timeout=10)
        if not response.text.strip():
            return {"response": "Failed to fetch information from Lichess API."}

        data = response.json()

        result = [
            {
                "fideId": player["id"],
                "standardRating": player.get("standard", None),
                "fideName": player.get("name"),
                "rapid": player.get("rapid", None),
                "blitz": player.get("blitz", None),
            }
            for player in data[:5]
        ]

        return result
    except Exception as e:
        return {"response": f"Error while fetching information from Lichess API:{e}"}


# Create agent with both tools
tools = [search_similar_entities, query_chess_graph, get_latest_ratings]

agent_prompt = PromptTemplate.from_template(agent_prompt)

agent = create_tool_calling_agent(llmGroq_gpt_oss_20b, tools, agent_prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


def ask_chess_agent(question: str, chat_history=None) -> str:
    """Run a question through the chess agent and return only final text output."""
    if chat_history is None:
        chat_history = []

    result = agent_executor.invoke(
        {
            "input": question,
            "chat_history": chat_history,
        }
    )
    return result.get("output", "No response returned.")


if __name__ == "__main__":
    test_question = (
        "Who plays similarly to Vidit Gujrati and what is their rating, "
        "and did one of them dominate the other?"
    )
    print(ask_chess_agent(test_question, chat_history=[]))
