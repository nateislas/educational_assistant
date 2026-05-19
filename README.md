# Improving AI Output Quality

A system to generate structured, grounded, K-12 educational plans for AR/VR/MR learning modules.

The repository implements a search and planning agent using Gemini 2.5 Flash and Exa Search, evaluated via an LLM-as-a-Judge pipeline on LangSmith.

---

## Project Architecture

- **Search Agent**: Built using LangChain and LangGraph. The agent takes a topic input, executes web searches using Exa to retrieve facts, and outputs a plan structured via a Pydantic schema.
- **Evaluation Pipeline**: Uses an LLM judge to evaluate plans across five metrics (Clarity and Structure, Tone and Grade Appropriateness, Factuality and Groundedness, Actionability and Completeness, and Instruction Following). The evaluator contains constraints to penalize placeholders.

---

## File Structure

```text
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── README.md
├── docs
│   ├── DESIGN.md
│   └── FINAL_SUBMISSION.md
└── src
    ├── __init__.py
    ├── agent.py         # Agent graph definition and execution logic
    ├── prompts.py       # System prompts and few-shot examples
    └── evals
        ├── __init__.py
        ├── eval.py      # LangSmith evaluation setup and judge rubric
        ├── test_queries.json   # Baseline evaluation queries
        └── golden_queries.json # Benchmark queries
```

---

## Execution Instructions

### 1. Environment Configuration
Populate `.env` with API credentials:
```env
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=educational-assistant
GOOGLE_API_KEY=your_gemini_api_key
EXA_API_KEY=your_exa_api_key
```

### 2. Interactive Agent Console
Execute the interface to prompt the agent:
```bash
docker compose run --rm agent python src/agent.py
```

### 3. Evaluation Suite (Baseline Dataset)
Execute the evaluator against the test queries:
```bash
docker compose run --rm agent python src/evals/eval.py
```

### 4. Evaluation Suite (Benchmark Dataset)
Execute the evaluator against the benchmark queries:
```bash
docker compose run --rm -e EVAL_QUERIES_FILE=golden_queries.json -e EVAL_DATASET_NAME=educational-assistant-golden agent python src/evals/eval.py
```
