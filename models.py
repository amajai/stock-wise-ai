from langgraph.graph import MessagesState
from pydantic import BaseModel, Field

class QueryAnalysis(BaseModel):
    operation_type: str = Field(
        description="Type of operation: SALE, QUERY, ANALYSIS or STOCK"
    )
    question: str = Field(
        description="A question to ask the user to clarify the query. If no question then return ''(empty string) "
    )
    enhanced_query: str = Field(
        description="Cleaned up natural language version of the query"
    )
    validation_status: bool  = Field(
        description="Whether the user needs provide more information based on missing fields"
    )

class AnalysisResult(BaseModel):
    short_summary: str = Field(
        description="Concise 2-3 line summary of key insights and findings"
    )
    detailed_report: str = Field(
        description="Comprehensive analysis report with findings, trends, and recommendations"
    )

class AgentState(MessagesState):
    analyzed_query: QueryAnalysis
    final_report: str

class ClarifyWithUser(BaseModel):
    need_clarification: bool = Field(
        description="Whether the user needs to be asked a clarifying question.",
    )
    question: str = Field(
        description="A question to ask the user to clarify the report scope",
    )
    verification: str = Field(
        description="Verify message that we will start research after the user has provided the necessary information.",
    )
