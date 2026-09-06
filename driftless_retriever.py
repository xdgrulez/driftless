import json
from typing import List, Optional

from llama_index.core.async_utils import asyncio_run
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.callbacks.base import CallbackManager
from llama_index.core.schema import NodeWithScore, QueryBundle, TextNode
from mcp import ClientSession
from mcp.client.sse import sse_client


class DriftlessRetriever(BaseRetriever):
    """LlamaIndex Retriever powered by den Driftless MCP-Server (search_customer_context)."""

    def __init__(
        self,
        customer_id: str,
        mcp_server_url: str = "http://localhost:8000/sse",
        top_k: int = 3,
        callback_manager: Optional[CallbackManager] = None,
    ) -> None:
        self._customer_id = customer_id
        self._mcp_server_url = mcp_server_url
        self._top_k = top_k
        super().__init__(callback_manager=callback_manager)

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        return asyncio_run(self._aretrieve(query_bundle))

    async def _aretrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        async with sse_client(self._mcp_server_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                result = await session.call_tool(
                    "search_customer_context",
                    arguments={
                        "customer_id": self._customer_id,
                        "query": query_bundle.query_str,
                        "limit": self._top_k,
                    },
                )

                if result.is_error:
                    raise RuntimeError(f"MCP tool error: {result.content}")

                # FastMCP liefert strukturierte Tool-Ergebnisse zusätzlich als
                # JSON-Text-Block; darauf greifen wir zurück, falls
                # `structuredContent` fehlt (z.B. bei älteren Clients).
                matches = result.structured_content
                if matches is None:
                    text_block = next(
                        (c.text for c in result.content if c.type == "text"), "[]"
                    )
                    matches = json.loads(text_block)

                # Manche Server wrappen Listen in {"result": [...]}
                if isinstance(matches, dict):
                    matches = matches.get("result", [])

                return [
                    NodeWithScore(
                        node=TextNode(
                            text=m["text"],
                            id_=m["order_id"],
                            metadata={"customer_id": self._customer_id},
                        ),
                        score=float(m["score"]),
                    )
                    for m in matches
                ]