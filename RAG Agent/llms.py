import os
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()
HYPERBOLIC_API_KEY = os.getenv("HYPERBOLIC_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


llmGroq_gpt_oss_20b = ChatGroq(model_name="openai/gpt-oss-20b", temperature=0.7)


llm_hyperbolic_llama_3_70b = ChatOpenAI(
    openai_api_key=HYPERBOLIC_API_KEY,
    openai_api_base="https://api.hyperbolic.xyz/v1",
    model_name="meta-llama/Llama-3.3-70B-Instruct",
)
