"""
Enhanced chatbot with Langchain tools integration
The LLM can now automatically call tools based on user requests
Supports both Gemini and OpenAI as LLM providers
"""

import os
from langchain.agents import AgentExecutor, create_react_agent
from langchain.agents import initialize_agent, AgentType
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage, HumanMessage
from typing import Optional

from core.tools import get_all_tools


def get_llm_provider():
    """Get the configured LLM provider from environment"""
    return os.getenv("LLM_PROVIDER", "gemini").lower()


def create_llm_for_tools(provider: Optional[str] = None):
    """Create LLM instance based on provider configuration (optimized for tool use)"""
    provider = provider or get_llm_provider()
    
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return ChatOpenAI(
            model_name=model,
            temperature=0.7,
            openai_api_key=api_key,
            model_kwargs={}
        )
    else:  # Default to Gemini
        from langchain_google_genai import ChatGoogleGenerativeAI
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.7,
            google_api_key=api_key
        )


class SteroSonicChatbotWithTools:
    def __init__(self, api_key: Optional[str] = None, provider: Optional[str] = None):
        self.provider = provider or get_llm_provider()
        
        # Initialize LLM based on provider
        self.llm = create_llm_for_tools(self.provider)
        print(f"[LLM] Initialized chatbot with tools using provider: {self.provider}")
        
        # Get all tools
        self.tools = get_all_tools()
        
        # Create memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize conversation
        self.memory.chat_memory.add_user_message(
            "YOU ARE A CHAT BOT YOUR NAME IS \"STERO SONIC\" YOU WERE CREATED BY NAVANEETH. YOU NEED TO ANSWER ALL THE GENERAL QUESTIONS ASKED BY THE USERS AND HELP THEM WITH TASKS USING AVAILABLE TOOLS."
        )
        self.memory.chat_memory.add_ai_message(
            "Sure, I am STERO SONIC, a chatbot created by Navaneeth. I am here to answer your general questions and help you with various tasks using my available tools. How can I assist you today?"
        )
        
        # Create agent executor with tools - using AgentExecutor for better step tracking
        try:
            # Try to create agent executor that supports intermediate steps
            from langchain.agents import AgentExecutor, create_react_agent
            
            # Use ReAct prompt template
            prompt_template = """You are STERO SONIC, an AI assistant created by Navaneeth.

You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Question: {input}
Thought: {agent_scratchpad}"""
            
            prompt = PromptTemplate.from_template(prompt_template)
            
            agent = create_react_agent(self.llm, self.tools, prompt)
            
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5,
                return_intermediate_steps=True
            )
            self.use_agent_executor = True
        except Exception as e:
            # Fallback to initialize_agent
            print(f"Warning: Could not use create_react_agent, trying initialize_agent: {e}")
            try:
                self.agent_executor = initialize_agent(
                    tools=self.tools,
                    llm=self.llm,
                    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
                    memory=self.memory,
                    verbose=True,
                    handle_parsing_errors=True,
                    max_iterations=5,
                    agent_kwargs={
                        "system_message": """You are STERO SONIC, an AI assistant created by Navaneeth. 
You have access to various tools to help users with their tasks. 

When a user asks you to do something, you should:
1. Understand what the user wants
2. Choose the appropriate tool(s) to accomplish the task
3. Use the tool(s) with the correct parameters
4. Provide a clear, helpful response

Always be helpful and use the available tools to complete user requests."""
                    }
                )
                self.use_agent_executor = False
            except Exception as e2:
                print(f"Error initializing agent: {e2}")
                raise
    
    def chat(self, message: str, return_reasoning: bool = False) -> dict:
        """Chat with the assistant using tools
        
        Returns:
            str if return_reasoning=False
            dict with 'response' and 'reasoning' if return_reasoning=True
        """
        reasoning_steps = []
        reasoning_steps.append(f"💭 Received request: {message}")
        reasoning_steps.append(f"🤔 Analyzing request and determining appropriate tools...")
        
        try:
            # Use AgentExecutor style if available (better for step tracking)
            if hasattr(self, 'use_agent_executor') and self.use_agent_executor:
                # AgentExecutor style - can capture intermediate steps
                result = self.agent_executor.invoke({
                    "input": message
                })
                
                # Extract intermediate steps
                if "intermediate_steps" in result and result["intermediate_steps"]:
                    for i, step in enumerate(result["intermediate_steps"]):
                        action, observation = step
                        tool_name = action.tool if hasattr(action, 'tool') else "unknown_tool"
                        tool_input = action.tool_input if hasattr(action, 'tool_input') else ""
                        
                        reasoning_steps.append(f"🤔 Step {i+1}: Decided to use {tool_name}")
                        
                        # Format tool input nicely
                        if isinstance(tool_input, dict):
                            input_str = ", ".join([f"{k}: {v}" for k, v in tool_input.items()])
                        else:
                            input_str = str(tool_input)
                        reasoning_steps.append(f"🔧 Executing: {tool_name}({input_str})")
                        
                        # Format observation
                        if isinstance(observation, str):
                            obs_str = observation[:100] + "..." if len(observation) > 100 else observation
                        else:
                            obs_str = str(observation)[:100]
                        reasoning_steps.append(f"📊 Result: {obs_str}")
                else:
                    reasoning_steps.append("🤔 Using LLM reasoning (no tool steps captured)")
                
                output = result.get("output", "I apologize, but I couldn't process that request.")
                
            elif hasattr(self.agent_executor, 'run'):
                # For initialize_agent style
                reasoning_steps.append("🤔 Processing with LLM agent...")
                result = self.agent_executor.run(input=message)
                reasoning_steps.append("✅ LLM processed the request")
                output = result
            else:
                # Fallback
                reasoning_steps.append("⚠️ Using fallback processing...")
                result = self.agent_executor.invoke({
                    "input": message,
                    "chat_history": self.memory.chat_memory.messages if hasattr(self.memory, 'chat_memory') else []
                })
                output = result.get("output", "I apologize, but I couldn't process that request.")
                
                if "intermediate_steps" in result:
                    for step in result["intermediate_steps"]:
                        action, observation = step
                        tool_name = action.tool if hasattr(action, 'tool') else str(action)
                        reasoning_steps.append(f"🔧 Used tool: {tool_name}")
            
            reasoning_steps.append("✅ Task completed")
            
            if return_reasoning:
                return {
                    "response": output,
                    "reasoning": reasoning_steps,
                    "tools_used": [s for s in reasoning_steps if "Executing:" in s or "Used tool:" in s]
                }
            return output
        except Exception as e:
            error_msg = str(e)
            reasoning_steps.append(f"❌ Error occurred: {error_msg}")
            # Handle parsing errors gracefully
            if "Could not parse" in error_msg or "parsing" in error_msg.lower():
                response = "I apologize, but I couldn't understand that request. Could you please rephrase it?"
            else:
                response = f"An error occurred: {error_msg}"
            
            if return_reasoning:
                return {
                    "response": response,
                    "reasoning": reasoning_steps,
                    "tools_used": []
                }
            return response
    
    def reset(self):
        """Reset conversation memory"""
        self.memory.clear()
        # Reinitialize conversation
        self.memory.chat_memory.add_user_message(
            "YOU ARE A CHAT BOT YOUR NAME IS \"STERO SONIC\" YOU WERE CREATED BY NAVANEETH. YOU NEED TO ANSWER ALL THE GENERAL QUESTIONS ASKED BY THE USERS AND HELP THEM WITH TASKS USING AVAILABLE TOOLS."
        )
        self.memory.chat_memory.add_ai_message(
            "Sure, I am STERO SONIC, a chatbot created by Navaneeth. I am here to answer your general questions and help you with various tasks using my available tools. How can I assist you today?"
        )

# Global instance
chatbot_with_tools: Optional[SteroSonicChatbotWithTools] = None

def get_chatbot_with_tools() -> SteroSonicChatbotWithTools:
    """Get or create chatbot instance with tools"""
    global chatbot_with_tools
    if chatbot_with_tools is None:
        chatbot_with_tools = SteroSonicChatbotWithTools()
    return chatbot_with_tools

