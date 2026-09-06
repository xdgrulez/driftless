import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

async def run_query():
    async with sse_client("http://localhost:8000/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "search_customer_context",
                arguments={
                    "customer_id": "c101",
                    "query": "Lieferstatus der Bestellung"
                }
            )
            
            for content in result.content:
                if content.type == "text":
                    print(content.text)

if __name__ == "__main__":
    asyncio.run(run_query())
