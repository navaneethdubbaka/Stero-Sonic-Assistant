"""
Enhanced chatbot with Langchain tools integration and conversation memory
The LLM can now automatically call tools based on user requests
Supports local Ollama and API providers (Gemini/OpenAI) via llm_factory.
"""

from langchain.agents import AgentExecutor, create_react_agent, create_tool_calling_agent
from langchain.agents import initialize_agent, AgentType
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from typing import Optional, List

from core.llm_factory import create_llm, get_llm_provider, is_local_llm
from core.tools import get_all_tools


class SteroSonicChatbotWithTools:
    def __init__(self, api_key: Optional[str] = None, provider: Optional[str] = None):
        self.provider = provider or get_llm_provider()
        
        # Initialize LLM from centralized factory (temperature 0.7, for_tools=True for JSON format when using Ollama)
        self.llm = create_llm(temperature=0.7, for_tools=True)
        
        # Get all tools
        self.tools = get_all_tools()
        
        # Bind tools to the LLM (required for tool-calling agent; improves Ollama native tool use)
        if self.tools:
            try:
                self.llm = self.llm.bind_tools(self.tools)
                print(f"[LLM] Initialized chatbot with tools using provider: {self.provider} (tools bound)")
            except Exception as e:
                print(f"[LLM] Could not bind tools, agent may use ReAct only: {e}")
        else:
            print(f"[LLM] Initialized chatbot with tools using provider: {self.provider}")
        
        # Create memory with sliding window (keeps last k conversations)
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=20,  # Remember last 20 conversation turns
            input_key="input",
            output_key="output"
        )
        
        # Store conversation history for the ReAct agent (since memory doesn't work directly)
        self.conversation_history: List[dict] = []
        
        # System prompt for the assistant
        self.system_prompt = """You are STERO SONIC, a friendly and helpful AI assistant created by Navaneeth.

Your personality:
- Friendly, helpful, and conversational
- You can have casual conversations about any topic
- You remember what users tell you during the conversation
- You use tools when needed to help users with tasks

When users ask general questions or want to chat:
- Respond naturally and conversationally
- Remember context from earlier in the conversation
- Be helpful and engaging

When users want you to perform actions:
- Use the appropriate tools to complete the task
- Explain what you're doing
- Confirm when tasks are complete

You CAN open and close applications on the user's computer. When the user asks to open, launch, or start an application (e.g. "open Google Chrome", "open Notepad", "launch Spotify", "open WhatsApp web"), you MUST use the open_app tool with the application name. For "WhatsApp web" or "open WhatsApp" use open_app with app_name "WhatsApp" or "Google Chrome" (to open WhatsApp Web in browser). Do not use robot or camera tools for opening apps. Do not say you cannot open applications—you can, using the open_app tool.

You can help with:
- Opening or closing applications (e.g. Google Chrome, Notepad, Spotify, WhatsApp, any installed app)
- General conversation and questions
- Controlling a robot (movement, camera)
- Playing music on Spotify
- Sending emails and WhatsApp messages
- Taking screenshots and photos
- Creating reminders
- Searching the web (for answers that need current page text, use the web_search_and_crawl tool; use search_google only when the user wants Google opened in a browser). When web_search_and_crawl returns content, stay on the user's topic, then end with the line: This is the information regarding <topic>. then the line: Now summarise this: followed by a brief summary.
- And many other tasks using your available tools

Always be friendly and remember what the user has told you earlier in the conversation."""

        # Create agent executor with tools
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the agent with tools: try tool-calling agent first, fallback to ReAct."""
        # ReAct prompt for fallback
        react_prompt_template = """You are STERO SONIC, a friendly AI assistant created by Navaneeth.

{system_prompt}

Previous conversation:
{chat_history}

You have access to the following tools:

{tools}

IMPORTANT:
- For general conversation and questions that don't require tools, just provide a direct, friendly response.
- Only use tools when the user explicitly wants you to perform an action.

Use the following format:

Question: the input question you must answer
Thought: Think about what the user wants. Is this a general question/conversation or do they want me to perform an action?
Action: the action to take (only if needed), should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question (be conversational and friendly)

If no tool is needed:
Question: the input question you must answer
Thought: This is a general question/conversation, I don't need any tools.
Final Answer: [your friendly, conversational response]

Begin!

