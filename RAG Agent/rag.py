import os
import warnings
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from prompts import custom_sparql_prompt, qa_prompt

warnings.filterwarnings(
    "ignore", category=DeprecationWarning, module="langchain_community"
)

from langchain_community.graphs import OntotextGraphDBGraph
from langchain_community.chains.graph_qa.ontotext_graphdb import OntotextGraphDBQAChain
from llms import llm_hyperbolic_llama_3_70b, llmGroq_gpt_oss_20b


def get_graph_db_chain() -> OntotextGraphDBQAChain:

    graph = OntotextGraphDBGraph(
        query_endpoint="http://localhost:7200/repositories/ChessKG",
        local_file="/Users/sankalpdhupar/Documents/RPTU/Summer 26/Knowledge Graphs/ChessKG/RAG Agent/chessKG_Ontology.ttl",
        local_file_format="turtle",
    )
    chain = OntotextGraphDBQAChain.from_llm(
        llm=llmGroq_gpt_oss_20b,
        graph=graph,
        allow_dangerous_requests=True,
        verbose=True,
        qa_prompt=qa_prompt,
        sparql_generation_prompt=custom_sparql_prompt,
    )
    return chain


def main(question):

    chain = get_graph_db_chain()
    # print(graph.get_schema)
    result = chain.invoke(question)
    print(result["result"])


if __name__ == "__main__":
    question = """
    For players with rating >= 2700, find their preferred opening as white and calculate their win percentage with that opening.
    """
    main(question)
