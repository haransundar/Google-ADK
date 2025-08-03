# my_agents/agent_invoke_utils.py
"""
Utility for invoking the ADK root_agent in a way compatible with FastAPI sync endpoints.
Handles session, runner, and required ADK services for a stateless API call.
"""
import asyncio
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.auth.credential_service.in_memory_credential_service import InMemoryCredentialService
from google.genai import types
import logging
import warnings

# Suppress the google_genai.types warning about non-text parts
logging.getLogger("google_genai.types").setLevel(logging.ERROR)

# Suppress all UserWarning warnings globally (including EXPERIMENTAL warnings)
warnings.filterwarnings("ignore", category=UserWarning)

from google.adk.agents.run_config import RunConfig
import uuid

# You may want to persist these in production, but for demo/testing, in-memory is fine.
session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()
memory_service = InMemoryMemoryService()
credential_service = InMemoryCredentialService()

async def invoke_root_agent(root_agent, query: str, user_id: str = None, session_id: str = None):
    """
    Invokes the root agent and streams results. All errors are streamed using error_stream for consistency.
    Returns a dict with result and trace if successful, or a StreamingResponse with a JSON error if not.
    """
    import logging
    from starlette.responses import StreamingResponse
    try:
        user_id = user_id or f"user-{uuid.uuid4()}"
        session_id = session_id or f"session-{uuid.uuid4()}"
        runner = Runner(
            app_name="compliance_investigation",
            agent=root_agent,
            artifact_service=artifact_service,
            session_service=session_service,
            memory_service=memory_service,
            credential_service=credential_service,
        )
        session = await session_service.create_session(app_name="compliance_investigation", user_id=user_id)
        content = types.Content(role="user", parts=[types.Part.from_text(text=query)])
        event_trace = []
        logging.info("[invoke_root_agent] Starting agent invocation...")
        event_count = 0
        agent_gen = runner.run_async(user_id=user_id, session_id=session.id, new_message=content, run_config=RunConfig())
        async def defensive_stream():
            nonlocal event_count
            yielded = False
            try:
                async for event in agent_gen:
                    logging.info(f"[invoke_root_agent] Got event from agent: {event}")
                    event_count += 1
                    yielded = True
                    if event.content and event.content.parts:
                        parts = []
                        text_parts_only = []
                        for part in event.content.parts:
                            try:
                                if hasattr(part, 'to_dict') and callable(part.to_dict):
                                    part_dict = part.to_dict()
                                else:
                                    part_dict = {'text': getattr(part, 'text', None)}
                            except Exception as ex:
                                logging.error(f"Error processing part in invoke_root_agent: {ex}")
                                continue
                            parts.append(part_dict)
                            if part_dict.get('text') is not None:
                                text_parts_only.append(part_dict['text'])
                        event_trace.append({
                            "type": getattr(event, 'type', None),
                            "content": parts,
                            "text_parts_only": text_parts_only,
                            "raw": str(event.content.parts)
                        })
                    # Yield a chunk for the client (simulate streaming)
                    import json
                    # Filter: Only yield if at least one text part is non-empty
                    if any(text_parts_only) and any(t for t in text_parts_only if t is not None and str(t).strip() != ""):
                        # Remove newlines, carriage returns, and tabs from all text parts
                        cleaned_text_parts = [str(t).replace('\n', ' ').replace('\r', ' ').replace('\t', ' ') if t is not None else '' for t in text_parts_only]
                        cleaned_parts = []
                        for part in parts:
                            part_copy = dict(part)
                            if 'text' in part_copy and part_copy['text'] is not None:
                                part_copy['text'] = str(part_copy['text']).replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                            cleaned_parts.append(part_copy)
                        # Only stream the first non-empty cleaned text part as a plain passage
                        passage = next((t for t in cleaned_text_parts if t and str(t).strip() != ""), "")
                        if passage:
                            import re
                            # Remove all non-word and non-space characters
                            cleaned_passage = re.sub(r'[^\w\s]', '', passage)
                            # Yield only the cleaned passage as a raw utf-8 string (no JSON, no braces, no quotes)
                            yield cleaned_passage.encode('utf-8')
                    else:
                        # Skip empty/null events
                        continue
            except Exception as ex:
                logging.error(f"[defensive_stream] Exception in agent stream: {ex}")
                import json
                error = {"error": f"Agent error: {str(ex)}"}
                yield json.dumps(error, ensure_ascii=False).encode('utf-8')
            if not yielded:
                logging.error("[defensive_stream] Agent yielded no events, sending fallback error chunk.")
                import json
                error = {"error": "No response from agent (no events yielded)."}
                yield json.dumps(error, ensure_ascii=False).encode('utf-8')
        return StreamingResponse(defensive_stream(), media_type="application/json")
    except Exception as ex:
        logging.error(f"invoke_root_agent failed: {ex}")
        return StreamingResponse(error_stream(f'Agent error: {str(ex)}'), media_type="application/json")

def invoke_root_agent_sync(root_agent, query: str, user_id: str = None, session_id: str = None):
    return asyncio.run(invoke_root_agent(root_agent, query, user_id, session_id))

# ---
# Error streaming conventions: Use error_stream(msg, **context) to yield a JSON error. All StreamingResponses for errors should use this function for consistency and context.
# ---
from typing import Optional
async def error_stream(message: str, **context):
    import json
    error = {"error": message}
    if context:
        error.update(context)
    yield json.dumps(error, ensure_ascii=False).encode('utf-8')
