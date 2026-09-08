import copy, random

from datagen.constants.product_ids import product_id_str_list
from datagen.constants.customer_ids import customer_id_str_list
from datagen.constants.ips import ip_str_list

# from constants.product_ids import product_id_str_list
# from constants.customer_ids import customer_id_str_list
# from constants.ips import ip_str_list

#

class ShoeClickstreamGenerator:
    def __init__(self):
        self.ts_int = 1788854186242  # Sep 8, 2026
        self.ts_step_int = 1000

    def generate_records(self, n_int=1):
        r_list = []
        #
        while len(r_list) < n_int:
            k_r = None
            #
            click_dict = {
                "product_id": random.choice(product_id_str_list),
                "user_id": random.choice(customer_id_str_list),
                "view_time": random.randint(10, 120),
                "ip": random.choice(ip_str_list),
                "ts": self.ts_int
            }
            #
            v_r = {"before": None, "after": copy.deepcopy(click_dict), "op": "c"}
            #
            self.ts_int += self.ts_step_int
            #
            r_list.append((k_r, v_r))
        #
        return r_list

if __name__ == "__main__":
    generator = ShoeClickstreamGenerator()
    #
    r_list = generator.generate_records(n_int=20)
    #
    for r in r_list:
        print(r)