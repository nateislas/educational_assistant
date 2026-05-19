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

# 3. Bind structured output
structured_llm = model.with_structured_output(EducationalPlan)

def generate_educational_plan(prompt: str) -> EducationalPlan:
    """
    Generates a structured educational plan from a VR/AR/MR experience description.
    """
    messages = [
        ("system", SYSTEM_PROMPT),
        ("human", prompt)
    ]
    
    return structured_llm.invoke(messages)

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
