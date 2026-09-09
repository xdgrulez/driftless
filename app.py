from typing import Optional, TypedDict
import time

import lancedb
from lancedb.embeddings import get_registry
from lancedb.pydantic import LanceModel, Vector
from mcp.server.mcpserver import MCPServer
from kafi.streams.streams import Streams
from kafi.kafka.cluster.cluster import Cluster

#

from functools import cached_property

from lancedb.embeddings import TextEmbeddingFunction, register

table_str = "customer-context"
embedding_str = "snowflake/snowflake-arctic-embed-xs"

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

embeddingFunction = get_registry().get("fastembed").create(name=embedding_str)

class CustomerContext(LanceModel):
    id: str
    customer_id: str
    text: str = embeddingFunction.SourceField()
    vector: Vector(embeddingFunction.ndims()) = embeddingFunction.VectorField() # type: ignore[reportInvalidTypeForm]

class CustomerContextResult(TypedDict):
    order_id: str
    text: str
    score: float

dbConnection = lancedb.connect("./lancedb_data")
table = dbConnection.create_table(table_str, schema=CustomerContext, mode="overwrite")

def lancedb_upsert_sink(m_w_tuple_list):
    add_order_id_str_r_dict = {}
    delete_order_id_str_set = set()
    for m, w in m_w_tuple_list:
        v = m["value"]
        order_id_str = str(v["id"])
        customer_id_str = v["customer"]["id"]
        #
        if w == 1:
            text_str = f"""
            Order #{v["id"]} for customer {v["customer"]["id"]} (product {v["product"]["id"]}) is in status {v["status"]} at timestamp {v["ts"]}. Customer name: {v["customer"]["first_name"]} {v["customer"]["last_name"]}, address: {v["customer"]["street_address"]}, {v["customer"]["state"]}, {v["customer"]["zip_code"]}. Product name: {v["product"]["name"]}, brand: {v["product"]["brand"]}, sale price: ${v["product"]["sale_price"]}
            """
            
            r = {
                "id": order_id_str,
                "customer_id": customer_id_str,
                "text": text_str,
                "vector": embeddingFunction.generate_embeddings([text_str])[0]
            }
    
            add_order_id_str_r_dict[order_id_str] = r
        elif w == -1:
            delete_order_id_str_set.add(order_id_str)

    order_id_str_list = list(delete_order_id_str_set)
    if order_id_str_list:
        ids_sql_str = ", ".join(f"'{i}'" for i in order_id_str_list)
        # print()
        # print(f"Deleting: {order_id_str_list}")
        table.delete(f"id IN ({ids_sql_str})")

    r_list = list(add_order_id_str_r_dict.values())
    # print()
    # print(f"Merge inserting: {d_list}")
    if r_list:
        a = time.time()
        print(f"Merge inserting {len(r_list)} rows...")
        table.merge_insert("id") \
            .when_matched_update_all() \
            .when_not_matched_insert_all() \
            .execute(r_list)
        b = time.time()
        print(f"...done ({(b - a)}s, {(b - a)/len(r_list)} per row).")

    print([r["customer_id"] for r in r_list])

c = Cluster({"kafka": {"bootstrap.servers": "localhost:9092"}, "kafi": {"consume_batch_size": 100}})

orders_tn = (
    Streams.source(c, "orders").to_zSet(Streams.from_debezium)
    .map(lambda r: {
        "id": r["value"]["id"],
        "product_id": r["value"]["product_id"],
        "customer_id": r["value"]["customer_id"],
        "status": r["value"]["status"],
        "ts": r["value"]["ts"]
    })
    .distinct()
)

customers_tn = (
    Streams.source(c, "customers").to_zSet(Streams.from_debezium)
    .map(lambda r: {
        "id": r["value"]["id"],
        "first_name": r["value"]["first_name"],
        "last_name": r["value"]["last_name"],
        "street_address": r["value"]["street_address"],
        "state": r["value"]["state"],
        "zip_code": r["value"]["zip_code"]
        })
    .distinct()
)

products_tn = (
    Streams.source(c, "products").to_zSet(Streams.from_debezium)
    .map(lambda r: {
        "id": r["value"]["id"],
        "brand": r["value"]["brand"],
        "name": r["value"]["name"],
        "sale_price": r["value"]["sale_price"]
        })
    .distinct()
)

sink_tn = (
    orders_tn
    .join(
        customers_tn,
        lambda l_r: l_r["customer_id"],
        lambda r_r: r_r["id"],
        lambda l_r, r_r: {**l_r, "customer": r_r}
    )
    .join(
        products_tn,
        lambda l_r: l_r["product_id"],
        lambda r_r: r_r["id"],
        lambda l_r, r_r: {"value": {**l_r,
                                    "product": r_r}}
    )
    .sink_fun(lancedb_upsert_sink, "sink")
)

tn = Streams.build(sink_tn)
tn.from_zSet(Streams._to_records)
stop_streams = Streams.start_streams(tn)

mcp = MCPServer("Driftless Agentic Memory Demo")

@mcp.tool()
def search_customer_context(query: str, customer_id: Optional[str] = None, limit: int = 3) -> list[CustomerContextResult]:
    table1 = dbConnection.open_table(table_str)
    #
    query_vector = embeddingFunction.generate_embeddings([query])[0]
    #
    if customer_id:
            results = table1.search(query_vector) \
                        .where(f"customer_id = '{customer_id}'") \
                        .limit(limit) \
                        .to_list()
    else:
        results = table1.search(query_vector) \
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
