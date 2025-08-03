import google.generativeai as genai
from google.adk.agents import Agent
from google.adk.tools import google_search

# --- The Fix ---
# Directly configure the API key in the code, bypassing the .env file.
# Replace the placeholder text with your actual API key.
genai.configure(api_key="AIzaSyC6LLaATy1Oi6UPgDvht_sRNadivWmH3NA")
# ---------------

root_agent = Agent(
    name="my_correct_agent",
    model="gemini-1.5-flash",
    instruction="You are a search agent. Immediately use the Google Search tool to answer the user's question. Be concise.",
    tools=[google_search]
)