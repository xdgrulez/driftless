from driftless_retriever import DriftlessRetriever

retriever = DriftlessRetriever(customer_id="c101")
nodes = retriever.retrieve("Lieferstatus der Bestellung")
print(nodes)
