import copy, random

from datagen.constants.product_ids import product_id_str_list
from datagen.constants.customer_ids import customer_id_str_list

# from constants.product_ids import product_id_str_list
# from constants.customer_ids import customer_id_str_list

#

status_id_int_status_str_dict = {
    0: "LOOKED_AT (in shopping cart)",
    1: "ORDERED (payment pending)",
    2: "ORDER_COMPLETE (payment complete)",
    3: "PACKED (packed in warehouse)",
    4: "IN_TRANSIT (on the way)",
    5: "DELIVERED (delivered to front door)",
    6: "FAILED_DELIVERY (address not found)"}

#

class ShoeOrderGenerator:
    def __init__(self):
        self.order_id_int = 1
        self.order_id_step_int = 1
        #
        self.ts_int = 1788854186242 # Sep 8, 2026
        self.ts_step_int = 10000
        #
        self.order_id_int_order_dict_dict = {}

    def generate_records(self, n_int=1):
        r_list = []
        #
        while len(r_list) < n_int:
            rand_int = random.randrange(10)
            #
            if rand_int <= 4 or self.order_id_int_order_dict_dict == {}: # insert
                order_dict = {
                    "id": self.order_id_int,
                    "product_id": random.choice(product_id_str_list),
                    "customer_id": random.choice(customer_id_str_list),
                    "status_id": 0,
                    "status": status_id_int_status_str_dict[0],
                    "ts": self.ts_int
                }
                #
                self.order_id_int_order_dict_dict[self.order_id_int] = copy.deepcopy(order_dict)
                #
                self.order_id_int += self.order_id_step_int
                self.ts_int += self.ts_step_int
                #
                k_r = str(order_dict["id"])
                #
                v_r = {"before": None, "after": order_dict, "op": "c"}
                #
                r_list.append((k_r, v_r))
            elif rand_int > 4 and rand_int <= 8: # update
                order_id_int = random.choice(list(self.order_id_int_order_dict_dict.keys()))
                #
                old_order_dict = self.order_id_int_order_dict_dict[order_id_int]
                #
                order_dict = copy.deepcopy(old_order_dict)
                #
                if order_dict["status_id"] not in [5, 6]:
                    if order_dict["status_id"] == 4 and random.random() < 0.2:
                        order_dict["status_id"] = 6
                    else:
                        order_dict["status_id"] += 1
                    #
                    order_dict["status"] = status_id_int_status_str_dict[order_dict["status_id"]]
                    #
                    self.ts_int += self.ts_step_int
                    #
                    order_dict["ts"] = self.ts_int
                    #
                    self.order_id_int_order_dict_dict[order_id_int] = order_dict
                    #
                    k_r = str(order_id_int)
                    #
                    v_r = {"before": old_order_dict, "after": order_dict, "op": "u"}
                    #
                    r_list.append((k_r, v_r))
            else: # delete
                order_id_int = random.choice(list(self.order_id_int_order_dict_dict.keys()))
                #
                order_dict = self.order_id_int_order_dict_dict[order_id_int]
                del self.order_id_int_order_dict_dict[order_id_int]
                #
                self.ts_int += self.ts_step_int
                #
                k_r = str(order_dict["id"])
                #
                v_r = {"before": order_dict, "after": None, "op": "d"}
                #
                r_list.append((k_r, v_r))
        #
        return r_list

if __name__ == "__main__":
    generator = ShoeOrderGenerator()
    #
    r_list = generator.generate_records(n_int=20)
    #
    for r in r_list:
        print(r)
