import subprocess
from typing import TypedDict, List

from dotenv import load_dotenv
from pydantic import BaseModel

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)


class AgentState(TypedDict):
    user_task: str
    plan: List[str]
    current_task: str
    current_task_index: int
    generated_code: str
    execution_output: str
    review_feedback: str
    final_output: str
    success: bool
    retry_count: int


class PlanOutput(BaseModel):
    tasks: List[str]


class ReviewOutput(BaseModel):
    success: bool
    feedback: str


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


MAX_RETRIES = 3


def review_router(state: AgentState):

    if state["success"]:
        return "success"

    if state["retry_count"] >= MAX_RETRIES:
        return "failed"

    return "retry"


def next_task_router(state: AgentState):

    if state["current_task_index"] >= len(state["plan"]):
        return "end"

    return "next"


workflow = StateGraph(AgentState)

workflow.add_node("planner", planner_agent)
workflow.add_node("task_selector", task_selector_agent)
workflow.add_node("coder", coder_agent)
workflow.add_node("executor", executor_agent)
workflow.add_node("reviewer", reviewer_agent)
workflow.add_node("fixer", fixer_agent)
workflow.add_node("collector", result_collector_agent)

workflow.set_entry_point("planner")

workflow.add_edge("planner", "task_selector")
workflow.add_edge("task_selector", "coder")
workflow.add_edge("coder", "executor")
workflow.add_edge("executor", "reviewer")

workflow.add_conditional_edges(
    "reviewer", review_router, {"success": "collector", "retry": "fixer", "failed": END}
)

workflow.add_edge("fixer", "executor")

workflow.add_conditional_edges(
    "collector", next_task_router, {"next": "task_selector", "end": END}
)

app = workflow.compile()


if __name__ == "__main__":

    task = """
    Create a python script that:
    1. get the data from this csv "sample_sales.csv"
    2. find which product has the highest price
    3. find which city has that product
    """

    result = app.invoke(
        {
            "user_task": task,
            "plan": [],
            "current_task": "",
            "current_task_index": 0,
            "generated_code": "",
            "execution_output": "",
            "review_feedback": "",
            "final_output": "",
            "success": False,
            "retry_count": 0,
        }
    )

    print("\n=========== FINAL OUTPUT ===========\n")

    print(result["final_output"])
