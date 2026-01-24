# Deployment Fix Summary

## Issue
The MCP server failed to deploy to Cloud Run with `ValueError: Request validation failed`.
This was caused by the `mcp` library's `FastMCP` class automatically enabling strict DNS rebinding protection when the host is set to "localhost" or "127.0.0.1" (the default). This protection blocks requests from Cloud Run's proxy (e.g., `*.run.app`).

## Root Cause Analysis
- `FastMCP` defaults to `host="127.0.0.1"`.
- When `host` is "127.0.0.1", `FastMCP` enables `TransportSecurityMiddleware` with strict `allowed_hosts`.
- Cloud Run requests come with a different Host header, causing `validate_request` to fail with 421 (or ValueError in logs).

## Fix Applied
1. **Updated `src/server.py`**:
   - Initialized `FastMCP` with `host="0.0.0.0"`.
   - This disables the automatic "localhost-only" security policy, allowing the server to accept requests from the Cloud Run proxy.
   - Also explicitly set the `port` in initialization using the `PORT` environment variable.

2. **Updated `src/server.py` `main()`**:
   - Corrected the `mcp.run()` call to use `transport="sse"` (valid for this version) and removed invalid `host`/`port` arguments (now handled in initialization).

## Next Steps
- Redeploy the application to Cloud Run using `./deploy.sh` or your standard deployment pipeline.
- The server should now start correctly and accept requests.
