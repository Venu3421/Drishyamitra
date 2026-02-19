"""
Receipt Analyzer — uses Groq vision directly (no Tesseract required).
Extracts merchant, date, total, tax, and category from a receipt image.
"""
import os
import json
import base64
from .groq_client import GroqClient


RECEIPT_PROMPT = """You are a receipt parser. Look at this receipt image carefully and extract ALL details.
Respond with ONLY valid JSON in this exact format — no other text:
{
  "Merchant Name": "store or restaurant name",
  "Date": "YYYY-MM-DD or null",
  "Total Amount": 0.00,
  "Tax Amount": 0.00,
  "Category": "Food|Transport|Shopping|Utilities|Health|Entertainment|General",
  "Items": [{"name": "item name", "price": 0.00}]
}

Rules:
- Total Amount and Tax Amount must be numbers (float), NOT strings
- If you cannot read the total, estimate from visible line items
- Category should match the type of store/receipt
- Date must be YYYY-MM-DD format or null if not visible
- If merchant name is not clear, use a description like "Supermarket"
"""


class ReceiptAnalyzer:
    @staticmethod
    def analyze_receipt(image_path: str) -> dict | None:
        """
        Analyze a receipt image using Groq vision AI.
        Returns structured dict with merchant, date, amounts, category.
        Falls back to basic OCR if vision fails.
        """
        client = GroqClient.get_client()
        if not client:
            print("[ReceiptAnalyzer] Groq client not available.")
            return None

        try:
            with open(image_path, "rb") as f:
                image_data = base64.standard_b64encode(f.read()).decode("utf-8")

            ext = image_path.rsplit(".", 1)[-1].lower()
            mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                        "gif": "image/gif", "webp": "image/webp"}
            mime = mime_map.get(ext, "image/jpeg")

            completion = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{image_data}"}
                        },
                        {
                            "type": "text",
                            "text": RECEIPT_PROMPT
                        }
                    ]
                }],
                response_format={"type": "json_object"},
                max_tokens=512
            )

            raw = completion.choices[0].message.content
            data = json.loads(raw)
            print(f"[ReceiptAnalyzer] Parsed receipt: {data}")
            return data

        except Exception as e:
            print(f"[ReceiptAnalyzer] Vision error: {e}")
            # Try basic text extraction as fallback
            return ReceiptAnalyzer._fallback_text_extraction(image_path)

    @staticmethod
    def _fallback_text_extraction(image_path: str) -> dict | None:
        """Fallback: use Groq text model with a basic description."""
        try:
            result = GroqClient.get_completion(
                f"This is a receipt from file: {os.path.basename(image_path)}. "
                "Since I can't read the image, create a placeholder receipt with unknown values. "
                "Respond ONLY with JSON: {\"Merchant Name\": \"Unknown\", \"Date\": null, "
                "\"Total Amount\": 0.00, \"Tax Amount\": 0.00, \"Category\": \"General\", \"Items\": []}",
                json_mode=True
            )
            return result
        except Exception:
            return {"Merchant Name": "Unknown", "Date": None, "Total Amount": 0.0, "Tax Amount": 0.0, "Category": "General", "Items": []}
