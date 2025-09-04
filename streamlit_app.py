import streamlit as st

from main import graph
from models import QueryAnalysis

# Set page config
st.set_page_config(
    page_title="Stock-Wise AI Chat",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "👋 Hello! I'm Stock-Wise AI, your inventory management assistant.\n\nI can help you manage your inventory with:\n\n- 📝 **Queries**: Get quick answers about your inventory\n\n- 📊 **Analysis**: Detailed reports and insights\n\n- 🛒 **Sales**: Record sales transactions\n\n- 📦 **Stock**: Manage inventory levels"
        }
    ]
if "config" not in st.session_state:
    st.session_state.config = {"configurable": {"thread_id": "streamlit_session"}}

# App title and description
st.title("📊 Stock-Wise AI Chat")
st.markdown("Your intelligent inventory management assistant")

# Sidebar with information
with st.sidebar:
    st.header("About")
    st.markdown("""
    **Stock-Wise AI** is an intelligent inventory management system that provides:
    
    - 📝 **Quick Queries**: Instant answers about your inventory
    - 📊 **Smart Analysis**: Comprehensive reports and business insights  
    - 🛒 **Sales Tracking**: Record and monitor sales transactions
    - 📦 **Stock Management**: Update and track inventory levels
    - 💡 **AI-Powered**: Natural language processing for easy interaction
    """)
    
    st.header("Examples")
    st.code("What is the most expensive item?")
    st.code("Sold 5 digestive biscuits today")
    st.code("Analyze sales trends this month")
    st.code("Stock 10 tea bags")

# Chat interface
chat_container = st.container()

# Display chat messages
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Enter your inventory query..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Create empty placeholder to prevent message ghosting
    placeholder = st.empty()
    
    # Process the query
    with placeholder.container():
        with st.spinner("Processing your query..."):
            # Handle clarification loop
            max_clarifications = 3  # Prevent infinite loops
            clarification_count = 0
            
            final_result = None
            
            while clarification_count < max_clarifications:
                try:
                    # Invoke the workflow
                    result = graph.invoke(
                        {"messages": [{"role": "user", "content": prompt}]},
                        config=st.session_state.config
                    )
                    
                    analysis: QueryAnalysis = result["analyzed_query"]
                    
                    if analysis.validation_status:
                        # Query is complete, store result for rendering outside spinner
                        final_result = result
                        break
                        
                    else:
                        # Need clarification
                        clarification_count += 1
                        if clarification_count >= max_clarifications:
                            st.error("Too many clarifications needed. Please try rephrasing your query.")
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": "Too many clarifications needed. Please try rephrasing your query.",
                                "type": "error"
                            })
                            break
                        
                        # Show clarification question
                        st.warning(f"🤔 Need clarification: \n\n{analysis.question}")
                        
                        # For now, we'll add a message suggesting the user provide more details
                        # In a real implementation, you might want to use st.text_input for clarification
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"🤔 Need clarification: \n\n{analysis.question}\n\nPlease provide more details in your next message.",
                            "type": "clarification"
                        })
                        break
                        
                except Exception as e:
                    st.error(f"Error processing query: {str(e)}")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"Error processing query: {str(e)}",
                        "type": "error"
                    })
                    break
    
    # Clear the placeholder to remove the spinner
    placeholder.empty()
        
    # Process results outside spinner
    if final_result:
        analysis = final_result["analyzed_query"]
        if analysis.operation_type == "ANALYSIS":
            # Handle analysis results
            if "messages" in final_result:
                latest_message = final_result["messages"][-1]
                response_content = ""
                if hasattr(latest_message, 'content') and latest_message.content:
                    response_content += f"{latest_message.content}\n"
                
                # Add to session state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_content.strip(),
                    "type": "analysis"
                })
            else:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Analysis report not available.",
                    "type": "error"
                })
        else:
            # Handle regular messages (QUERY, SALE, STOCK)
            if "messages" in final_result:
                latest_message = final_result["messages"][-1]
                response_content = ""
                if hasattr(latest_message, 'content') and latest_message.content:
                    response_content += f"{latest_message.content}\n"
                
                # Add to session state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_content.strip(),
                    "type": "query_complete"
                })
            else:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Query completed successfully!",
                    "type": "query_complete"
                })
    
    # Trigger rerun to display new messages
    st.rerun()

# Add a clear chat button in the sidebar
with st.sidebar:
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()