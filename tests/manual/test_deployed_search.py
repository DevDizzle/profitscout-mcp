import asyncio

from mcp import ClientSession
from mcp.client.sse import sse_client

# Configuration
# URL of your deployed Cloud Run service
SERVER_URL = "https://profitscout-mcp-469352939749.us-central1.run.app/sse"


async def run_test():
    print(f"Connecting to MCP Server at: {SERVER_URL}")

    try:
        async with sse_client(SERVER_URL) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                print("\n--- Listing Tools ---")
                tools = await session.list_tools()
                search_tool = None
                for tool in tools.tools:
                    print(f"- {tool.name}: {tool.description}")
                    if tool.name == "web_search":
                        search_tool = tool

                if not search_tool:
                    print("\n[ERROR] 'web_search' tool not found!")
                    return

                print("\n--- Executing Web Search: 'current price of NVDA stock' ---")
                # Call the web_search tool
                result = await session.call_tool(
                    "web_search", arguments={"query": "current price of NVDA stock"}
                )

                # Print the result text
                if result.content:
                    print("\nResult:")
                    for content in result.content:
                        print(content.text)
                else:
                    print("No content returned.")

    except Exception as e:
        print(f"\n[ERROR] Failed to connect or execute: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_test())
