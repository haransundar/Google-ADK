# my_agents/agent.py
from google.adk.agents import LlmAgent
from google.adk.agents.base_agent import BaseAgent
# --- BEGIN: Dummy Content/Part fallback for DummyAgent ---
try:
    from google.adk.types import Content, Part
except ImportError:
    class Part:
        def __init__(self, text):
            self.text = text
        @staticmethod
        def from_text(text):
            return Part(text)
    class Content:
        def __init__(self, role, parts):
            self.role = role
            self.parts = parts
# --- END: Dummy Content/Part fallback ---

# We import the tools directly for the orchestrator to use.
from .tools.aml_rag_tool import lookup_aml_regulations
from .tools.internal_data_tool import customer_lookup

# LOG: Make it clear which tool is being used
print("[INFO] Using local/mock customer_lookup tool from internal_data_tool.py (fast, no HTTP calls)")

# NOTE: Do NOT use mcp_customer_tool.py for customer_lookup in development or demo. That version makes HTTP calls and will hang or fail if the backend is not running. Use ONLY in production with a live backend.

# --- DUMMY AGENT FOR ISOLATION TEST ---
class DummyAgent(BaseAgent):
    def __init__(self, name="DummyAgent"):
        super().__init__(name=name)
    async def run_async(self, ctx):
        import logging
        logging.info("[DummyAgent] run_async called")
        user_message = None
        yielded = False
        if hasattr(ctx, 'message') and ctx.message and hasattr(ctx.message, 'parts') and ctx.message.parts:
            user_message = ctx.message.parts[0].text
        else:
            user_message = "[No input]"
        from datetime import datetime, timezone
        class ADKEvent(dict):
            def __init__(self, content, partial):
                super().__init__(content=content, partial=partial)
                self.content = content
                self.partial = partial
                self.actions = None
                self.timestamp = datetime.now(timezone.utc)
        try:
            logging.info(f"[DummyAgent] yielding event with user_message: {user_message}")
            yield ADKEvent(Content(role="assistant", parts=[Part.from_text(f"ECHO: {user_message}")]), False)
            logging.info("[DummyAgent] yield completed successfully")
            yielded = True
        except Exception as ex:
            logging.error(f"[DummyAgent] Exception during yield: {ex}")
        if not yielded:
            # Always yield an error event if nothing was yielded
            logging.error("[DummyAgent] No events yielded, sending fallback error event.")
            error_content = Content(role="assistant", parts=[Part.from_text("[ERROR] Agent failed to yield any response.")])
            yield ADKEvent(error_content, False)

# Temporarily use DummyAgent for debugging
# root_agent = DummyAgent(name="DummyAgent")

# --- ENABLED: REAL ORCHESTRATOR AGENT ---
root_agent = LlmAgent(
    name="Orchestrator_Agent",
    model="gemini-1.5-flash",
    instruction=(
        "You are the lead compliance investigator. Your task is to perform a "
        "Know Your Customer (KYC) and Anti-Money Laundering (AML) check based on user input. "
        "Follow these steps in order:\n"
        "1. Use the `customer_lookup` tool to retrieve the internal data for the specified customer ID.\n"
        "2. Use the `lookup_aml_regulations` tool to find regulations relevant to the user's query.\n"
        "3. After completing both steps, synthesize all the information into a single, "
        "comprehensive investigation summary report.\n"
        "\n--- OUTPUT FORMAT GUIDELINES ---\n"
        "- Begin every report with: '=== Investigation Report ===' and a one-line summary.\n"
        "- Use markdown for section headers (## Customer Information, ## AML Regulatory Context, etc).\n"
        "- End every report with a clear next action for the compliance team, e.g., 'Next step: Escalate to AML team for review.'\n"
        "- If customer data is missing, clearly state this and suggest verifying the customer ID or data source.\n"
        "- If regulations are not found, suggest a more targeted query.\n"
        "- Always provide actionable, concise, and readable output for compliance professionals."
    ),
    # The orchestrator has access to all necessary tools.
    tools=[
        customer_lookup,
        lookup_aml_regulations
    ]
)