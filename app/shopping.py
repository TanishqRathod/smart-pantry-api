import json
import os
from rapidfuzz import fuzz
from matcher import ProductMatcher


class ShoppingList:

    MANUAL_MATCH_THRESHOLD = 88
    RECIPE_MATCH_THRESHOLD = 94

    def __init__(
        self,
        path="database/shopping.json"
    ):

        self.path = path

        self.matcher = ProductMatcher(
            "database/products.json"
        )

        if not os.path.exists(path):

            with open(path, "w") as f:
                json.dump([], f)

    # ----------------------------
    # Internal Helpers
    # ----------------------------

    def _read(self):

        with open(self.path, "r") as f:
            return json.load(f)

    def _write(self, data):

        with open(self.path, "w") as f:
            json.dump(
                data,
                f,
                indent=4
            )

    def find_similar_item(
        self,
        name,
        items,
        threshold
    ):

        best_item = None
        best_score = 0

        for item in items:

            score = fuzz.token_set_ratio(
                name.lower(),
                item["name"].lower()
            )

            if score > best_score:

                best_score = score
                best_item = item

        if best_score >= threshold:
            return best_item

        return None

    # ----------------------------
    # CRUD
    # ----------------------------

    def get_items(self):

        return self._read()

    def clear(self):

        self._write([])

    def add_item(
        self,
        name,
        quantity=1,
        source="manual"
    ):

        items = self._read()

        match = self.matcher.match(name)

        if match:

            product = match["product"]

            canonical_name = product["name"]

            product_id = product["id"]

        else:

            canonical_name = name

            product_id = None

        # Merge using product id
        if product_id is not None:

            for item in items:

                if item.get("product_id") == product_id:

                    item["quantity"] += quantity

                    self._write(items)

                    return item

        else:

            threshold = (
                self.MANUAL_MATCH_THRESHOLD
                if source == "manual"
                else self.RECIPE_MATCH_THRESHOLD
            )

            similar = self.find_similar_item(
                canonical_name,
                items,
                threshold
            )

            if similar:

                similar["quantity"] += quantity

                self._write(items)

                return similar

        new_item = {

            "id": max(
                [i["id"] for i in items],
                default=0
            ) + 1,

            "product_id": product_id,

            "name": canonical_name,

            "display_name": name,

            "quantity": quantity,

            "checked": False,

            "source": source

        }

        items.append(new_item)

        self._write(items)

        return new_item
    

    def check_item(self, item_id):

        items = self._read()

        for item in items:

            if item["id"] == item_id:

                item["checked"] = not item["checked"]

                self._write(items)

                return True

        return False

    def remove_item(self, item_id):

        items = self._read()

        new_items = [

            item
            for item in items
            if item["id"] != item_id

        ]

        self._write(new_items)

        return len(items) != len(new_items)

    # ----------------------------
    # Recipe Integration
    # ----------------------------

    def generate_from_recipe(
        self,
        recipe
    ):

        missing = recipe.get(
            "missing_ingredients",
            []
        )

        for ingredient in missing:

            self.add_item(
                name=ingredient,
                quantity=1,
                source="recipe"
            )

        return self.get_items()

    def delete_product(self, product_id):

        products = self.get_products()

        new_products = [

            product
            for product in products
            if product["id"] != product_id

        ]

        if len(products) == len(new_products):
            return False

        self._save_products(new_products)

        return True