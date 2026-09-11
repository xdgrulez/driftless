import asyncio
import argparse
import os
from typing import Dict, Any
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

async def run_mcp_tool(
    server_url: str, 
    tool_name: str, 
    arguments: Dict[str, Any]
):
    async with streamable_http_client(server_url) as (read, write, *_):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            callToolResult = await session.call_tool(
                tool_name,
                arguments=arguments
            )
            
            for content in callToolResult.content:
                if content.type == "text":
                    print(content.text)

if __name__ == "__main__":
    server_url_str = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")

    argumentParser = argparse.ArgumentParser(description="Konfigurierbarer MCP Client")
    argumentParser.add_argument("--url", default=server_url_str, help="MCP Streamable HTTP Server URL")
    argumentParser.add_argument("--id", default=None, help="Order ID")
    argumentParser.add_argument("--customer-id", default=None, help="Customer ID")
    argumentParser.add_argument("--customer-name", default=None, help="Customer name")
    argumentParser.add_argument("--query", default=None, help="Query")
    
    args = argumentParser.parse_args()

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
