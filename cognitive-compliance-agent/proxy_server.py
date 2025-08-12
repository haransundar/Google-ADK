# proxy_server.py
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse, JSONResponse

ADK_BACKEND_URL = "http://localhost:8001"
MCP_BACKEND_URL = "http://localhost:8002"

app = FastAPI(title="CORS Reverse Proxy")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Your React frontend's address
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REMOVE global adk_client and mcp_client

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def reverse_proxy(request: Request, path: str):
    import logging
    # Route /api/v1/investigate to MCP, all else to ADK
    if request.url.path == "/api/v1/investigate":
        backend_url_str = MCP_BACKEND_URL
        timeout = httpx.Timeout(600.0)  # 10 minutes for long investigations
    else:
        backend_url_str = ADK_BACKEND_URL
        timeout = httpx.Timeout(60.0)  # 1 minute default timeout

    backend_url = httpx.URL(request.url.path, query=request.url.query.encode("utf-8"))
    req_body = await request.body()
    logging.info(f"[PROXY] Incoming {request.method} {request.url.path} -> {backend_url_str}{request.url.path}")
    logging.info(f"[PROXY] Request headers: {dict(request.headers)}")
    logging.info(f"[PROXY] Request body (first 200 bytes): {req_body[:200]}")
    # Sanitize headers before forwarding
    forbidden_headers = {b'host', b'content-length', b'transfer-encoding', b'connection', b'accept-encoding'}
    # Convert to dict and preserve Content-Type
    safe_headers_dict = {k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v for k, v in request.headers.raw if k.lower() not in forbidden_headers}
    # Force Content-Type for /api/v1/investigate
    if request.url.path == "/api/v1/investigate":
        safe_headers_dict['content-type'] = 'application/json'
    # Log outgoing headers and body
    logging.info(f"[PROXY] Outgoing headers to backend: {safe_headers_dict}")
    logging.info(f"[PROXY] Outgoing body to backend (first 200 bytes): {req_body[:200]}")
    # Always use a fresh AsyncClient per request, and build/send the request using the same client
    try:
        async with httpx.AsyncClient(base_url=backend_url_str, timeout=timeout) as backend_client:
            logging.info(f"[PROXY] Sending request to backend: {backend_url_str}{request.url.path}")
            if request.method == "POST":
                rp_resp = await backend_client.post(
                    str(backend_url),
                    headers=safe_headers_dict,
                    content=req_body,
                    timeout=timeout
                )
            else:
                rp_req = backend_client.build_request(
                    request.method, backend_url, headers=safe_headers_dict, content=req_body
                )
                rp_resp = await backend_client.send(rp_req, stream=True)
            logging.info(f"[PROXY] Backend response status: {rp_resp.status_code}")
            logging.info(f"[PROXY] Backend response headers: {dict(rp_resp.headers)}")
            headers = {k: v for k, v in rp_resp.headers.items() if k.lower() not in ("content-encoding", "content-length")}
            # Log first 200 bytes of backend response for diagnostics
            try:
                preview = await rp_resp.aread() if hasattr(rp_resp, 'aread') else b''
                logging.info(f"[PROXY] Backend response body (first 200 bytes): {preview[:200]}")
            except Exception:
                pass
            try:
                return StreamingResponse(
                    [preview],
                    status_code=rp_resp.status_code,
                    headers=headers
                ) if request.method == "POST" else StreamingResponse(
                    safe_stream_with_min_chunk(rp_resp, backend_url_str, request.method),
                    status_code=rp_resp.status_code,
                    headers=headers
                )
            except Exception as ex:
                logging.error(f"[PROXY] StreamingResponse error: {ex} | backend_url={backend_url_str} method={request.method}")
                return JSONResponse({"error": f"Proxy error: {ex}", "backend_url": backend_url_str, "method": request.method}, status_code=502)
    except Exception as ex:
        logging.error(f"[PROXY] Exception before backend response: {ex} | backend_url={backend_url_str} method={request.method}")
        return JSONResponse({"error": f"Proxy error: {ex}", "backend_url": backend_url_str, "method": request.method}, status_code=502)

# ---
# Streaming proxy logic: All backend streaming uses safe_stream_with_min_chunk(rp_resp, backend_url, request_method), which logs errors, yields a JSON error if the backend fails or yields no data, and always provides context (backend URL, method). Only this function is used and defined globally.
# ---

async def safe_stream_with_min_chunk(rp_resp, backend_url, request_method):
    import logging
    yielded = False
    try:
        async for chunk in rp_resp.aiter_raw():
            logging.info(f"[PROXY] Streaming: yielding backend chunk of size {len(chunk)}")
            yielded = True
            yield chunk
    except Exception as stream_ex:
        import traceback
        err_type = type(stream_ex).__name__
        err_msg = str(stream_ex) or "Unknown backend/proxy stream error"
        tb = traceback.format_exc()
        logging.error(f"[PROXY] Streaming error (generator): [{err_type}] {err_msg} | backend_url={backend_url} method={request_method}\n{tb}")
        error_json = (
            f'\n{{"error": "Proxy streaming error: [{err_type}] {err_msg}", '
            f'"backend_url": "{backend_url}", "method": "{request_method}"}}'
        ).encode('utf-8')
        yield error_json
    if not yielded:
        logging.error(f"[PROXY] Streaming: backend yielded no chunks (empty stream) | backend_url={backend_url} method={request_method}")
        yield (
            f'{{"error": "Proxy backend yielded no data", '
            f'"backend_url": "{backend_url}", "method": "{request_method}"}}'
        ).encode('utf-8')