import logging
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from core.chatbot import (
    get_chatbot,
    TOOLS_AVAILABLE,
    get_chatbot_with_tools,
    reset_tools_chatbot,
    _tools_import_error,
)
from core.speech import tts

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
            # Use basic chatbot (tools unavailable or not requested)
            chatbot = get_chatbot()
            response = chatbot.chat(chat_input.message)
            out = {
                "success": True,
                "response": response,
                "reasoning": ["Using basic chatbot mode (no tools)"],
                "tools_used": False,
                "tools_available": False,
            }
            if _tools_import_error:
                out["tools_unavailable_reason"] = _tools_import_error
            return out
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
async def reset_conversation():
    """Reset chatbot conversation memory"""
    try:
        # Reset basic chatbot
        chatbot = get_chatbot()
        chatbot.reset()
        
        # Reset tools-enabled chatbot if available
        if reset_tools_chatbot:
            reset_tools_chatbot()
        
        return {"success": True, "message": "Conversation memory cleared"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/history")
async def get_conversation_history():
    """Get the conversation history"""
    try:
        if get_chatbot_with_tools:
            chatbot = get_chatbot_with_tools()
            history = chatbot.get_conversation_history()
            return {
                "success": True,
                "history": history,
                "message_count": len(history)
            }
        else:
            return {
                "success": True,
                "history": [],
                "message_count": 0,
                "note": "Tools-enabled chatbot not available"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/status")
async def get_chatbot_status():
    """Get chatbot status and capabilities"""
    try:
        tools_available = TOOLS_AVAILABLE and get_chatbot_with_tools is not None
        
        status = {
            "success": True,
            "tools_available": tools_available,
            "memory_enabled": True,
            "provider": "unknown"
        }
        if not tools_available and _tools_import_error:
            status["tools_unavailable_reason"] = _tools_import_error

        if tools_available:
            chatbot = get_chatbot_with_tools()
            status["provider"] = chatbot.provider
            status["conversation_length"] = len(chatbot.conversation_history)
            status["tools_count"] = len(chatbot.tools) if hasattr(chatbot, 'tools') else 0
        
        return status
    except Exception as e:
        return {"success": False, "error": str(e)}

