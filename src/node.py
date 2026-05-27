import subprocess
from state import AgentState, PlanOutput, ReviewOutput
from config import llm

def planner_agent(state: AgentState):

    prompt = f"""
    Break the user request into executable coding steps.

    USER TASK:
    {state["user_task"]}

    Return short task list.
    """

    structured_llm = llm.with_structured_output(PlanOutput)

    result = structured_llm.invoke(prompt)

    return {"plan": result.tasks}


def task_selector_agent(state: AgentState):

    idx = state["current_task_index"]

    if idx >= len(state["plan"]):
        return {"current_task": "DONE"}

    return {"current_task": state["plan"][idx]}


def coder_agent(state: AgentState):

    prompt = f"""
    Generate executable python code.

    USER ORIGINAL TASK:
    {state["user_task"]}

    CURRENT TASK:
    {state["current_task"]}

    IMPORTANT:
    - Generate code ONLY for CURRENT TASK
    - Return ONLY python code
    - No markdown
    - No explanations
    - Code must run directly
    """

    response = llm.invoke(prompt)

    code = response.content.strip()

    code = code.replace("```python", "")
    code = code.replace("```", "")

    return {"generated_code": code}


def executor_agent(state: AgentState):

    code = state["generated_code"]

    with open("generated_script.py", "w", encoding="utf-8") as f:
        f.write(code)

    try:

        result = subprocess.run(
            ["python", "generated_script.py"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = f"""
STDOUT:
{result.stdout}

STDERR:
{result.stderr}
"""

        return {"execution_output": output}

    except Exception as e:

        return {"execution_output": str(e)}


def reviewer_agent(state: AgentState):

    prompt = f"""
    Review execution result.

    TASK:
    {state["current_task"]}

    OUTPUT:
    {state["execution_output"]}

    Decide:
    - Was task completed correctly?
    - Any runtime errors?
    - Any syntax issues?

    Return structured output.
    """

    structured_llm = llm.with_structured_output(ReviewOutput)

    result = structured_llm.invoke(prompt)

    return {"success": result.success, "review_feedback": result.feedback}


def fixer_agent(state: AgentState):

    prompt = f"""
    Fix this python code.

    TASK:
    {state["current_task"]}

    PREVIOUS CODE:
    {state["generated_code"]}

    EXECUTION OUTPUT:
    {state["execution_output"]}

    REVIEW FEEDBACK:
    {state["review_feedback"]}

    RULES:
    - Return ONLY fixed python code
    - No markdown
    - No explanations
    """

    response = llm.invoke(prompt)

    fixed_code = response.content.strip()

    fixed_code = fixed_code.replace("```python", "")
    fixed_code = fixed_code.replace("```", "")

    return {"generated_code": fixed_code, "retry_count": state["retry_count"] + 1}


def result_collector_agent(state: AgentState):

    old_output = state.get("final_output", "")

    combined = f"""
{old_output}

==================================================
TASK:
{state["current_task"]}

RESULT:
{state["execution_output"]}
"""

    return {
        "final_output": combined,
        "current_task_index": state["current_task_index"] + 1,
        "retry_count": 0,
    }
