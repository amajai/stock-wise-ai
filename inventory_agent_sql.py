import os
from datetime import datetime

from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from typing import Literal
from langchain_core.messages import AIMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from utils import create_llm, get_today_str, get_currency_config
from models import AgentState, AnalysisResult
from prompts import generate_query_system_prompt, check_query_system_prompt, analysis_prompt

llm = create_llm()
db = SQLDatabase.from_uri("sqlite:///inventory.db")

toolkit = SQLDatabaseToolkit(db=db, llm=llm)
tools = toolkit.get_tools()

get_schema_tool = next(tool for tool in tools if tool.name == "sql_db_schema")
get_schema_node = ToolNode([get_schema_tool], name="get_schema")

run_query_tool = next(tool for tool in tools if tool.name == "sql_db_query")
run_query_node = ToolNode([run_query_tool], name="run_query")

def list_tables(state: AgentState):
    tool_call = {
        "name": "sql_db_list_tables",
        "args": {},
        "id": "abc123",
        "type": "tool_call",
    }
    tool_call_message = AIMessage(content="", tool_calls=[tool_call])

    list_tables_tool = next(tool for tool in tools if tool.name == "sql_db_list_tables")
    tool_message = list_tables_tool.invoke(tool_call)
    response = AIMessage(f"Available tables: {tool_message.content}")


    return {"messages": [tool_call_message, tool_message, response]}

def call_get_schema(state: AgentState):
    llm_with_tools = llm.bind_tools([get_schema_tool], tool_choice="any")
    response = llm_with_tools.invoke(state["messages"])

    return {"messages": [response]}

def generate_query(state: AgentState):
    # Get operation type from analyzed query
    analyzed_query = state.get("analyzed_query")
    operation_type = analyzed_query.operation_type if analyzed_query else "QUERY"
    
    currency_config = get_currency_config()
    
    system_message = {
        "role": "system",
        "content": generate_query_system_prompt.format(
            dialect=db.dialect,
            top_k=5,
            operation_type=operation_type,
            date=get_today_str(),
            currency=currency_config["name"],
            currency_example=currency_config["example"]
        ),
    }

    llm_with_tools = llm.bind_tools([run_query_tool])
    response = llm_with_tools.invoke([system_message] + state["messages"])
    
    # For ANALYSIS operations, process the result immediately
    if operation_type == "ANALYSIS" and not response.tool_calls:
        # Get the detailed analysis from response
        detailed_report = response.content
        
        structured_llm = llm.with_structured_output(AnalysisResult)
        formatted_prompt = analysis_prompt.format(detailed_report=detailed_report)
        
        analysis_result = structured_llm.invoke(formatted_prompt)
        
        return {
            "messages": [AIMessage(content=analysis_result.detailed_report)],
            "final_report": analysis_result.detailed_report
        }
    
    return {"messages": [response]}


def check_query(state: AgentState):
    system_message = {
        "role": "system",
        "content": check_query_system_prompt.format(dialect=db.dialect),
    }

    tool_call = state["messages"][-1].tool_calls[0]
    user_message = {"role": "user", "content": tool_call["args"]["query"]}
    llm_with_tools = llm.bind_tools([run_query_tool], tool_choice="any")
    response = llm_with_tools.invoke([system_message, user_message])
    response.id = state["messages"][-1].id

    return {"messages": [response]}

def should_continue(state: AgentState) -> Literal['__end__', "check_query"]:
    messages = state["messages"]
    last_message = messages[-1]
    
    if not last_message.tool_calls:
        return END
    else:
        return "check_query"


workflow = StateGraph(AgentState)
workflow.add_node("list_tables", list_tables)
workflow.add_node("call_get_schema", call_get_schema)
workflow.add_node("get_schema", get_schema_node)
workflow.add_node("generate_query", generate_query)
workflow.add_node("check_query", check_query)
workflow.add_node("run_query", run_query_node)

workflow.set_entry_point('list_tables')
workflow.add_edge("list_tables", "call_get_schema")
workflow.add_edge("call_get_schema", "get_schema")
workflow.add_edge("get_schema", "generate_query")
workflow.add_conditional_edges(
    "generate_query",
    should_continue,
    {"check_query": "check_query", "__end__": END}
)
workflow.add_edge("check_query", "run_query")
workflow.add_edge("run_query", "generate_query")

sql_agent = workflow.compile()

# pprint(sql_agent.invoke({
#     'messages': [HumanMessage('Provide a detail analysis on the best product to sell in the future')],
#     'analyzed_query': {'operation_type': 'ANALYSIS'}}))