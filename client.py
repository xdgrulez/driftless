import asyncio
import argparse
import os
from typing import Dict, Any
from mcp import ClientSession
from mcp.client.sse import sse_client

async def run_mcp_tool(
    server_url: str, 
    tool_name: str, 
    arguments: Dict[str, Any]
):
    async with sse_client(server_url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                tool_name,
                arguments=arguments
            )
            
            for content in result.content:
                if content.type == "text":
                    print(content.text)

if __name__ == "__main__":
    DEFAULT_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/sse")

    parser = argparse.ArgumentParser(description="Konfigurierbarer MCP Client")
    parser.add_argument("--url", default=DEFAULT_URL, help="MCP SSE Server URL")
    parser.add_argument("--id", default=None, help="Order ID")
    parser.add_argument("--customer-id", default=None, help="Customer ID")
    parser.add_argument("--customer-name", default=None, help="Customer name")
    parser.add_argument("--query", default=None, help="Query")
    
    args = parser.parse_args()

    tool_args = {
        "id": args.id,
        "customer_id": args.customer_id,
        "customer_name": args.customer_name,
        "query": args.query
    }

    asyncio.run(
        run_mcp_tool(
            server_url=args.url, 
            tool_name="search_customer_context", 
            arguments=tool_args
        )
    )
