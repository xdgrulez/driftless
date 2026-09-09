from typing import Optional, TypedDict

from mcp.server.mcpserver import MCPServer

from db.db import connect, create_table, get_sink_fun, search, embeddingFunction, table_str
from kafka.kafka import streams

#

dbConnection = connect()
#
table = create_table(dbConnection)
#
sink_fun = get_sink_fun(table)
#
stop_fun = streams(sink_fun, emulated=False)

#

mcp = MCPServer("Driftless Agentic Memory in One Pod")

class CustomerContextResult(TypedDict):
    summary: str
    score: float

@mcp.tool()
def search_customer_context(query: Optional[str] = None, id: Optional[str] = None, customer_id: Optional[str] = None, customer_name: Optional[str] = None, limit: int = 3) -> list[CustomerContextResult]:
    return search(dbConnection, query, id, customer_id, customer_name, limit)

#

if __name__ == "__main__":
    mcp.run(transport="sse", port=8000)
