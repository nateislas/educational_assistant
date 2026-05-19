import os
import sys

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from models import EducationalPlan
from prompts import AGENT_SYSTEM_PROMPT
from tools import exa_search_tool

# Load local .env environment variables
load_dotenv()

# 1. Get LLM parameters from environment variables with defaults
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash-lite")
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.1"))
MODEL_MAX_TOKENS = int(os.getenv("MODEL_MAX_TOKENS", "1000"))
GEMINI_THINKING_BUDGET = int(os.getenv("GEMINI_THINKING_BUDGET", "1024"))

# 2. Initialize the Gemini LLM
model = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL_NAME,
    temperature=MODEL_TEMPERATURE,
    max_tokens=MODEL_MAX_TOKENS,
    thinking_budget=GEMINI_THINKING_BUDGET,
)

# 3. Setup the Exa Search Tool
tools = [exa_search_tool]

# 4. Initialize the Agent
# We use create_agent, which creates an agent graph and natively supports response_format.
agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=AGENT_SYSTEM_PROMPT,
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
        print(f"🚀 K-12 Educational Agent Console (Model: {GEMINI_MODEL_NAME})")
        print("   All prompts are fully traced & uploaded to LangSmith.")
        print("   Type 'exit' or 'quit' to close the console.")
        print("==============================================================")
        
        while True:
            try:
                prompt = input("\nEnter your educational query: ").strip()
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
