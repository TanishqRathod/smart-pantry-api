import json
from rapidfuzz import fuzz


class ProductMatcher:

    def __init__(self, database_path):

        with open(database_path, "r") as f:
            self.products = json.load(f)

    def match(self, text):

        text = text.lower().strip()

        best_product = None
        best_score = 0

        for product in self.products:

            # Compare with product name
            score = fuzz.token_set_ratio(
                text,
                product["name"].lower()
            )

            # Compare with every keyword
            for keyword in product["keywords"]:

                keyword_score = fuzz.token_set_ratio(
                    text,
                    keyword.lower()
                )

                score = max(score, keyword_score)

            if score > best_score:

                best_score = score
                best_product = product

        # Minimum similarity required
        if best_score >= 70:

            return {
                "product": best_product,
                "score": best_score
            }

        return None