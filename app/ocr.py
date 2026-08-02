import cv2
import easyocr


class ReceiptOCR:

    def __init__(self):

        self.reader = easyocr.Reader(
            ['en'],
            gpu=False
        )

    def preprocess(self, image_path):

        image = cv2.imread(image_path)

        if image is None:
            raise ValueError(f"Unable to load image: {image_path}")

        # Upscale image for better OCR
        image = cv2.resize(
            image,
            None,
            fx=3,
            fy=3,
            interpolation=cv2.INTER_CUBIC
        )

        # Convert to grayscale
        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )

        # Remove noise
        gray = cv2.fastNlMeansDenoising(
            gray,
            None,
            10,
            7,
            21
        )

        # Adaptive threshold
        thresh = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            15
        )

        return thresh

    def extract_text(self, image_path):

        processed = self.preprocess(image_path)

        results = self.reader.readtext(
            processed,
            paragraph=False,
            decoder="beamsearch",
            width_ths=0.8,
            ycenter_ths=0.5,
            height_ths=0.5
        )

        texts = []

        for bbox, text, confidence in results:

            confidence = float(confidence)

            # Ignore very weak detections
            if confidence < 0.20:
                continue

            text = text.strip()

            # ------------------------
            # Common OCR corrections
            # ------------------------

            # S25.97 -> $25.97
            if text.startswith("S") and len(text) > 1 and text[1].isdigit():
                text = "$" + text[1:]

            # 5 .95 -> 5.95
            text = text.replace(" . ", ".")
            text = text.replace(" .", ".")
            text = text.replace(". ", ".")

            # OCR mistakes
            text = text.replace("|", "1")

            # Ilb -> 1lb
            if text.lower().endswith("lb"):
                text = text.replace("I", "1")

            texts.append({
                "bbox": bbox,
                "text": text,
                "confidence": round(confidence, 3)
            })

        return texts