Question: {input}
Thought: {agent_scratchpad}"""
        react_prompt = PromptTemplate.from_template(react_prompt_template)
        react_prompt = react_prompt.partial(system_prompt=self.system_prompt)

        try:
            # Try tool-calling agent first (better for Ollama native tool support)
            tool_calling_prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            agent = create_tool_calling_agent(self.llm, self.tools, tool_calling_prompt)
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5,
                return_intermediate_steps=True,
            )
            self.use_agent_executor = True
            self.use_tool_calling_agent = True
            print("[LLM] Using tool-calling agent")
        except Exception as e:
            # Fallback to ReAct agent
            print(f"[LLM] Tool-calling agent failed, falling back to ReAct: {e}")
            try:
                agent = create_react_agent(self.llm, self.tools, react_prompt)
                self.agent_executor = AgentExecutor(
                    agent=agent,
                    tools=self.tools,
                    verbose=True,
                    handle_parsing_errors=True,
                    max_iterations=5,
                    return_intermediate_steps=True,
                )
                self.use_agent_executor = True
                self.use_tool_calling_agent = False
                print("[LLM] Successfully initialized ReAct agent with conversation memory")
            except Exception as e2:
                print(f"Warning: Could not use create_react_agent, trying initialize_agent: {e2}")
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
                            "system_message": self.system_prompt
                        }
                    )
                    self.use_agent_executor = False
                    self.use_tool_calling_agent = False
                    print("[LLM] Successfully initialized CHAT_CONVERSATIONAL_REACT agent")
                except Exception as e3:
                    print(f"Error initializing agent: {e3}")
                    raise
    
    def _format_chat_history(self) -> str:
        """Format conversation history for the prompt (ReAct agent)."""
        if not self.conversation_history:
            return "No previous conversation."
        formatted = []
        recent_history = self.conversation_history[-20:]
        for entry in recent_history:
            if entry["role"] == "user":
                formatted.append(f"User: {entry['content']}")
            else:
                formatted.append(f"Assistant: {entry['content']}")
        return "\n".join(formatted)

    def _get_chat_history_messages(self, exclude_last: int = 0):
        """Return conversation history as list of messages (for tool-calling agent). exclude_last=1 to omit the current user message."""
        if not self.conversation_history:
            return []
        recent = self.conversation_history[-20 - exclude_last:]
        if exclude_last:
            recent = recent[:-exclude_last]
        messages = []
        for entry in recent:
            if entry["role"] == "user":
                messages.append(HumanMessage(content=entry["content"]))
            else:
                messages.append(AIMessage(content=entry["content"]))
        return messages
    
    def chat(self, message: str, return_reasoning: bool = False) -> dict:
        """Chat with the assistant using tools
        
        Returns:
            str if return_reasoning=False
            dict with 'response' and 'reasoning' if return_reasoning=True
        """
        reasoning_steps = []
        reasoning_steps.append(f"💭 Received request: {message}")
        reasoning_steps.append(f"🤔 Analyzing request and determining appropriate action...")
        
        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": message
            })
            
            # Format chat history for context
            chat_history = self._format_chat_history()
            
            # Use AgentExecutor style if available (better for step tracking)
            if hasattr(self, 'use_agent_executor') and self.use_agent_executor:
                # Tool-calling agent expects chat_history as list of messages; ReAct expects string
                if getattr(self, 'use_tool_calling_agent', False):
                    history_messages = self._get_chat_history_messages(exclude_last=1)
                    invoke_input = {"input": message, "chat_history": history_messages}
                else:
                    invoke_input = {"input": message, "chat_history": chat_history}
                result = self.agent_executor.invoke(invoke_input)
                
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
                    reasoning_steps.append("💬 Responded conversationally (no tools needed)")
                
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
                    "chat_history": chat_history
                })
                output = result.get("output", "I apologize, but I couldn't process that request.")
                
                if "intermediate_steps" in result:
                    for step in result["intermediate_steps"]:
                        action, observation = step
                        tool_name = action.tool if hasattr(action, 'tool') else str(action)
                        reasoning_steps.append(f"🔧 Used tool: {tool_name}")
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": output
            })
            
            reasoning_steps.append("✅ Response generated")
            
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
                response = f"I encountered an issue: {error_msg}. Let me try to help you another way."
            
            # Still add to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            if return_reasoning:
                return {
                    "response": response,
                    "reasoning": reasoning_steps,
                    "tools_used": []
                }
            return response
    
    def get_conversation_history(self) -> List[dict]:
        """Get the full conversation history"""
        return self.conversation_history.copy()
    
    def reset(self):
        """Reset conversation memory"""
        self.conversation_history.clear()
        self.memory.clear()
        print("[LLM] Conversation memory cleared")


# Global instance
chatbot_with_tools: Optional[SteroSonicChatbotWithTools] = None


def get_chatbot_with_tools() -> SteroSonicChatbotWithTools:
    """Get or create chatbot instance with tools"""
    global chatbot_with_tools
    if chatbot_with_tools is None:
        chatbot_with_tools = SteroSonicChatbotWithTools()
    return chatbot_with_tools


def reset_chatbot():
    """Reset the chatbot conversation"""
    global chatbot_with_tools
    if chatbot_with_tools is not None:
        chatbot_with_tools.reset()
