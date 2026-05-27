# CodeForgeGraph

CodeForgeGraph is a small LangGraph-based Python project that turns a user request into an automated coding workflow. It plans tasks, generates Python code, executes the code, reviews the result, and retries when needed.

## Features

- Task planning and decomposition
- Code generation for each step
- Execution and output capture
- Review and retry loop for failed runs
- Simple CLI entry point via `src/main.py`

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- A Groq API key in a `.env` file

## Installation with uv

1. Install uv if you do not already have it:

   - macOS/Linux:
     ```sh
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   - Windows (PowerShell):
     ```powershell
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```

2. Clone the repository and move into it:

   ```sh
   git clone <your-repo-url>
   cd CodeForgeGraph
   ```

3. Create the environment and install dependencies:

   ```sh
   uv sync
   ```

4. Create a `.env` file in the project root and add your Groq key:

   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

## Running the project

Run the application with:

```sh
uv run python src/main.py
```

This starts the workflow defined in `src/main.py` and prints the final generated result.

## Project structure

- `src/main.py` — workflow setup and entry point
- `src/node.py` — LangGraph agents for planning, coding, execution, review, and fixing
- `src/state.py` — typed state definitions
- `src/config.py` — LLM configuration
- `src/sample_sales.csv` — sample input data for the demo task

## Notes

- The current demo task in `src/main.py` asks the system to analyze the sample CSV and report the highest-priced product and its city.
- If you want to change the prompt or workflow, update the task string in `src/main.py`.
