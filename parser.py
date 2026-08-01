import re

MIN_CONFIDENCE = 0.50

IGNORE_WORDS = {
    "TOTAL",
    "SUBTOTAL",
    "TAX",
    "DEBIT",
    "ACCOUNT",
    "CHANGE",
    "PAY",
    "PAYMENT",
    "WALMART",
    "SAVE",
    "NETWORK",
    "REF",
    "ITEMS",
    "SOLD",
    "LAYAWAY",
    "MANAGER"
}


def is_number(text: str) -> bool:
    """
    Detect OCR outputs that are only prices/numbers.

    Examples:
        0.99
        0 - 99
        1-15
        25
        $25.97
        ₹50
        Rs.50
    """

    clean = text.upper()

    clean = clean.replace("₹", "")
    clean = clean.replace("$", "")
    clean = clean.replace("£", "")
    clean = clean.replace("€", "")
    clean = clean.replace("RS.", "")
    clean = clean.replace("RS", "")
    clean = clean.replace("INR", "")

    clean = clean.replace(".", "")
    clean = clean.replace(",", "")
    clean = clean.replace("-", "")
    clean = clean.replace(" ", "")

    return clean.isdigit()


def filter_text(ocr_results):

    filtered = []

    for item in ocr_results:

        text = item["text"].strip().upper()
        confidence = item["confidence"]

        if confidence < MIN_CONFIDENCE:
            continue

        if not text:
            continue

        if is_number(text):
            continue

        if re.search(r"\d{2}/\d{2}/\d{2,4}", text):
            continue

        if text in IGNORE_WORDS:
            continue

        filtered.append({
            "bbox": item["bbox"],
            "text": text,
            "confidence": confidence
        })

    return filtered