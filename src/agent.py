import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from prompts import SYSTEM_PROMPT

# Load local .env environment variables
load_dotenv()

# 1. Define the extremely simple structured response schema
class EducationalPlan(BaseModel):
    response: str = Field(description="The complete educational summary/plan generated for the student.")

# 2. Get LLM parameters from environment variables with defaults
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash-lite")
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.1"))
MODEL_MAX_TOKENS = int(os.getenv("MODEL_MAX_TOKENS", "1000"))
GEMINI_THINKING_BUDGET = int(os.getenv("GEMINI_THINKING_BUDGET", "1024"))

# Initialize the Gemini LLM
model = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL_NAME,
    temperature=MODEL_TEMPERATURE,
    max_tokens=MODEL_MAX_TOKENS,
    thinking_budget=GEMINI_THINKING_BUDGET,
)

from langchain.agents import create_agent
from langchain_exa import ExaSearchResults

# 3. Setup the Exa Search Tool
search_tool = ExaSearchResults(
    exa_api_key=os.environ.get("EXA_API_KEY"),
    num_results=3,
    text_contents_options=True
)
tools = [search_tool]

agent_system_prompt = SYSTEM_PROMPT + """

You are an autonomous Research & Planning Agent. You have access to a neural web search tool (Exa).
You MUST use this search tool to gather real, concrete facts (specific names, dates, events, numbers, metrics) before writing your educational plan.

CRITICAL SEARCH STRATEGY & RULES:

1. NEURAL DECLARATIVE QUERIES ONLY:
   - Exa is a neural, embeddings-based search engine, NOT a keyword Google search. Do not use keywords or questions (e.g., avoid "history of ISS key dates" or "how do volcanoes erupt?").
   - You must use "Link-Continuation" or "Declarative" prompting. Write your query as a natural, authoritative sentence that looks like the text that would immediately lead into a high-quality link perfectly answering the question.
   - Imagine you are writing a blog post or technical article, and are about to link to the answer. Write the words right before that imaginary link.
   - Example style: "Here is a comprehensive, chronological timeline of all key assembly dates and resident astronaut crews on the International Space Station (ISS):"
   - Example style: "Magma rises from the Earth's mantle and causes a volcanic eruption through the following physical mechanisms:"

2. SEARCH FOR THE RAW TRUTH:
   - Do NOT include age or grade filters in your search queries (e.g., avoid "for kids", "for 3rd graders", "elementary level").
   - Search for the raw, rigorous scientific, physical, or historical truth. You (the LLM) are the expert instructional designer—you will translate and simplify these highly accurate facts into K-12 friendly language yourself in the final response.

3. OPTIMIZE SEARCH LATENCY:
   - Perform a maximum of 1 or 2 high-quality, comprehensive searches.
   - Craft your declarative query to be broad and authoritative enough to capture all necessary facts (dates, names, metrics) in a single request, avoiding sequential API bloat.
"""

# 5. Initialize the Agent
# We use create_agent, which creates an agent graph and natively supports response_format.
agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=agent_system_prompt,
    response_format=EducationalPlan,
)

def generate_educational_plan(prompt: str) -> EducationalPlan:
    """
    Generates a structured educational plan by autonomously searching for facts first.
    """
    config = {"configurable": {"thread_id": "planning_session"}}
    response = agent.invoke(
        {"messages": [{"role": "user", "content": prompt}]},
        config=config
    )
    
    # Extract the natively parsed Pydantic model
    structured_res = response.get("structured_response")
    if isinstance(structured_res, EducationalPlan):
        return structured_res
        
    # Fallback just in case
    final_output = response.get("output") or response["messages"][-1].content
    return EducationalPlan(response=str(final_output))

import sys

if __name__ == "__main__":
    # If a prompt is passed as a command-line argument, execute it immediately
    if len(sys.argv) > 1:
        prompt = sys.argv[1]
        print(f"Running agent using model: {GEMINI_MODEL_NAME}...")
        try:
            result = generate_educational_plan(prompt)
            print("\n=== Result Structured Response ===")
            print(result.response)
            print("==================================")
            print("\nTrace synced to LangSmith project: 'educational-assistant'")
        except Exception as e:
            print(f"Error executing agent: {e}")
    else:
        # If no arguments, launch a friendly interactive console
        print("==============================================================")
        print(f"🚀 K-12 Aerospace Agent Console (Model: {GEMINI_MODEL_NAME})")
        print("   All prompts are fully traced & uploaded to LangSmith.")
        print("   Type 'exit' or 'quit' to close the console.")
        print("==============================================================")
        
        while True:
            try:
                prompt = input("\nEnter your aerospace/space query: ").strip()
                if not prompt:
                    continue
                if prompt.lower() in ("exit", "quit"):
                    print("Exiting console. Goodbye!")
                    break
                
                print("\nThinking...")
                result = generate_educational_plan(prompt)
                print("\n=== Result Structured Response ===")
                print(result.response)
                print("==================================")
                print("Trace synced to LangSmith.")
            except (KeyboardInterrupt, EOFError):
                print("\nExiting console. Goodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
