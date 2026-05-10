import os, json
from typing import Annotated, TypedDict, List, Dict, Any
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

load_dotenv()

BATCH_SIZE   = 4
MAX_REGRADES = 2

class AgentState(TypedDict):
    messages:      Annotated[List[BaseMessage], add_messages]
    documents:     List[Dict[str, str]]
    question:      str
    rubric:        str
    batches:       List[List[Dict[str, str]]]
    batch_index:   int
    current_batch: List[Dict[str, str]]
    marks:         List[Dict[str, Any]]
    critic_result: Dict[str, Any]
    decision:      str
    regrade_count: int
    final_marks:   List[Dict[str, Any]]

llm = ChatDeepSeek(model="deepseek-chat", temperature=0)

def call_json(system_prompt, user_prompt):
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
    content  = response.content.strip()
    if content.startswith("```"):
        content = content.split("```")[1].strip()
        if content.startswith("json"):
            content = content[4:].strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM returned non-JSON:\n{response.content}\nError: {e}")

def batch_handler(state):
    docs    = state["documents"]
    batches = [docs[i:i+BATCH_SIZE] for i in range(0, len(docs), BATCH_SIZE)]
    return {
        "batches": batches, "batch_index": 0,
        "current_batch": batches[0] if batches else [],
        "marks": [], "critic_result": {}, "decision": "",
        "regrade_count": 0, "final_marks": [],
        "messages": [HumanMessage(content=f"Created {len(batches)} batches.")],
    }

def grader(state):
    system_prompt = """You are the GRADER AGENT. Grade each student answer from 1 to 10.
Return ONLY raw JSON:
{"marks": [{"stdno": "S001", "mark": 8, "lost_marks_reason": ["reason"]}]}"""

    critic_feedback = ""
    if state.get("critic_result") and state["regrade_count"] > 0:
        issues = state["critic_result"].get("issues", [])
        if issues:
            critic_feedback = f"\nCritic issues to fix:\n{json.dumps(issues, indent=2)}"

    user_prompt = (
        f"Question:\n{state['question']}\n\n"
        f"Rubric:\n{state['rubric']}\n\n"
        f"Students:\n{json.dumps(state['current_batch'], indent=2)}"
        f"{critic_feedback}"
    )
    result = call_json(system_prompt, user_prompt)
    return {"marks": result["marks"], "messages": [HumanMessage(content="Graded.")]}

def critic(state):
    system_prompt = """You are the CRITIC AGENT. Check if marks follow the rubric.
Return ONLY raw JSON:
{"approved": true, "issues": [], "confidence": 0.9}"""

    user_prompt = (
        f"Question:\n{state['question']}\n\n"
        f"Rubric:\n{state['rubric']}\n\n"
        f"Students:\n{json.dumps(state['current_batch'], indent=2)}\n\n"
        f"Marks:\n{json.dumps(state['marks'], indent=2)}"
    )
    result = call_json(system_prompt, user_prompt)
    return {"critic_result": result, "messages": [HumanMessage(content="Critic done.")]}

def supervisor(state):
    approved      = state["critic_result"].get("approved", False)
    regrade_count = state["regrade_count"]
    if regrade_count == 0:
        decision, regrade_count = "regrade", 1
    elif approved:
        decision = "accept"
    elif regrade_count < MAX_REGRADES:
        decision, regrade_count = "regrade", regrade_count + 1
    else:
        decision = "accept"
    return {
        "decision":      decision,
        "regrade_count": regrade_count,
        "messages":      [HumanMessage(content=f"Decision: {decision}")],
    }

def save_result(state):
    accumulated = state.get("final_marks") or []
    return {"final_marks": accumulated + state["marks"], "messages": [HumanMessage(content="Saved batch.")]}

def batch_controller(state):
    next_index = state["batch_index"] + 1
    if next_index < len(state["batches"]):
        return {
            "batch_index": next_index, "current_batch": state["batches"][next_index],
            "marks": [], "critic_result": {}, "decision": "", "regrade_count": 0,
            "messages": [HumanMessage(content=f"Next batch {next_index + 1}.")],
        }
    return {"current_batch": [], "messages": [HumanMessage(content="All done.")]}

def route_supervisor(state):
    return "grader" if state["decision"] == "regrade" else "save_result"

def route_batch(state):
    return "grader" if state["current_batch"] else END

# Build graph
workflow = StateGraph(AgentState)
for name, fn in [
    ("batch_handler",    batch_handler),
    ("grader",           grader),
    ("critic",           critic),
    ("supervisor",       supervisor),
    ("save_result",      save_result),
    ("batch_controller", batch_controller),
]:
    workflow.add_node(name, fn)

workflow.set_entry_point("batch_handler")
workflow.add_edge("batch_handler", "grader")
workflow.add_edge("grader",        "critic")
workflow.add_edge("critic",        "supervisor")
workflow.add_conditional_edges("supervisor",       route_supervisor, {"grader": "grader", "save_result": "save_result"})
workflow.add_edge("save_result",   "batch_controller")
workflow.add_conditional_edges("batch_controller", route_batch,      {"grader": "grader", END: END})

app = workflow.compile()

def run_grader(documents, rubric, question):
    result = app.invoke({
        "messages": [], "documents": documents, "question": question, "rubric": rubric,
        "batches": [], "batch_index": 0, "current_batch": [],
        "marks": [], "critic_result": {}, "decision": "",
        "regrade_count": 0, "final_marks": [],
    })
    return result["final_marks"]