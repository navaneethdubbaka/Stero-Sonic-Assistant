import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from core.chatbot import get_chatbot, TOOLS_AVAILABLE
from core.speech import tts

# Try to import tools-enabled chatbot
try:
    from core.chatbot_with_tools import get_chatbot_with_tools
except ImportError:
    get_chatbot_with_tools = None

router = APIRouter()

class ChatInput(BaseModel):
    message: str
    use_tools: Optional[bool] = True  # Default to using tools if available
    return_reasoning: Optional[bool] = True  # Return LLM reasoning steps

class ChatReset(BaseModel):
    confirm: bool = False

@router.post("/chat")
async def chat(chat_input: ChatInput):
    """Chat with Stereo Sonic (with optional tools and reasoning)"""
    try:
        # Use tools-enabled chatbot if available and requested
        if chat_input.use_tools and TOOLS_AVAILABLE and get_chatbot_with_tools:
            chatbot = get_chatbot_with_tools()
            if chat_input.return_reasoning:
                result = chatbot.chat(chat_input.message, return_reasoning=True)
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "reasoning": result.get("reasoning", []),
                    "tools_used": result.get("tools_used", []),
                    "has_tools": True
                }
            else:
                response = chatbot.chat(chat_input.message, return_reasoning=False)
                return {"success": True, "response": response, "tools_used": True}
        else:
            # Use basic chatbot
            chatbot = get_chatbot()
            response = chatbot.chat(chat_input.message)
            return {
                "success": True,
                "response": response,
                "reasoning": ["Using basic chatbot mode (no tools)"],
                "tools_used": False
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "reasoning": [f"Error: {str(e)}"]
        }

@router.post("/chat/tts")
async def chat_with_tts(chat_input: ChatInput):
    """Chat with Stereo Sonic and get TTS response (with optional tools)"""
    try:
        # Use tools-enabled chatbot if available and requested
        if chat_input.use_tools and TOOLS_AVAILABLE and get_chatbot_with_tools:
            chatbot = get_chatbot_with_tools()
            response = chatbot.chat(chat_input.message)
        else:
            chatbot = get_chatbot()
            response = chatbot.chat(chat_input.message)
        
        tts.speak(response)
        return {"success": True, "response": response, "tools_used": chat_input.use_tools and TOOLS_AVAILABLE}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/reset")
async def reset_chatbot():
    """Reset chatbot conversation"""
    try:
        chatbot = get_chatbot()
        chatbot.reset()
        return {"success": True, "message": "Conversation reset"}
    except Exception as e:
        return {"success": False, "error": str(e)}

