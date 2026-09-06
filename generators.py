import copy
import random

#

def m_to_debezium(m, w):
    if w > 0:
        for _ in range(w):
            m1 = copy.deepcopy(m)
            m1["value"] = {
                "before": None,
                "after": m["value"],
                "op": "c"
            }
            return m1
    elif w < 0:
        for _ in range(-w):
            m1 = copy.deepcopy(m)
            m1["value"] = {
                "before": m["value"],
                "after": None,
                "op": "d"
            }
            return m1
    return m

#

class CustomerGenerator:
    def __init__(self, debezium_bool=False, weights_bool=False):
        self.customer_dict_list = [
            {"id": "c101", "name": "Klaus Weber"},
            {"id": "c102", "name": "Sarah Connor"},
            {"id": "c103", "name": "Devin AI"},
            {"id": "c104", "name": "Elena Rostova"},
            {"id": "c105", "name": "Marc Aurel"},
            {"id": "c106", "name": "Lina Chen"},
            {"id": "c107", "name": "Sven Lindqvist"},
            {"id": "c108", "name": "Amira Patel"},
            {"id": "c109", "name": "Beat Meier"},
            {"id": "c110", "name": "Chloe Dubois"},
        ]
        self.current_idx_int = 0
        self.debezium_bool = debezium_bool
        self.weights_bool = weights_bool

    def generate(self, n=1, w=1):
        m_or_m_w_tuple_list = []
        for _ in range(n):
            customer_dict = self.customer_dict_list[self.current_idx_int % len(self.customer_dict_list)]
            self.current_idx_int += 1

            m = {
                "key": customer_dict["id"],
                "value": {
                    "id": customer_dict["id"],
                    "name": customer_dict["name"]
                }
            }

            if self.debezium_bool:
                m = m_to_debezium(m, w)
                m_or_m_w_tuple_list.append(m)
            elif self.weights_bool:
                m_w_tuple = (m, w)
                m_or_m_w_tuple_list.append(m_w_tuple)
            else:
                m_or_m_w_tuple_list.append(m)

        return m_or_m_w_tuple_list

#

class OrderGenerator:
    def __init__(self, debezium_bool=False, weights_bool=False):
        self.state_str_list = [
            "LOOKED_AT (In Shopping Cart)",
            "ORDERED (Payment Pending)",
            "PACKED (Warehouse Zürich)",
            "IN_TRANSIT (Swiss Post)",
            "DELIVERED (Signed at Front Door)",
            "FAILED_DELIVERY (Address Not Found)"
        ]

        self.order_id_int_order_dict_dict = {
            1001: {"customer_id": "c101", "state_idx": 0, "amount": 149.90},
            1002: {"customer_id": "c102", "state_idx": 0, "amount": 89.00},
            1003: {"customer_id": "c103", "state_idx": 0, "amount": 299.50},
            1004: {"customer_id": "c104", "state_idx": 0, "amount": 49.00},
            1005: {"customer_id": "c105", "state_idx": 0, "amount": 1250.00},
            1006: {"customer_id": "c106", "state_idx": 0, "amount": 19.90},
            1007: {"customer_id": "c107", "state_idx": 0, "amount": 540.00},
            1008: {"customer_id": "c108", "state_idx": 0, "amount": 88.50},
            1009: {"customer_id": "c109", "state_idx": 0, "amount": 310.00},
            1010: {"customer_id": "c110", "state_idx": 0, "amount": 670.20},
        }

        self.debezium_bool = debezium_bool
        self.weights_bool = weights_bool

    def generate(self, n=1, w=1):
        m_or_m_w_tuple_list = []
        for _ in range(n):
            order_id_int = random.choice(list(self.order_id_int_order_dict_dict.keys()))
            order_dict = self.order_id_int_order_dict_dict[order_id_int]

            if order_dict["state_idx"] < len(self.state_str_list) - 1:
                if order_dict["state_idx"] == 3 and random.random() < 0.2:
                    order_dict["state_idx"] = 5
                else:
                    order_dict["state_idx"] += 1

            m = {
                "key": str(order_id_int),
                "value": {
                    "order_id": order_id_int,
                    "customer_id": order_dict["customer_id"],
                    "status": self.state_str_list[order_dict["state_idx"]],
                    "amount": order_dict["amount"]
                }
            }

            if self.debezium_bool:
                m = m_to_debezium(m, w)
                m_or_m_w_tuple_list.append(m)
            elif self.weights_bool:
                m_w_tuple = (m, w)
                m_or_m_w_tuple_list.append(m_w_tuple)
            else:
                m_or_m_w_tuple_list.append(m)

        return m_or_m_w_tuple_list
