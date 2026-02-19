from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..ai_services.groq_client import GroqClient
from pydantic import BaseModel
from typing import List
import json
from ..ai_services.tools import TOOL_REGISTRY

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

class ChatMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []   # Full conversation history from frontend

@router.post("/")
async def chat_with_agent(
    request: ChatRequest,
    user_id: int = 1,  # TODO: get from JWT when auth is wired
    db: Session = Depends(get_db)
):
    from ..models.photo import Photo
    from ..models.person import Person
    from ..models.user import User

    # --- Build live context from DB ---
    photo_count = db.query(Photo).filter(Photo.user_id == user_id).count()
    person_count = db.query(Person).filter(Person.user_id == user_id).count()
    recent_photos = db.query(Photo).filter(Photo.user_id == user_id).order_by(Photo.created_at.desc()).limit(3).all()
    recent_context = ", ".join([f"Photo {p.id} ({p.category}, path: {p.path})" for p in recent_photos]) or "None"

    # Include receipt summary in context
    from ..models.receipt import Receipt
    from sqlalchemy import func as sqlfunc
    receipt_total = db.query(sqlfunc.sum(Receipt.amount)).join(Photo).filter(Photo.user_id == user_id).scalar() or 0

    system_prompt = f"""You are PersonaLens, a powerful AI assistant with FULL ACCESS to the user's photo library, people, receipts, vault, and messaging.
Be helpful, concise, and action-oriented. Always confirm before deleting.

=== USER CONTEXT ===
- user_id: {user_id}
- Total Photos: {photo_count}
- Recognized People: {person_count}
- Recent Uploads: {recent_context}
- Total Receipt Spending: ₹{receipt_total:.2f}

=== AVAILABLE TOOLS ===
You have FULL CONTROL. Use these tools when the user asks you to act:

📷 PHOTOS:
1. list_photos(user_id, category=None) — list all photos; category: Person/Receipt/Document/Note/General
2. delete_photo(photo_id, user_id) — permanently delete a photo from disk and DB
3. move_photo(photo_id, category, user_id) — move photo to a different category

👥 PEOPLE:
4. list_people(user_id) — list all named people
5. create_person(name, user_id) — create a new person profile
6. tag_person_in_photo(photo_id, person_id, user_id) — tag who is in a photo

🧾 RECEIPTS:
7. get_receipt_summary(user_id) — show spending totals and category breakdown
8. delete_receipt(receipt_id, user_id) — delete a receipt record

🔐 VAULT:
9. list_vault(user_id) — list all files in the secure vault

📨 MESSAGING:
10. send_email(to_email, subject, message) — send email via Gmail SMTP
11. send_whatsapp(phone_number, message, image_path=None) — send WhatsApp text or image
    - image_path MUST be the exact file path like "uploads/photos/uuid.jpg" (NOT the photo ID)

=== RULES ===
- user_id is ALWAYS: {user_id}
- When you need IDs or Paths, call list_photos first
- For WhatsApp images: use the 'path' from list_photos/recent_context (e.g., 'photos/uuid.jpg') and prefix with 'uploads/'
- Before deleting anything, tell the user what you're about to delete and confirm
- To call a tool, respond with ONLY this JSON (nothing else):
{{"tool": "tool_name", "args": {{"arg": "value"}}}}
- For normal replies, use plain text only"""



    # --- Build messages array with history ---
    messages = [{"role": "system", "content": system_prompt}]
    for msg in request.history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": request.message})

    # --- Get LLM response with full history ---
    response_content = GroqClient.get_completion_with_history(messages)

    if not response_content:
        raise HTTPException(status_code=500, detail="AI Service unavailable")

    # --- Parse tool calls ---
    try:
        cleaned = response_content.strip()
        # Find JSON block even if wrapped in markdown
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()

        if cleaned.startswith("{") and cleaned.endswith("}"):
            tool_call = json.loads(cleaned)
            tool_name = tool_call.get("tool")
            tool_args = tool_call.get("args", {})

            if tool_name in TOOL_REGISTRY:
                print(f"[TOOL] Executing: {tool_name} with args {tool_args}")

                # Inject user SMTP credentials for emails
                if tool_name == "send_email":
                    current_user = db.query(User).filter(User.id == user_id).first()
                    if current_user and current_user.smtp_email and current_user.smtp_password:
                        tool_args["smtp_user"] = current_user.smtp_email
                        tool_args["smtp_pass"] = current_user.smtp_password

                result = TOOL_REGISTRY[tool_name](**tool_args)
                friendly_msg = result.get("message", "Done!")
                return {
                    "response": f"✓ {friendly_msg}",
                    "tool_result": result
                }
    except (json.JSONDecodeError, KeyError, Exception) as e:
        print(f"[TOOL PARSE] Not a tool call, treating as text: {e}")

    return {"response": response_content}
