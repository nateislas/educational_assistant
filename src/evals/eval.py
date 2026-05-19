import sys
import os
import json
from dotenv import load_dotenv

# Inject parent directory (src/) to the python search path so it can import agent and prompts
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langsmith import Client
from langsmith.evaluation import evaluate
from langchain_google_genai import ChatGoogleGenerativeAI
from agent import generate_educational_plan
from prompts import SYSTEM_PROMPT

load_dotenv()

# Initialize the Gemini judge model, parameterizing the model name via GEMINI_LLM_JUDGE environment variable
GEMINI_LLM_JUDGE = os.getenv("GEMINI_LLM_JUDGE", "gemini-3.1-flash-lite")
judge_model = ChatGoogleGenerativeAI(
    model=GEMINI_LLM_JUDGE,
    temperature=0.1,
    max_tokens=1000,
)

# Define the LLM-as-a-Judge prompt that grades based on our rubrics
JUDGE_SYSTEM_PROMPT = """You are an expert educational curriculum evaluator specializing in K-12 Aerospace and Space sciences. 
Your task is to grade the generated "Educational Plan" against the given "User Prompt".

You must grade the educational plan on a 1-5 scale (where 1 is poor and 5 is excellent) across these four dimensions:
1. clarity_and_structure (formatting, bullet points, scanning ease)
2. tone_and_grade_appropriateness (engaging, educational, K-12 student-friendly)
3. factuality_and_groundedness (factual accuracy, no scientific or historical hallucinations, matches established aerospace principles)
4. completeness_and_usefulness (actionable learning plan depth, covers core concepts)

Provide your final score as a JSON object with keys:
"clarity_and_structure": <int>,
"tone_and_grade_appropriateness": <int>,
"factuality_and_groundedness": <int>,
"completeness_and_usefulness": <int>,
"reasoning": "<short string explaining your grading rationale>"
"""


def llm_judge_evaluator(run, example) -> dict:
    """
    Custom LangSmith LLM-as-a-Judge evaluator.
    """
    user_prompt = example.inputs.get("prompt")
    generated_plan = run.outputs.get("response")

    judge_prompt = f"""
[User Prompt]:
{user_prompt}

[Generated Educational Plan]:
{generated_plan}

Please evaluate the generated plan based on the criteria. Output your evaluation ONLY in the requested JSON format.
"""

    # We use our configured Gemini model as the judge
    messages = [("system", JUDGE_SYSTEM_PROMPT), ("human", judge_prompt)]

    # Call Gemini model
    try:
        response = judge_model.invoke(messages)
        # Parse the JSON response safely (handling string or list content types)
        content = response.content
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, str):
                    parts.append(part)
                elif isinstance(part, dict) and "text" in part:
                    parts.append(part["text"])
            clean_text = "".join(parts)
        else:
            clean_text = str(content)

        clean_text = (
            clean_text.strip().replace("```json", "").replace("```", "").strip()
        )
        scores = json.loads(clean_text)

        return {
            "results": [
                {
                    "key": "clarity_and_structure",
                    "score": scores.get("clarity_and_structure"),
                },
                {
                    "key": "tone_and_grade_appropriateness",
                    "score": scores.get("tone_and_grade_appropriateness"),
                },
                {
                    "key": "factuality_and_groundedness",
                    "score": scores.get("factuality_and_groundedness"),
                },
                {
                    "key": "completeness_and_usefulness",
                    "score": scores.get("completeness_and_usefulness"),
                },
                {
                    "key": "judge_reasoning",
                    "score": None,
                    "value": scores.get("reasoning"),
                },
            ]
        }
    except Exception as e:
        print(f"Error during LLM judging: {e}")
        return {"results": [{"key": "judging_failed", "score": 1, "value": str(e)}]}


def main():
    client = Client()
    dataset_name = "educational-assistant-baseline"

    # Bootstrapping dataset if missing
    if not client.has_dataset(dataset_name=dataset_name):
        print(f"Creating baseline dataset '{dataset_name}' in LangSmith...")
        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description="Baseline evaluations for K-12 Aerospace and Space Science educational experience prompts.",
        )

        # Load the 10 static K-12 aerospace/space queries from test_queries.json
        queries_path = os.path.join(os.path.dirname(__file__), "test_queries.json")
        try:
            with open(queries_path, "r") as f:
                seed_cases = json.load(f)
            
            for case in seed_cases:
                client.create_example(
                    inputs={"prompt": case["prompt"]},
                    outputs=None,
                    dataset_id=dataset.id,
                )
            print(f"Dataset seeded successfully with {len(seed_cases)} K-12 aerospace/space queries!")
        except Exception as e:
            print(f"Error loading or seeding static queries: {e}")
            exit(1)
    else:
        print(f"Dataset '{dataset_name}' already exists in LangSmith.")

    # Define target task function for evaluation
    def evaluate_task(inputs: dict) -> dict:
        prompt = inputs.get("prompt")
        result = generate_educational_plan(prompt)
        return {"response": result.response}

    print("Starting LangSmith evaluation run with custom LLM-as-a-Judge...")
    results = evaluate(
        evaluate_task,
        data=dataset_name,
        evaluators=[llm_judge_evaluator],  # Native LLM-as-a-judge
        experiment_prefix="gemini-baseline",
    )
    print(
        "Evaluation completed! Check your LangSmith dashboard to view the rubric scores."
    )


if __name__ == "__main__":
    if not os.environ.get("LANGCHAIN_API_KEY"):
        print(
            "WARNING: LANGCHAIN_API_KEY is not set. Evals will run locally but won't sync to LangSmith."
        )
    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
        print(
            "ERROR: GEMINI_API_KEY or GOOGLE_API_KEY must be set to run Google GenAI models."
        )
        exit(1)

    main()
