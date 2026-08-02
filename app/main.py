from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import shutil
import os

from ocr import ReceiptOCR
from line_grouper import group_into_lines, lines_to_text
from receipt_parser import (
    parse_receipt_line,
    is_valid_receipt_item
)
from matcher import ProductMatcher
from pantry import Pantry
from expiry import ExpiryCalculator
from recipe_matcher import RecipeMatcher
from gemini_service import GeminiService
from shopping import ShoppingList

app = FastAPI(title="Smart Pantry OCR API")

# ----------------------------
# Services
# ----------------------------

ocr = ReceiptOCR()
matcher = ProductMatcher("database/products.json")
recipe_matcher = RecipeMatcher("database/recipes.json")
pantry = Pantry()
expiry = ExpiryCalculator()
gemini = GeminiService()
shopping = ShoppingList()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ----------------------------
# Request Models
# ----------------------------

class ConsumeRequest(BaseModel):
    id: int
    quantity: int = 1

class UpdateQuantityRequest(BaseModel):

    quantity: int

class RecipeRequest(BaseModel):
    recipe: str

class ShoppingItemRequest(BaseModel):
    name: str
    quantity: int = 1

class GenerateShoppingRequest(BaseModel):
    recipe: str

# ----------------------------
# Home
# ----------------------------

@app.get("/")
def home():
    return {
        "message": "Smart Pantry OCR API is running"
    }


# ----------------------------
# Pantry
# ----------------------------

@app.get("/pantry")
def get_pantry():

    pantry.cleanup_expired_products()

    products = pantry.get_products()

    for product in products:

        info = expiry.get_status(product["expiry_date"])

        product["status"] = info["status"]
        product["days_left"] = info["days_left"]

    return products

# ----------------------------
# Delete Expired Products
# ----------------------------

@app.delete("/pantry/expired")
def delete_expired_products():

    result = pantry.delete_expired_products()

    return {

        "success": True,

        "deleted_count": result["deleted_count"],

        "deleted_products": result["deleted_products"]

    }

# ----------------------------
# Delete Pantry Product
# ----------------------------

@app.delete("/pantry/{product_id}")
def delete_pantry_product(product_id: int):

    success = pantry.delete_product(product_id)

    return {

        "success": success,

        "message": (
            "Product deleted successfully."
            if success
            else "Product not found."
        )

    }



# ----------------------------
# Receipt OCR
# ----------------------------

@app.post("/scan-receipt")
async def scan_receipt(file: UploadFile = File(...)):

    pantry.cleanup_expired_products()

    file_path = os.path.join(
        UPLOAD_FOLDER,
        file.filename
    )

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # OCR
    results = ocr.extract_text(file_path)

    print("\n========== OCR ==========")
    print(results)

    lines = group_into_lines(results)

    line_texts = lines_to_text(lines)

    print("\n========== LINES ==========")

    for line in line_texts:
        print(line)

    # Parse receipt
    parsed_items = []

    for line in line_texts:

        item = parse_receipt_line(line["text"])

        if is_valid_receipt_item(item):
            parsed_items.append(item)

    print("\n========== PARSED ==========")

    for item in parsed_items:
        print(item)

    matched_products = []

    for item in parsed_items:

        if not item["name"]:
            continue

        match = matcher.match(item["name"])

        if not match:
            continue

        product = match["product"]

        pantry_product = {

            "id": product["id"],

            "name": product["name"],

            "display_name": item["name"],

            "brand": product["brand"],

            "category": product["category"],

            "price": item["price"],

            "size": item["size"],

            "quantity": item["quantity"],

            "expiry_date": expiry.estimate_expiry(
                product["name"]
            )

        }

        pantry.add_product(pantry_product)

        matched_products.append({

            **pantry_product,

            "match_score": match["score"]

        })

    # Remove duplicates

    unique_products = []
    seen = set()

    for product in matched_products:

        if product["id"] not in seen:

            unique_products.append(product)

            seen.add(product["id"])

    return {

        "filename": file.filename,

        "products": unique_products

    }


# ----------------------------
# Consume Product
# ----------------------------

@app.post("/consume")
def consume(request: ConsumeRequest):

    success = pantry.consume_product(
        request.id,
        request.quantity
    )

    return {

        "success": success,

        "message": (
            "Product consumed successfully"
            if success
            else "Product not found"
        )

    }

