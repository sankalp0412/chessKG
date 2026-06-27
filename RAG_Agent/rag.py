import os
import warnings
import socket
import requests
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from prompts import custom_sparql_prompt, qa_prompt
import streamlit as st
import tempfile

from dotenv import load_dotenv

load_dotenv()

warnings.filterwarnings(
    "ignore", category=DeprecationWarning, module="langchain_community"
)

from langchain_community.graphs import OntotextGraphDBGraph
from langchain_community.chains.graph_qa.ontotext_graphdb import OntotextGraphDBQAChain
from llms import (
    llm_hyperbolic_llama_3_70b,
    llm_qwenp7_plus,
    llmGroq_gpt_oss_20b,
    llm_deepseek,
    glm_5p2,
    llm_gpt_oss120_Fireworks,
    llama_groq_3_70b,
    qwen3,
)
import boto3

SPARQL_ENDPOINT = os.getenv(
    "SPARQL_ENDPOINT", "http://localhost:7200/repositories/ChessKG"
)
SPARQL_UPDATE = os.getenv(
    "SPARQL_UPDATE", "http://localhost:7200/repositories/ChessKG/statements"
)

ENV = os.getenv("ENVIRONMENT")
if ENV == "DEV":
    SPARQL_ENDPOINT = "http://localhost:7200/repositories/ChessKG"

    SPARQL_UPDATE = "http://localhost:7200/repositories/ChessKG/statements"

LOCAL_ONTOLOGY_PATH = os.getenv(
    "LOCAL_ONTOLOGY_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "chessKG_Ontology.ttl"),
)


def get_graph_db_chain() -> OntotextGraphDBQAChain:
    if ENV == "DEV":
        tmp_path = LOCAL_ONTOLOGY_PATH
    else:
        s3 = boto3.client("s3")
        with tempfile.NamedTemporaryFile(suffix=".ttl", delete=False) as tmp:
            s3.download_fileobj("chesskg", "chessKG_Ontology.ttl", tmp)
            tmp_path = tmp.name

    graph = OntotextGraphDBGraph(
        query_endpoint=SPARQL_ENDPOINT,
        local_file=tmp_path,
        local_file_format="turtle",
    )

    chain = OntotextGraphDBQAChain.from_llm(
        llm=llama_groq_3_70b,
        graph=graph,
        allow_dangerous_requests=True,
        verbose=True,
        qa_prompt=qa_prompt,
        sparql_generation_prompt=custom_sparql_prompt,
    )
    return chain


def main(question):

    chain = get_graph_db_chain()
    result = chain.invoke(question)
    print(result["result"])


if __name__ == "__main__":
    question = """
    how many players are there with Ratings more than 2750
    """
    main(question)
