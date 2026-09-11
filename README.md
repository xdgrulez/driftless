# driftless
Driftless - Zero-Drift Agentic Memory in One Pod

1. `app.py` - this is the MCP server - reads from Kafka, joins twice, embeds the output and puts it into LanceDB; and has an MCP endpoint for accessing the DB
2. `producer.py` - this is the producer for example data (customers, products + orders)
3. `client.py` - this is the MCP client to access the DB of the MCP server

So to test it, run `app.py` and `producer.py` in parallel, and then use `client.py` to access the "driftless" data. `py client.py --help` gives you the possible query params (`--query` is for the vector search).
