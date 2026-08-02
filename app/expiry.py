import json
from datetime import date, datetime, timedelta


class ExpiryCalculator:

    def __init__(self):

        with open("database/expiry_rules.json", "r") as f:
            self.rules = json.load(f)

    def estimate_expiry(self, product_name):

        days = self.rules.get(product_name)

        if days is None:
            return None

        expiry = date.today() + timedelta(days=days)

        return str(expiry)

    def get_status(self, expiry_date):

        if expiry_date is None:
            return {
                "status": "Unknown",
                "days_left": None
            }

        expiry = datetime.strptime(
            expiry_date,
            "%Y-%m-%d"
        ).date()

        today = date.today()

        days_left = (expiry - today).days

        if days_left < 0:

            status = "Expired"

        elif days_left <= 3:

            status = "Expiring Soon"

        else:

            status = "Fresh"

        return {
            "status": status,
            "days_left": days_left
        }