from typing import Annotated

import lancedb
from lancedb.embeddings import get_registry
from lancedb.pydantic import LanceModel, Vector
from mcp.server.mcpserver import MCPServer
from kafi.streams.streams import Streams
from kafi.kafka.cluster.cluster import Cluster

import fastembed_lancedb

embeddingFunction = get_registry().get("fastembed").create(name="BAAI/bge-small-en-v1.5")

class CustomerContext(LanceModel):
    id: str
    text: str = embeddingFunction.SourceField()
    vector: Annotated[list[float], Vector(embeddingFunction.ndims())] = embeddingFunction.VectorField()
    customer_id: str

dbConnection = lancedb.connect("./lancedb_data")
table = dbConnection.create_table("customer_context", schema=CustomerContext, mode="overwrite")

def lancedb_upsert_sink(r):
    v = r["value"]
    order_id = f"order_{v['order_id']}"
    text_str = f"Order #{v['order_id']} for Customer {v['name']} (ID: {v['customer_id']}) status: {v['status']}, amount: {v['amount']} EUR"
    
    table.merge_insert("id") \
         .when_matched_update_all() \
         .when_not_matched_insert_all() \
         .execute([{
             "id": order_id,
             "text": text_str,
             "customer_id": str(v["customer_id"])
         }])

c = Cluster({"kafka": {"bootstrap.servers": "localhost:9092"}})

orders_tn = (
    Streams.source(c, "orders")
    .map(lambda r: {
        "order_id": r["value"]["order_id"],
        "customer_id": r["value"]["customer_id"],
        "status": r["value"]["status"],
        "amount": r["value"]["amount"]
    })
    .distinct()
)

customers_tn = (
    Streams.source(c, "customers")
    .map(lambda r: {
        "id": r["value"]["id"],
        "name": r["value"]["name"]})
    .distinct()
)

sink_tn = (
    orders_tn
    .join(
        customers_tn,
        lambda l: l["customer_id"],
        lambda r: r["id"],
        lambda l, r: {"value": {**l, "name": r["name"]}}
    )
    .sink_fun(lancedb_upsert_sink, "sink")
)

topology = Streams.build(sink_tn)
stop_streams = Streams.start_streams(topology)

mcp = MCPServer("Driftless Agentic Memory Demo")

@mcp.tool()
def search_customer_context(customer_id: str, query: str) -> str:
    results = table.search(query) \
                   .where(f"customer_id = '{customer_id}'") \
                   .limit(3) \
                   .to_list()
    
    if not results:
        return f"No context found for customer {customer_id}."
    
    context_output = [f"--- Found context for customer {customer_id} ---"]
    for r in results:
        context_output.append(f"  Order ID: {r['id']}")
        context_output.append(f"  Text: {r['text']}")
        context_output.append(f"  Relevance score: {round(r['_distance'], 3)}")
        context_output.append("")
        
    return "\n".join(context_output)

if __name__ == "__main__":
    mcp.run(transport="sse", port=8000)
