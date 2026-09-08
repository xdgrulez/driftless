import copy, random

from datagen.constants.products import product_dict_list

# from constants.products import product_dict_list

#

class ShoeProductGenerator:
    def __init__(self):
        self.product_dict_list = []

    def generate_records(self, n_int=1):
        r_list = []
        #
        while len(r_list) < n_int:
            rand_int = random.randrange(10)
            #
            if rand_int <= 6 or self.product_dict_list == []: # insert
                product_dict = random.choice(product_dict_list)
                #
                product_dict = copy.deepcopy(product_dict)
                self.product_dict_list.append(product_dict)
                #
                k_r = product_dict["id"]
                #
                v_r = {"before": None, "after": product_dict, "op": "c"}
                #
                r_list.append((k_r, v_r))
            elif rand_int > 6 and rand_int <= 8: # update
                product_index_int = random.randint(0, len(self.product_dict_list) - 1)
                #
                old_product_dict = self.product_dict_list.pop(product_index_int)
                #
                product_dict = copy.deepcopy(old_product_dict)
                product_dict["sale_price"] = round(product_dict["sale_price"] * random.uniform(0.85, 1.15), 2)
                #
                self.product_dict_list.append(product_dict)
                #
                k_r = product_dict["id"]
                #
                v_r = {"before": old_product_dict, "after": product_dict, "op": "u"}
                #
                r_list.append((k_r, v_r))
            else: # delete
                product_index_int = random.randint(0, len(self.product_dict_list) - 1)
                #
                product_dict = self.product_dict_list.pop(product_index_int)
                k_r = product_dict["id"]
                #
                v_r = {"before": product_dict, "after": None, "op": "d"}
                #
                r_list.append((k_r, v_r))
        #
        return r_list

if __name__ == "__main__":
    generator = ShoeProductGenerator()
    #
    r_list = generator.generate_records(n_int=20)
    #
    for r in r_list:
        print(r)
