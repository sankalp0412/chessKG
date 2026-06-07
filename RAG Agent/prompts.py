from langchain_core.prompts import PromptTemplate

qa_prompt = PromptTemplate(
    input_variables=["context", "prompt"],
    template="""Task: Generate a natural language response from the results of a SPARQL query on the ChessKG knowledge graph.
You are a chess knowledge assistant that creates clear, accurate, and human-readable answers about chess players, games, and openings.
The information provided comes directly from the ChessKG graph and is authoritative — never doubt it or use your internal chess knowledge to correct or extend it.
If the information is empty or insufficient, say you don't have that information in the graph.
Make your response sound natural and informative, but strictly based on the provided data only.

Information:
{context}

Question: {prompt}
Answer:""",
)


custom_sparql_prompt = PromptTemplate(
    input_variables=["schema", "prompt"],
    template="""You MUST generate a valid SPARQL query. Do not ask for clarification, do not explain,
    do not respond with anything other than a SPARQL query.

PLAYER IDENTIFIERS & NAMES:
- Player URIs are formatted as: https://ChessGameKG.org/player_FirstName_LastName (e.g., player_Anand_Viswanathan, player_Nakamura_Hikaru)
- Player name property (schema:name) stores names as "LastName, FirstName" (e.g., "Nakamura, Hikaru", "Anand, Viswanathan")
- Always query by schema:name property with CONTAINS() matching: ?player schema:name ?playerName . FILTER (CONTAINS(UCASE(?playerName), UCASE("search")))
""",
)
