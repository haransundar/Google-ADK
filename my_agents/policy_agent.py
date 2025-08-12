# my_agents/policy_agent.py
from google.adk.agents import Agent
from .tools.aml_rag_tool import lookup_aml_regulations

# This is a specialized agent for RAG lookups.
policy_interpretation_agent = Agent(
    name="Policy_Interpretation_Agent",
    model="gemini-1.5-flash",
    instruction=(
        "You are an expert paralegal. Given a query about financial regulations, "
        "use the lookup_aml_regulations tool to find the most relevant text. "
        "Return only the retrieved information."
    ),
    tools=[lookup_aml_regulations]
)