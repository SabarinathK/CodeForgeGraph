from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from node import (
    planner_agent,
    task_selector_agent,
    coder_agent,
    executor_agent,
    reviewer_agent,
    fixer_agent,
    result_collector_agent,
)
from state import AgentState, PlanOutput, ReviewOutput

load_dotenv()




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
