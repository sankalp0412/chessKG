import os
import warnings
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from prompts import custom_sparql_prompt, qa_prompt

# Suppress deprecation warning for langchain-community (Ontotext integration not yet migrated to standalone packages)
warnings.filterwarnings(
    "ignore", category=DeprecationWarning, module="langchain_community"
)

# OntotextGraphDBGraph and OntotextGraphDBQAChain are still in langchain-community
# until official standalone integration is released
from langchain_community.graphs import OntotextGraphDBGraph
from langchain_community.chains.graph_qa.ontotext_graphdb import OntotextGraphDBQAChain

# from langchain.chains
load_dotenv()
HYPERBOLIC_API_KEY = os.getenv("HYPERBOLIC_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def main():

    llm = ChatOpenAI(
        openai_api_key=HYPERBOLIC_API_KEY,
        openai_api_base="https://api.hyperbolic.xyz/v1",
        model_name="meta-llama/Llama-3.3-70B-Instruct",
    )

    llmGroq = ChatGroq(model_name="openai/gpt-oss-20b", temperature=0.7)

    graph = OntotextGraphDBGraph(
        query_endpoint="http://localhost:7200/repositories/ChessKG",
        local_file="/Users/sankalpdhupar/Documents/RPTU/Summer 26/Knowledge Graphs/ChessKG/RAG Agent/chessKG_Ontology.ttl",
        local_file_format="turtle",
    )
    chain = OntotextGraphDBQAChain.from_llm(
        llm=llmGroq,
        graph=graph,
        allow_dangerous_requests=True,
        verbose=True,
        qa_prompt=qa_prompt,
        # sparql_generation_prompt=custom_sparql_prompt,
    )
    # print(graph.get_schema)
    result = chain.invoke(
        "For players with rating >= 2700, find their preferred opening as white and calculate their win percentage with that opening."
    )
    print(result["result"])


if __name__ == "__main__":
    main()
