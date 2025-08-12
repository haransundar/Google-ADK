# my_agents/impact_agent.py
from google.adk.agents import Agent
from .tools.mcp_customer_tool import customer_lookup

# This is a specialized agent for internal data lookups via MCP.
impact_assessment_agent = Agent(
    name="Impact_Assessment_Agent",
    model="gemini-1.5-flash",
    instruction=(
        "You are an internal business analyst. Given a customer ID, use the "
        "get_customer_details tool to retrieve all available data for that customer."
    ),
    tools=[customer_lookup]
)