# ----------------------------
# Update Product Quantity
# ----------------------------

@app.patch("/pantry/{product_id}/quantity")
def update_product_quantity(
    product_id: int,
    request: UpdateQuantityRequest
):

    success = pantry.update_quantity(
        product_id,
        request.quantity
    )

    return {

        "success": success,

        "message": (
            "Quantity updated successfully."
            if success
            else "Product not found."
        )

    }

# ----------------------------
# Expiry Notifications
# ----------------------------

@app.get("/expiry-notifications")
def expiry_notifications():

    pantry.cleanup_expired_products()

    notifications = []

    for product in pantry.get_products():

        info = expiry.get_status(
            product["expiry_date"]
        )

        if info["status"] != "Fresh":

            notifications.append({

                "id": product["id"],

                "name": product["name"],

                "expiry_date": product["expiry_date"],

                "status": info["status"],

                "days_left": info["days_left"]

            })

    return notifications


# ----------------------------
# Low Stock Notifications
# ----------------------------

@app.get("/low-stock")
def low_stock_notifications():

    pantry.cleanup_expired_products()

    return pantry.get_low_stock_products()

# ----------------------------
# Recipe Recommendation
# ----------------------------

@app.get("/recipes")
def get_recipes():

    pantry.cleanup_expired_products()
    pantry_items = pantry.get_products()

    recipes = recipe_matcher.recommend(
        pantry_items
    )

    return recipes

# ======= Shopping List ========== #

# GET Shopping List
@app.get("/shopping-list")
def get_shopping_list():

    return shopping.get_items()

# Add Manual Item
@app.post("/shopping-list/add")
def add_shopping_item(request: ShoppingItemRequest):

    item = shopping.add_item(
        name=request.name,
        quantity=request.quantity,
        source="manual"
    )

    return item

# Check / Uncheck Item.  Patch
@app.patch("/shopping-list/check/{item_id}")
def check_item(item_id: int):

    success = shopping.check_item(item_id)

    return {

        "success": success,

        "message": (
            "Shopping item updated"
            if success
            else "Item not found"
        )

    }

# Clear Shopping List
@app.delete("/shopping-list/clear")
def clear_shopping_list():

    shopping.clear()

    return {

        "success": True,

        "message": "Shopping list cleared"

    }

# Delete Item
@app.delete("/shopping-list/items/{item_id}")
def remove_item(item_id: int):

    success = shopping.remove_item(item_id)

    return {

        "success": success,

        "message": (
            "Item removed"
            if success
            else "Item not found"
        )

    }

@app.post("/shopping-list/generate")
def generate_shopping_list(request: GenerateShoppingRequest):

    pantry.cleanup_expired_products()
    pantry_items = pantry.get_products()

    recipes = recipe_matcher.recommend(
        pantry_items
    )

    selected_recipe = None

    for recipe in recipes:

        if recipe["name"].lower() == request.recipe.lower():

            selected_recipe = recipe
            break

    if selected_recipe is None:

        return {

            "success": False,

            "message": "Recipe not found."

        }

    shopping.generate_from_recipe(selected_recipe)

    return {

        "success": True,

        "recipe": selected_recipe["name"],

        "shopping_list": shopping.get_items()

    }
# ----------------------------
# Gemini AI
# ----------------------------

@app.post("/cook-with-ai")
def cook_with_ai(request: RecipeRequest):

    pantry.cleanup_expired_products()
    pantry_items = pantry.get_products()

    recipes = recipe_matcher.recommend(
        pantry_items
    )

    selected = None

    for recipe in recipes:

        if recipe["name"].lower() == request.recipe.lower():

            selected = recipe
            break

    if selected is None:

        return {

            "success": False,

            "message": "Recipe not found."

        }

    answer = gemini.generate_recipe(

        recipe_name=selected["name"],

        available=selected["matched_ingredients"],

        missing=selected["missing_ingredients"]

    )

    return {

        "success": True,

        "recipe": selected["name"],

        "category": selected["category"],

        "cook_time": selected["cook_time"],

        "match": selected["match"],

        "available": selected["matched_ingredients"],

        "missing": selected["missing_ingredients"],

        "ai_response": answer

    }