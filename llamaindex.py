from typing import List
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.schema import NodeWithScore, TextNode
from mcp import ClientSession
from mcp.client.sse import sse_client  # oder stdio_client

class DriftlessRetriever(BaseRetriever):
    """LlamaIndex Retriever powered by the Driftless Zero-Drift Pod."""

    def __init__(self, mcp_server_url: str = "http://localhost:8000/sse", top_k: int = 3):
        self.mcp_server_url = mcp_server_url
        self.top_k = top_k
        super().__init__()

    def _retrieve(self, query_str: str) -> List[NodeWithScore]:
        """Holt den frischesten Kontext aus dem Driftless Pod."""
        # Synchroner Wrapper fuer async MCP Client Call
        import asyncio
        return asyncio.run(self._aretrieve(query_str))

    async def _aretrieve(self, query_str: str) -> List[NodeWithScore]:
        """Asynchroner Aufruf des Driftless MCP-Servers."""
        async with sse_client(self.mcp_server_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Call das FastMCP Tool auf deinem Driftless Pod
                result = await session.call_tool(
                    "search_realtime_context", 
                    arguments={"query": query_str, "limit": self.top_k}
                )

                # Parsen der MCP-Antwort in native LlamaIndex Nodes
                nodes = []
                # Result.content enthaelt die frischen Events aus LanceDB
                for idx, text_block in enumerate(result.content):
                    node = TextNode(text=str(text_block))
                    # LlamaIndex erwartet NodeWithScore
                    nodes.append(NodeWithScore(node=node, score=1.0 - (idx * 0.05)))

                return nodes
            
##

from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.retrievers.driftless import DriftlessRetriever

# 1. Driftless als Zero-Drift Context-Engine droppen
retriever = DriftlessRetriever(mcp_server_url="http://localhost:8000/sse")

# 2. In bestehende LlamaIndex Agenten / Query Engines einklinken
query_engine = RetrieverQueryEngine.from_args(retriever=retriever)

# 3. Das LLM antwortet garantiert ohne Data Drift!
response = query_engine.query("Gibt es ein Update zur Bestellung von Kunde 4711?")
print(response)

