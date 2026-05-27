from typing import TypedDict, List
from pydantic import BaseModel

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
