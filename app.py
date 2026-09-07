from typing import Optional, TypedDict

import lancedb
from lancedb.embeddings import get_registry
from lancedb.index import BTree
from lancedb.pydantic import LanceModel, Vector
from mcp.server.mcpserver import MCPServer
from kafi.streams.streams import Streams
from kafi.kafka.cluster.cluster import Cluster

#

from functools import cached_property

from lancedb.embeddings import TextEmbeddingFunction, register

embedding_str = "BAAI/bge-small-en-v1.5"

@register("fastembed")
class FastEmbedEmbeddings(TextEmbeddingFunction):
    name: str = embedding_str
    max_length: int = 512

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [e.tolist() for e in self._model.embed(list(texts))]

    def ndims(self) -> int:
        return len(self.generate_embeddings(["test"])[0])

    @cached_property
    def _model(self):
        from fastembed import TextEmbedding

        return TextEmbedding(model_name=self.name, max_length=self.max_length)

#

embeddingFunction = get_registry().get("fastembed").create(name="BAAI/bge-small-en-v1.5")

class CustomerContext(LanceModel):
    id: str
    text: str = embeddingFunction.SourceField()
    vector: Vector(embeddingFunction.ndims()) = embeddingFunction.VectorField() # type: ignore[reportInvalidTypeForm]
    customer_id: str

class CustomerContextResult(TypedDict):
    order_id: str
    text: str
    score: float

dbConnection = lancedb.connect("./lancedb_data")
table = dbConnection.create_table("customer_context", schema=CustomerContext, mode="overwrite")
table.create_index("id", config=BTree())

def lancedb_upsert_sink(m_w_tuple_list):
    add_order_id_str_d_dict = {}
    delete_order_id_str_set = set()
    for m, w in m_w_tuple_list:
        v = m["value"]
        order_id_str = f"order_{v['order_id']}"
        #
        if w == 1:
            text_str = f"Order #{v['order_id']} for Customer {v['name']} (ID: {v['customer_id']}) status: {v['status']}, amount: {v['amount']} EUR"
            
            d = {
                "id": order_id_str,
                "text": text_str,
                "customer_id": str(v["customer_id"]),
            }
    
            add_order_id_str_d_dict[order_id_str] = d
        elif w == -1:
            delete_order_id_str_set.add(order_id_str)

    order_id_str_list = list(delete_order_id_str_set)
    print()
    print(f"Deleting: {order_id_str_list}")
    if order_id_str_list:
        ids_sql_str = ", ".join(f"'{i}'" for i in order_id_str_list)
        print()
        print(f"Deleting: {order_id_str_list}")
        table.delete(f"id IN ({ids_sql_str})")

    d_list = list(add_order_id_str_d_dict.values())
    print()
    print(f"Merge inserting: {d_list}")
    table.merge_insert("id") \
        .when_matched_update_all() \
        .when_not_matched_insert_all() \
        .execute(d_list)

    x = table.to_pandas()
    print(x)


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

tn = Streams.build(sink_tn)
tn.from_zSet(Streams._to_records)
stop_streams = Streams.start_streams(tn)

mcp = MCPServer("Driftless Agentic Memory Demo")

@mcp.tool()
def search_customer_context(query: str, customer_id: Optional[str] = None, limit: int = 3) -> list[CustomerContextResult]:
    if customer_id:
        results = table.search(query) \
                    .where(f"customer_id = '{customer_id}'") \
                    .limit(limit) \
                    .to_list()
    else:
        results = table.search(query) \
                    .limit(limit) \
                    .to_list()

    return [
        {
            "order_id": r["id"],
            "text": r["text"],
            "score": round(1.0 - r["_distance"], 4),
        }
        for r in results
    ]

if __name__ == "__main__":
    mcp.run(transport="sse", port=8000)
