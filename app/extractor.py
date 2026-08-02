import re


def extract_size(text):
    """
    Extract sizes like:
    500ml
    1L
    2kg
    250 g
    """

    pattern = r'(\d+(?:\.\d+)?)\s?(kg|ml|l|g)'

    match = re.search(pattern, text.lower())

    if match:
        return match.group()

    return None