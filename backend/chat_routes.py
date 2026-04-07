from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime
from database import chat_collection
from app.services.jarvis_core import run_jarvis
import os
import csv
import re

router = APIRouter()

CHAT_FOLDER = "chat"
os.makedirs(CHAT_FOLDER, exist_ok=True)


class ChatMessageRequest(BaseModel):
    message: str
    chat_id: str | None = None


class NewChatRequest(BaseModel):
    title: str = "New Chat"


def safe_filename(name: str) -> str:
    name = (name or "New Chat").strip()
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:80] if name else "New Chat"


def csv_path_from_title_and_id(title: str, chat_id: str) -> str:
    safe_title = safe_filename(title)
    return os.path.join(CHAT_FOLDER, f"{safe_title}_{chat_id}.csv")


def write_chat_csv(chat):
    chat_id = str(chat["_id"])
    title = chat.get("title", "New Chat")
    file_path = csv_path_from_title_and_id(title, chat_id)

    for file_name in os.listdir(CHAT_FOLDER):
        if file_name.endswith(f"_{chat_id}.csv"):
            old_path = os.path.join(CHAT_FOLDER, file_name)
            if old_path != file_path and os.path.exists(old_path):
                os.remove(old_path)

    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["role", "text"])
        for msg in chat.get("messages", []):
            writer.writerow([msg.get("role", ""), msg.get("text", "")])

    return file_path


def delete_chat_csv(chat):
    chat_id = str(chat["_id"])
    for file_name in os.listdir(CHAT_FOLDER):
        if file_name.endswith(f"_{chat_id}.csv"):
            file_path = os.path.join(CHAT_FOLDER, file_name)
            if os.path.exists(file_path):
                os.remove(file_path)


def serialize_chat(chat):
    return {
        "id": str(chat["_id"]),
        "title": chat.get("title", "New Chat"),
        "messages": chat.get("messages", []),
        "created_at": chat.get("created_at"),
        "updated_at": chat.get("updated_at"),
    }


@router.get("/chats")
async def get_all_chats():
    chats = await chat_collection.find().sort("updated_at", -1).to_list(length=200)
    return [serialize_chat(chat) for chat in chats]


@router.post("/chats/new")
async def create_new_chat(data: NewChatRequest):
    now = datetime.utcnow().isoformat()
    new_chat = {
        "title": data.title,
        "messages": [
            {"role": "bot", "text": "Hello, I am Jarvis. How can I assist you?"}
        ],
        "created_at": now,
        "updated_at": now,
    }
    result = await chat_collection.insert_one(new_chat)
    created_chat = await chat_collection.find_one({"_id": result.inserted_id})
    write_chat_csv(created_chat)
    return serialize_chat(created_chat)


@router.get("/chats/{chat_id}")
async def get_chat(chat_id: str):
    if not ObjectId.is_valid(chat_id):
        raise HTTPException(status_code=400, detail="Invalid chat ID")

    chat = await chat_collection.find_one({"_id": ObjectId(chat_id)})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    return serialize_chat(chat)


@router.delete("/chats/{chat_id}")
async def delete_chat(chat_id: str):
    if not ObjectId.is_valid(chat_id):
        raise HTTPException(status_code=400, detail="Invalid chat ID")

    chat = await chat_collection.find_one({"_id": ObjectId(chat_id)})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    delete_chat_csv(chat)

    result = await chat_collection.delete_one({"_id": ObjectId(chat_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Chat not found")

    return {"success": True}


@router.post("/chat")
async def send_message(data: ChatMessageRequest):
    if not data.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")

    now = datetime.utcnow().isoformat()

    if data.chat_id:
        if not ObjectId.is_valid(data.chat_id):
            raise HTTPException(status_code=400, detail="Invalid chat ID")

        chat = await chat_collection.find_one({"_id": ObjectId(data.chat_id)})
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
    else:
        new_chat = {
            "title": "New Chat",
            "messages": [
                {"role": "bot", "text": "Hello, I am Jarvis. How can I assist you?"}
            ],
            "created_at": now,
            "updated_at": now,
        }
        result = await chat_collection.insert_one(new_chat)
        chat = await chat_collection.find_one({"_id": result.inserted_id})

    bot_reply = run_jarvis(data.message)

    updated_messages = chat["messages"] + [
        {"role": "user", "text": data.message},
        {"role": "bot", "text": bot_reply},
    ]

    updated_title = chat.get("title", "New Chat")
    if updated_title == "New Chat":
        updated_title = data.message[:30] + ("..." if len(data.message) > 30 else "")

    await chat_collection.update_one(
        {"_id": chat["_id"]},
        {
            "$set": {
                "messages": updated_messages,
                "title": updated_title,
                "updated_at": now,
            }
        }
    )

    updated_chat = await chat_collection.find_one({"_id": chat["_id"]})
    write_chat_csv(updated_chat)

    return {
        "chat_id": str(updated_chat["_id"]),
        "response": bot_reply,
        "chat": serialize_chat(updated_chat)
    }