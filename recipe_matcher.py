import json


class RecipeMatcher:

    def __init__(self, recipe_file="database/recipes.json"):

        with open(recipe_file, "r") as f:
            self.recipes = json.load(f)

    def recommend(self, pantry_products):

        # Pantry product names
        pantry = {
            product["name"].lower()
            for product in pantry_products
        }

        recommendations = []

        for recipe in self.recipes:

            matched = []
            missing = []

            for ingredient in recipe["ingredients"]:

                if ingredient.lower() in pantry:
                    matched.append(ingredient)
                else:
                    missing.append(ingredient)

            score = round(
                len(matched) / len(recipe["ingredients"]) * 100
            )

            recommendations.append({

                "id": recipe["id"],

                "name": recipe["name"],

                "category": recipe["category"],

                "cook_time": recipe["cook_time"],

                "match": score,

                "matched_ingredients": matched,

                "missing_ingredients": missing

            })

        recommendations.sort(
            key=lambda x: x["match"],
            reverse=True
        )

        return recommendations[:5]