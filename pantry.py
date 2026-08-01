import json
import os
from datetime import date, datetime

LOW_STOCK_THRESHOLD = 2

class Pantry:

    def __init__(self, pantry_file="database/pantry.json"):

        self.pantry_file = pantry_file

        if not os.path.exists(self.pantry_file):

            with open(self.pantry_file, "w") as f:
                json.dump([], f, indent=4)

    # -------------------------
    # Internal Helpers
    # -------------------------

    def load(self):

        with open(self.pantry_file, "r") as f:
            return json.load(f)

    def save(self, pantry):

        with open(self.pantry_file, "w") as f:
            json.dump(
                pantry,
                f,
                indent=4
            )

    # -------------------------
    # Public Helpers
    # -------------------------

    def get_products(self):
        return self.load()

    def save_products(self, products):
        self.save(products)

    # -------------------------
    # Add Product
    # -------------------------

    def add_product(self, product):

        pantry = self.load()

        for item in pantry:

            same_product = (
                item["id"] == product["id"]
            )

            same_size = (
                item.get("size") ==
                product.get("size")
            )

            if same_product and same_size:

                item["quantity"] += product.get(
                    "quantity",
                    1
                )

                item["purchase_date"] = str(
                    date.today()
                )

                self.save(pantry)

                return

        pantry.append({

            "id": product["id"],

            "name": product["name"],

            "display_name": product.get(
                "display_name"
            ),

            "brand": product["brand"],

            "category": product["category"],

            "price": product.get("price"),

            "size": product.get("size"),

            "quantity": product.get(
                "quantity",
                1
            ),

            "purchase_date": str(
                date.today()
            ),

            "expiry_date": product.get(
                "expiry_date"
            )

        })

        self.save(pantry)

    # -------------------------
    # Consume Product
    # -------------------------

    def consume_product(
        self,
        product_id,
        quantity=1
    ):

        pantry = self.load()

        for item in pantry:

            if item["id"] == product_id:

                item["quantity"] -= quantity

                if item["quantity"] <= 0:

                    pantry.remove(item)

                self.save(pantry)

                return True

        return False

    # -------------------------
    # Delete Single Product
    # -------------------------

    def delete_product(self, product_id):

        pantry = self.load()

        new_pantry = [

            item
            for item in pantry
            if item["id"] != product_id

        ]

        if len(new_pantry) == len(pantry):

            return False

        self.save(new_pantry)

        return True

    # -------------------------
    # Delete Expired Products
    # -------------------------

    def delete_expired_products(self):

        pantry = self.load()

        today = date.today()

        remaining_products = []

        deleted_products = []

        for product in pantry:

            expiry = product.get(
                "expiry_date"
            )

            if not expiry:

                remaining_products.append(
                    product
                )

                continue

            try:

                expiry_date = datetime.strptime(
                    expiry,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                remaining_products.append(
                    product
                )

                continue

            if expiry_date < today:

                deleted_products.append(
                    product
                )

            else:

                remaining_products.append(
                    product
                )

        self.save(remaining_products)

        return {

            "deleted_count": len(
                deleted_products
            ),

            "deleted_products": deleted_products

        }
    
       # -------------------------
    # Auto Cleanup Expired Products
    # -------------------------

    def cleanup_expired_products(self):
        """
        Automatically removes expired products.
        Called internally before reading pantry data.
        """
        return self.delete_expired_products()

    # -------------------------
    # Low Stock Notifications
    # -------------------------

    def get_low_stock_products(self):

        pantry = self.load()

        notifications = []

        for product in pantry:

            quantity = product.get("quantity", 0)

            if quantity <= LOW_STOCK_THRESHOLD:

                if quantity <= 1:
                    message = f"Only {quantity} left"
                else:
                    message = "Running low"

                notifications.append({

                    "id": product["id"],
                    "name": product["name"],
                    "display_name": product.get("display_name"),
                    "quantity": quantity,
                    "message": message

                })

        return notifications

    # -------------------------
    # Update Product Quantity
    # -------------------------

    def update_quantity(
        self,
        product_id,
        quantity
    ):

        pantry = self.load()

        for item in pantry:

            if item["id"] == product_id:

                if quantity <= 0:

                    pantry.remove(item)

                else:

                    item["quantity"] = quantity

                self.save(pantry)

                return True

        return False