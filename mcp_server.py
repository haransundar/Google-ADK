# mcp_server.py
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# This defines the expected input for our API endpoint
class ToolInput(BaseModel):
    customer_id: str

# Create the FastAPI app instance
app = FastAPI(title="Tool Server")

# ASGI middleware to log all incoming requests at the raw level
@app.middleware("http")
async def log_raw_request(request, call_next):
    body = await request.body()
    headers = dict(request.headers)
    import logging
    logging.info(f"[ASGI-RAW] {request.method} {request.url.path} | headers: {headers} | body (first 200 bytes): {body[:200]}")
    # Reconstruct the request so downstream handlers can read the body
    from starlette.requests import Request as StarletteRequest
    request = StarletteRequest(request.scope, receive=lambda: {"type": "http.request", "body": body, "more_body": False})
    response = await call_next(request)
    return response

from fastapi.responses import JSONResponse
from fastapi.requests import Request
import logging

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.exception(f"UNHANDLED EXCEPTION: {exc}")
    # For investigate endpoint, always stream errors
    from starlette.responses import StreamingResponse
    if request.url.path == "/api/v1/investigate":
        async def error_stream():
            import json
            error = {"error": f"Internal server error: {str(exc)}"}
            yield json.dumps(error, ensure_ascii=False).encode('utf-8')
        return StreamingResponse(error_stream(), media_type="application/json")
    return JSONResponse(status_code=500, content={"error": f"Internal server error: {str(exc)}"})

# --- Add CORS Middleware for local dev ---
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev, allow all. For prod, restrict to ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- END CORS ---

# Mock database
MOCK_CUSTOMER_DB = {
    "CUST-007": {
        "name": "John Doe",
        "risk_score": "High",
        "account_open_date": "2022-01-15",
        "recent_activity": "Multiple cash deposits of $9,500 in the last 7 days.",
        "occupation": "Owner, Cash-Intensive Business"
    },
    "CUST-101": {
        "name": "Jane Smith",
        "risk_score": "Low",
        "account_open_date": "2018-05-20",
        "recent_activity": "Regular payroll deposits, occasional bill payments.",
        "occupation": "Software Engineer"
    },
}

# Business logic function
def get_customer_details(customer_id: str) -> dict:
    """The business logic for the tool."""
    print(f"Tool Server received request for customer: {customer_id}")
    return MOCK_CUSTOMER_DB.get(customer_id, {"error": "Customer not found."})


# The HTTP endpoint for the tool
@app.post("/tools/get_customer_details/invoke")
def invoke_tool(tool_input: ToolInput):
    result = get_customer_details(tool_input.customer_id)
    return {"output": result}

# New investigation endpoint for /api/v1/investigate
from my_agents.agent import root_agent

class InvestigationInput(BaseModel):
    query: str

import asyncio
import logging

@app.post("/api/v1/investigate")
async def investigate(request: Request):
    from starlette.responses import StreamingResponse
    import json
    raw_body = await request.body()
    logging.info(f"[INVESTIGATE] Received request at /api/v1/investigate")
    logging.info(f"[INVESTIGATE] Request headers: {dict(request.headers)}")
    logging.info(f"[INVESTIGATE] Request body (first 200 bytes): {raw_body[:200]}")
    try:
        parsed = json.loads(raw_body)
        logging.info(f"[INVESTIGATE] Parsed JSON body: {parsed}")
        query = parsed.get('query', None)
        if not query:
            raise ValueError("Missing 'query' field in JSON body")
    except Exception as ex:
        logging.error(f"[INVESTIGATE] Failed to parse JSON body or missing query: {ex}")
        async def error_stream():
            import json
            msg = {"error": f"Invalid or missing JSON body: {str(ex)}"}
            yield json.dumps(msg, ensure_ascii=False).encode('utf-8')
        return StreamingResponse(error_stream(), media_type="application/json")

    # Call the real agent and stream its output
    from my_agents.agent_invoke_utils import invoke_root_agent
    from my_agents.agent import root_agent
    async def agent_stream():
        # invoke_root_agent returns a StreamingResponse, so we need to await it and yield its body_iterator
        response = await invoke_root_agent(root_agent, query)
        async for chunk in response.body_iterator:
            yield chunk
    return StreamingResponse(agent_stream(), media_type="application/json")

if __name__ == "__main__":
    print("Starting Tool Server at http://localhost:8002")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)