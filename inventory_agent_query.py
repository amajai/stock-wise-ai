from langgraph.graph import StateGraph
from langchain_core.messages import  get_buffer_string

from utils import create_llm, get_all_items, get_today_str
from models import AgentState, QueryAnalysis
from prompts import query_analyzer_prompt

from langgraph.checkpoint.memory import InMemorySaver
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langgraph.prebuilt import ToolNode

llm = create_llm()
db = SQLDatabase.from_uri("sqlite:///inventory.db")

toolkit = SQLDatabaseToolkit(db=db, llm=llm)
tools = toolkit.get_tools()


get_schema_tool = next(tool for tool in tools if tool.name == "sql_db_schema")
get_schema_node = ToolNode([get_schema_tool], name="get_schema")

run_query_tool = next(tool for tool in tools if tool.name == "sql_db_query")
run_query_node = ToolNode([run_query_tool], name="run_query")

def analyze_query(state: AgentState):
    structured_llm = llm.with_structured_output(QueryAnalysis)
    response = structured_llm.invoke(query_analyzer_prompt.format(
        all_items = get_all_items(),
        messages=get_buffer_string(state.get('messages', [])),
        date=get_today_str()
    ))
    return {"analyzed_query": response}

workflow = StateGraph(AgentState)

workflow.add_node("analyze_query", analyze_query)

workflow.set_entry_point('analyze_query')

checkpointer = InMemorySaver()

query_agent = workflow.compile(checkpointer=checkpointer)
