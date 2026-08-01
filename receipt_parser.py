import re


def normalize_line(line: str):

    line = " ".join(line.split())

    # ------------------------
    # OCR PRICE FIXES
    # ------------------------

    # 0 .99 -> 0.99
    line = re.sub(
        r'(\d)\s+\.(\d{2})',
        r'\1.\2',
        line
    )

    # 0. 99 -> 0.99
    line = re.sub(
        r'(\d)\.\s+(\d{2})',
        r'\1.\2',
        line
    )

    # 0 - 99 -> 0.99
    line = re.sub(
        r'(\d)\s*-\s*(\d{2})',
        r'\1.\2',
        line
    )

    # 0-.59 -> 0.59
    line = re.sub(
        r'(\d)-\.(\d{2})',
        r'\1.\2',
        line
    )

    # 2 -19 -> 2.19
    line = re.sub(
        r'(\d)\s*-(\d{2})',
        r'\1.\2',
        line
    )

    # 1-82 -> 1.82
    line = re.sub(
        r'(\d)-(\d{2})',
        r'\1.\2',
        line
    )

    # ₹ 50 -> ₹50
    line = re.sub(
        r'([₹$£€])\s+(\d)',
        r'\1\2',
        line
    )

    # Rs. 50
    line = re.sub(
        r'(RS\.?)\s+(\d)',
        r'\1\2',
        line,
        flags=re.IGNORECASE
    )

    # INR 50
    line = re.sub(
        r'(INR)\s+(\d)',
        r'\1\2',
        line,
        flags=re.IGNORECASE
    )

    # ------------------------
    # SIZE FIXES
    # ------------------------

    line = re.sub(
        r'(\d+)\s+(KG|LB|ML|PK|G|L)',
        r'\1\2',
        line,
        flags=re.IGNORECASE
    )

    return line


def parse_receipt_line(line):

    line = normalize_line(line)

    item = {
        "name": None,
        "price": None,
        "size": None,
        "quantity": 1
    }

    # ------------------------
    # PRICE
    # ------------------------

    price_match = re.search(
        r'(?:₹|\$|£|€|RS\.?|INR)?\s*(\d+(?:\.\d{1,2})?)$',
        line,
        flags=re.IGNORECASE
    )

    if price_match:

        item["price"] = float(price_match.group(1))

        line = line[:price_match.start()].strip()

    # ------------------------
    # SIZE
    # ------------------------

    size_match = re.search(
        r'(\d+(?:\.\d+)?(?:KG|LB|ML|PK|G|L))',
        line,
        flags=re.IGNORECASE
    )

    if size_match:

        item["size"] = size_match.group(1).upper()

        line = line.replace(
            size_match.group(1),
            ""
        )

    # ------------------------
    # QUANTITY
    # ------------------------

    quantity_match = re.search(
        r'(\d+)X|X(\d+)|QTY\s*(\d+)',
        line,
        flags=re.IGNORECASE
    )

    if quantity_match:

        qty = next(
            x for x in quantity_match.groups()
            if x is not None
        )

        item["quantity"] = int(qty)

        line = re.sub(
            r'(\d+)X|X(\d+)|QTY\s*(\d+)',
            '',
            line,
            flags=re.IGNORECASE
        )

    # ------------------------
    # CLEAN NAME
    # ------------------------

    line = re.sub(
        r'[,:;]',
        ' ',
        line
    )

    line = re.sub(
        r'\s+',
        ' ',
        line
    ).strip()

    item["name"] = line.upper()

    return item

IGNORE_KEYWORDS = {
    "TOTAL",
    "SUBTOTAL",
    "TAX",
    "CHANGE",
    "CASH",
    "CARD",
    "PAYMENT",
    "STORE",
    "SHOP",
    "WELCOME",
    "THANK",
    "DEBIT",
    "CREDIT",
    "BALANCE",
    "CHICAGO"
}


def is_valid_receipt_item(item):

    if not item["name"]:
        return False

    name = item["name"].upper()

    if len(name) < 2:
        return False

    # for word in IGNORE_KEYWORDS:
    #     if word in name:
    #         return False
    words = name.split()

    for word in words:
        if word in IGNORE_KEYWORDS:
            return False

    return True