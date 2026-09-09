import threading, time

from kafi.kafka.cluster.cluster import Cluster

from datagen.shoe_orders import ShoeOrderGenerator
from datagen.shoe_customers import ShoeCustomerGenerator
from datagen.shoes import ShoeProductGenerator

#

c = Cluster({"kafka": {"bootstrap.servers": "localhost:9092"}})

order_str = "orders"
customer_str = "customers"
product_str = "products"

c.retouch(order_str)
c.retouch(customer_str)
c.retouch(product_str)

#

def produce_orders():
    order_generator = ShoeOrderGenerator()
    order_producer = c.producer(order_str)
    #
    while True:
        m_list = order_generator.generate(n_int=10)
        #
        order_producer.produce_list(m_list)
        #
        for m in m_list:
            print(f"Produced order: {m}")
        #
        time.sleep(1)

def produce_consumers():
    customer_generator = ShoeCustomerGenerator()
    customer_producer = c.producer(customer_str)
    #
    while True:
        m_list = customer_generator.generate(n_int=10)
        #
        customer_producer.produce_list(m_list)
        #
        for m in m_list:
            print(f"Produced customer: {m}")
        #
        time.sleep(0.1)

def produce_products():
    product_generator = ShoeProductGenerator()
    product_producer = c.producer(product_str)
    #
    while True:
        m_list = product_generator.generate(n_int=10)
        #
        product_producer.produce_list(m_list)
        #
        for m in m_list:
            print(f"Produced product: {m}")
        #
        time.sleep(0.1)

#
    
produce_orders_thread = threading.Thread(target=produce_orders)
produce_consumers_thread = threading.Thread(target=produce_consumers)
produce_products_thread = threading.Thread(target=produce_products)

produce_orders_thread.start()
produce_consumers_thread.start()
produce_products_thread.start()
