import os
import json
import base64
from groq import Groq

class GroqClient:
    client = None

    @classmethod
    def get_client(cls):
        if not cls.client:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                print("Warning: GROQ_API_KEY not found.")
                return None
            cls.client = Groq(api_key=api_key)
        return cls.client

    @classmethod
    def get_completion(cls, prompt: str, json_mode: bool = False):
        """Single-turn completion (legacy, used for tool calls)."""
        messages = [{"role": "user", "content": prompt}]
        return cls.get_completion_with_history(messages, json_mode=json_mode)

    @classmethod
    def get_completion_with_history(cls, messages: list, json_mode: bool = False):
        """
        Multi-turn completion. messages should be a list of:
        {"role": "system"|"user"|"assistant", "content": "..."}
        """
        client = cls.get_client()
        if not client:
            return None
        try:
            kwargs = {
                "messages": messages,
                "model": "llama-3.3-70b-versatile",
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            chat_completion = client.chat.completions.create(**kwargs)
            content = chat_completion.choices[0].message.content
            if json_mode:
                return json.loads(content)
            return content
        except Exception as e:
            print(f"Groq API Error: {e}")
            return None

    @classmethod
    def analyze_image(cls, image_path: str) -> dict | None:
        """
        Use Groq vision model to classify an image.
        Returns: {category, is_sensitive, doc_type} or None on failure.
        """
        client = cls.get_client()
        if not client:
            return None

        try:
            # Read and base64-encode the image
            with open(image_path, "rb") as f:
                image_data = base64.standard_b64encode(f.read()).decode("utf-8")

            # Detect MIME type from extension
            ext = image_path.rsplit(".", 1)[-1].lower()
            mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                        "gif": "image/gif", "webp": "image/webp"}
            mime = mime_map.get(ext, "image/jpeg")

            prompt = """Analyze this image and respond with ONLY valid JSON in this exact format:
{
  "category": "Person|Receipt|Document|Note|General",
  "is_sensitive": true|false,
  "doc_type": "selfie|group_photo|receipt|invoice|aadhaar|pan_card|passport|bank_statement|note|general"
}

Rules:
- "Person" if image contains human faces/selfies
- "Receipt" if it's a shopping receipt or invoice  
- "Document" if it's an ID card (Aadhaar, PAN, passport), bank statement, or official document
- "Note" if it's handwritten or typed notes
- "General" for anything else
- "is_sensitive" = true ONLY for ID cards, bank statements, passports, official documents
- Be concise, respond ONLY with JSON"""

            completion = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime};base64,{image_data}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=100
            )
            result = json.loads(completion.choices[0].message.content)
            print(f"[AI Classification] {image_path}: {result}")
            return result
        except Exception as e:
            print(f"[Groq Vision] Error analyzing image: {e}")
            return None
