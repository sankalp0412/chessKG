import os
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_fireworks import ChatFireworks

load_dotenv()

HYPERBOLIC_API_KEY = os.getenv("HYPERBOLIC_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if "FIREWORKS_API_KEY" in os.environ:
    FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")

llmGroq_gpt_oss_20b = ChatGroq(
    model_name="openai/gpt-oss-20b",
    temperature=0,
    max_tokens=400,
)
llama_groq_3_70b = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0,
    max_tokens=400,
)


llm_hyperbolic_llama_3_70b = ChatOpenAI(
    openai_api_key=HYPERBOLIC_API_KEY,
    openai_api_base="https://api.hyperbolic.xyz/v1",
    model_name="meta-llama/Llama-3.3-70B-Instruct",
    temperature=0,
    max_tokens=400,
)

llm_deepseek = ChatFireworks(
    model="accounts/fireworks/models/deepseek-v4-pro",
    temperature=0,
    max_tokens=512,
    timeout=None,
    max_retries=2,
)
llm_gpt_oss120_Fireworks = ChatFireworks(
    model="accounts/fireworks/models/gpt-oss-120b",
    temperature=0.7,
    max_tokens=512,
    timeout=None,
    max_retries=2,
)

llm_qwenp7_plus = ChatFireworks(
    model="accounts/fireworks/models/qwen3p7-plus",
    temperature=0,
    max_tokens=400,
    timeout=None,
    max_retries=2,
)
glm_5p2 = ChatFireworks(
    model="accounts/fireworks/models/glm-5p2",
    temperature=0,  # for query generation
    max_tokens=400,
    timeout=None,
    max_retries=2,
)

qwen3 = ChatFireworks(
    model="accounts/fireworks/models/qwen3-235b-a22b-instruct-2507",
    temperature=0,  # for query generation
    max_tokens=400,
    timeout=None,
    max_retries=2,
)


if __name__ == "__main__":
    from langchain_core.messages import HumanMessage

    print("[Test] Invoking deepseek with a simple prompt...")
    try:
        response = llm_deepseek.invoke([HumanMessage(content="What is 2 + 2?")])
        print(response.content_blocks)
        print(f"[Success] Response: {response.content}")
    except Exception as e:
        print(f"[Error] Failed to invoke LLM: {e}")
