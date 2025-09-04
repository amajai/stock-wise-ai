from langgraph.graph import StateGraph, END

from models import AgentState, QueryAnalysis

from langgraph.checkpoint.memory import InMemorySaver
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langgraph.prebuilt import ToolNode

from inventory_agent_query import analyze_query
from inventory_agent_sql import sql_agent

def route_to_handler(state: AgentState) -> str:
    """Route based on analysis results"""
    analysis = state.get("analyzed_query")
    if analysis and analysis.validation_status:
        return "sql_agent"
    else:
        return "end"  # End if validation failed

workflow = StateGraph(AgentState)

workflow.add_node("analyze_user_query", analyze_query)
workflow.add_node("sql_agent", sql_agent)

workflow.set_entry_point('analyze_user_query')
workflow.add_conditional_edges(
    "analyze_user_query",
    route_to_handler,
    {"sql_agent": "sql_agent", "end": END}
)
checkpointer = InMemorySaver()

graph = workflow.compile(checkpointer=checkpointer)


def main():
    config = {"configurable": {"thread_id": "1"}}
    
    print("Welcome to Stock-Wise AI! Type 'quit' to exit.")
    
    while True:
        question = input("\nEnter your query: ")
        if question.lower() in ['quit', 'exit', 'q']:
            break
        
        messages = [{"role": "user", "content": question}]
        
        # Handle clarification loop
        while True:
            result = graph.invoke(
                {"messages": messages},
                config=config
            )
            
            analysis: QueryAnalysis = result["analyzed_query"]
            
            if analysis.validation_status:
                print(f"\n✅ Query Complete!")
                print(f"Enhanced Query: {analysis.enhanced_query}")
                print(f"Operation Type: {analysis.operation_type}")
                
                # Handle different output types
                if analysis.operation_type == "ANALYSIS":
                    # Show detailed report
                    if "final_report" in result and result["final_report"]:
                        print(f"\n📊 Analysis Report:")
                        print("="*50)
                        print(result["final_report"])
                        print("="*50)
                    else:
                        print("Analysis report not available.")
                else:
                    # Show regular messages (QUERY, SALE, STOCK)
                    if "messages" in result:
                        latest_messages = result["messages"][-3:]  # Show last few messages
                        for msg in latest_messages:
                            if hasattr(msg, 'content') and msg.content:
                                print(f"\n💬 {msg.content}")
                break  # Exit clarification loop
            else:
                print(f"\n{analysis.question}")
                response = input("Your response: ")
                messages.append({"role": "user", "content": response})
if __name__ == "__main__":
    main()
