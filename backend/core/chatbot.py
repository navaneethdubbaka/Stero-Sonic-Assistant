import logging
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from typing import Optional

from core.llm_factory import create_llm, get_llm_provider

# Import tools-enabled chatbot as alternative (catch any failure: ImportError, PydanticUserError, etc.)
TOOLS_AVAILABLE = False
get_chatbot_with_tools = None
reset_tools_chatbot = None
_tools_import_error = None
try:
    from core.chatbot_with_tools import get_chatbot_with_tools, reset_chatbot as reset_tools_chatbot
    TOOLS_AVAILABLE = True
except Exception as e:
    _tools_import_error = str(e)
    logging.exception("Tools-enabled chatbot failed to load (TOOLS_AVAILABLE=False): %s", e)

# Initial conversation seed (same as before, without using langchain.memory)
_INITIAL_USER = "YOU ARE A CHAT BOT YOURS NAME IS \"STERO SONIC\" YOU WERE CREATED BY NAVANEETH. YOU NEED TO ANSWER ALL THE GENERAL QUESTIONS ASKED BY THE USERS."
_INITIAL_AI = "Sure, I am STERO SONIC, a chatbot created by Navaneeth. I am here to answer your general questions to the best of my ability."


class SteroSonicChatbot:
    def __init__(self, api_key: Optional[str] = None, provider: Optional[str] = None):
        self.provider = provider or get_llm_provider()
        self.llm = create_llm(temperature=0.9)
        print(f"[LLM] Initialized chatbot with provider: {self.provider}")
        
        self.system_message = """YOU ARE A CHAT BOT YOUR NAME IS "STERO SONIC" YOU WERE CREATED BY NAVANEETH. 
        YOU NEED TO ANSWER ALL THE GENERAL QUESTIONS ASKED BY THE USERS."""
        # In-memory chat history (avoids langchain.memory for version compatibility)
        self._chat_history = [
            HumanMessage(content=_INITIAL_USER),
            AIMessage(content=_INITIAL_AI),
        ]
    
    def chat(self, message: str) -> str:
        """Chat with the assistant"""
        try:
            self._chat_history.append(HumanMessage(content=message))
            messages = [SystemMessage(content=self.system_message)] + self._chat_history
            response = self.llm.invoke(messages)
            response_text = response.content
            self._chat_history.append(AIMessage(content=response_text))
            return response_text
        except Exception as e:
            return f"Error: {str(e)}"
    
    def reset(self):
        """Reset conversation memory"""
        self._chat_history = [
            HumanMessage(content=_INITIAL_USER),
            AIMessage(content=_INITIAL_AI),
        ]

# Global instance (will be initialized in main)
chatbot: Optional[SteroSonicChatbot] = None

def get_chatbot() -> SteroSonicChatbot:
    """Get or create chatbot instance"""
    global chatbot
    if chatbot is None:
        chatbot = SteroSonicChatbot()
    return chatbot

