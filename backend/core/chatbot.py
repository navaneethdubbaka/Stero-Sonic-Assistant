import os
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from typing import Optional

# Import tools-enabled chatbot as alternative
try:
    from core.chatbot_with_tools import get_chatbot_with_tools
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False


def get_llm_provider():
    """Get the configured LLM provider from environment"""
    return os.getenv("LLM_PROVIDER", "gemini").lower()


def create_llm(provider: Optional[str] = None):
    """Create LLM instance based on provider configuration"""
    provider = provider or get_llm_provider()
    
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return ChatOpenAI(
            model=model,
            temperature=0.9,
            openai_api_key=api_key
        )
    else:  # Default to Gemini
        from langchain_google_genai import ChatGoogleGenerativeAI
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.9,
            google_api_key=api_key
        )


class SteroSonicChatbot:
    def __init__(self, api_key: Optional[str] = None, provider: Optional[str] = None):
        self.provider = provider or get_llm_provider()
        self.llm = create_llm(self.provider)
        print(f"[LLM] Initialized chatbot with provider: {self.provider}")
        
        self.memory = ConversationBufferMemory(return_messages=True)
        
        # System message
        self.system_message = """YOU ARE A CHAT BOT YOUR NAME IS "STERO SONIC" YOU WERE CREATED BY NAVANEETH. 
        YOU NEED TO ANSWER ALL THE GENERAL QUESTIONS ASKED BY THE USERS."""
        
        # Initialize conversation history
        self.memory.chat_memory.add_user_message(
            "YOU ARE A CHAT BOT YOURS NAME IS \"STERO SONIC\" YOU WERE CREATED BY NAVANEETH. YOU NEED TO ANSWER ALL THE GENERAL QUESTIONS ASKED BY THE USERS."
        )
        self.memory.chat_memory.add_ai_message(
            "Sure, I am STERO SONIC, a chatbot created by Navaneeth. I am here to answer your general questions to the best of my ability."
        )
    
    def chat(self, message: str) -> str:
        """Chat with the assistant"""
        try:
            # Add user message to memory
            self.memory.chat_memory.add_user_message(message)
            
            # Create prompt with system message and history
            messages = [
                SystemMessage(content=self.system_message),
            ] + self.memory.chat_memory.messages
            
            # Get response
            response = self.llm.invoke(messages)
            response_text = response.content
            
            # Add AI response to memory
            self.memory.chat_memory.add_ai_message(response_text)
            
            return response_text
        except Exception as e:
            return f"Error: {str(e)}"
    
    def reset(self):
        """Reset conversation memory"""
        self.memory.clear()

# Global instance (will be initialized in main)
chatbot: Optional[SteroSonicChatbot] = None

def get_chatbot() -> SteroSonicChatbot:
    """Get or create chatbot instance"""
    global chatbot
    if chatbot is None:
        chatbot = SteroSonicChatbot()
    return chatbot

