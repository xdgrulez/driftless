import time

from kafi.kafka.cluster.cluster import Cluster
from generators import CustomerGenerator, OrderGenerator

#

customer_generator = CustomerGenerator()
order_generator = OrderGenerator()

c = Cluster({"kafka": {"bootstrap.servers": "localhost:9092"}})

customer_str = "customers"
order_str = "orders"

c.retouch(customer_str)
c.retouch(order_str)

customer_producer = c.producer(customer_str)
order_producer = c.producer(order_str)

customer_m_list = customer_generator.generate(10)
for m in customer_m_list:
    print(f"Producing customer: {m}")
customer_producer.produce_list(customer_m_list)

for _ in range(100):
    order_m_list = order_generator.generate()
    for m in order_m_list:
        print(f"Producing order: {m}")
    order_producer.produce_list(order_m_list)
    #
    time.sleep(0.5)

customer_producer.close()
order_producer.close()
