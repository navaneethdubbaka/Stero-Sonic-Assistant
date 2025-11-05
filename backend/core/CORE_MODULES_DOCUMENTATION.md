# Core Modules Documentation

This document provides comprehensive documentation for all modules in the `backend/core` directory of the Stero Sonic Assistant project.

---

## Table of Contents

1. [__init__.py](#__init__py)
2. [chatbot.py](#chatbotpy)
3. [chatbot_with_tools.py](#chatbot_with_toolspy)
4. [tools.py](#toolspy)
5. [data_analyzer.py](#data_analyzerpy)
6. [intent_parser.py](#intent_parserpy)
7. [speech.py](#speechpy)

---

## __init__.py

### Overview
The `__init__.py` file serves as the package initialization file for the `core` module. It marks the directory as a Python package and can be used to define package-level imports and exports.

### File Contents
```python
# Core package
```

### Purpose
- **Package Marker**: Makes the `core` directory a Python package, allowing it to be imported as a module
- **Namespace Definition**: Provides a namespace for organizing core functionality
- **Future Extensibility**: Can be extended to include package-level imports or initialization code

### Usage
When importing from the core package, Python recognizes it as a module:
```python
from core.chatbot import get_chatbot
from core.tools import get_all_tools
```

### Dependencies
None - This is a minimal package initialization file.

---

## chatbot.py

### Overview
`chatbot.py` implements a basic conversational chatbot using Google's Gemini AI model via LangChain. This module provides a simple chatbot interface without tool integration capabilities.

### Key Components

#### Class: `SteroSonicChatbot`

A chatbot class that handles conversational interactions with memory management.

##### Initialization (`__init__`)
```python
def __init__(self, api_key: Optional[str] = None)
```

**Parameters:**
- `api_key` (Optional[str]): Google Gemini API key. If not provided, reads from `GEMINI_API_KEY` environment variable.

**Initialization Process:**
1. **API Key Validation**: Retrieves API key from parameter or environment variable, raises error if missing
2. **LLM Setup**: Initializes `ChatGoogleGenerativeAI` with:
   - Model: `gemini-2.5-flash`
   - Temperature: `0.9` (high creativity)
   - API key configuration
3. **Memory Initialization**: Creates `ConversationBufferMemory` to store conversation history
4. **System Message**: Defines the chatbot's identity as "STERO SONIC" created by Navaneeth
5. **Initial Context**: Sets up initial conversation messages to establish the chatbot's persona

**Memory Structure:**
- Uses LangChain's `ConversationBufferMemory` with `return_messages=True`
- Stores both user and AI messages in chronological order
- Maintains full conversation context for context-aware responses

##### Method: `chat(message: str) -> str`

**Purpose**: Processes a user message and returns the chatbot's response.

**Parameters:**
- `message` (str): User's input message

**Process Flow:**
1. **Add User Message**: Stores the user's message in conversation memory
2. **Create Message Chain**: Constructs message list with:
   - System message (chatbot identity)
   - Full conversation history from memory
3. **Invoke LLM**: Calls the language model with the message chain
4. **Extract Response**: Gets the text content from the LLM response
5. **Store Response**: Adds AI response to memory for future context
6. **Return Response**: Returns the generated text or error message

**Error Handling:**
- Catches all exceptions and returns error message string
- Prevents application crashes from LLM API failures

##### Method: `reset()`

**Purpose**: Clears the conversation memory to start a fresh conversation.

**Process:**
- Calls `memory.clear()` to remove all stored messages
- Effectively resets the chatbot to initial state

#### Module-Level Functions

##### `get_chatbot() -> SteroSonicChatbot`

**Purpose**: Singleton pattern implementation to get or create a global chatbot instance.

**Behavior:**
- Maintains a global `chatbot` variable
- Creates new instance on first call
- Returns existing instance on subsequent calls
- Ensures only one chatbot instance exists throughout the application lifecycle

### Dependencies
- `os`: Environment variable access
- `langchain_google_genai.ChatGoogleGenerativeAI`: Google Gemini integration
- `langchain.schema.HumanMessage, SystemMessage`: Message type definitions
- `langchain.prompts.ChatPromptTemplate, MessagesPlaceholder`: Prompt templates
- `langchain.memory.ConversationBufferMemory`: Conversation memory management
- `typing.Optional`: Type hints

### Use Cases
1. **Simple Q&A**: Basic question-answering without tool usage
2. **General Conversation**: Casual chat interactions
3. **Text-Only Interactions**: When tool integration is not needed
4. **Fallback Mode**: Backup when tools-enabled chatbot is unavailable

### Limitations
- No tool/function calling capabilities
- Cannot perform actions (send emails, take screenshots, etc.)
- Limited to text-based responses only
- No reasoning step tracking

### Example Usage
```python
from core.chatbot import get_chatbot

chatbot = get_chatbot()
response = chatbot.chat("What is artificial intelligence?")
print(response)

# Reset conversation
chatbot.reset()
```

---

## chatbot_with_tools.py

### Overview
`chatbot_with_tools.py` implements an enhanced chatbot that integrates with LangChain tools, allowing the AI to automatically call functions based on user requests. This is the advanced version of the chatbot with tool execution capabilities.

### Key Components

#### Class: `SteroSonicChatbotWithTools`

An advanced chatbot that can use tools to perform actions beyond text generation.

##### Initialization (`__init__`)
```python
def __init__(self, api_key: Optional[str] = None)
```

**Initialization Process:**

1. **API Key Setup**: Same as basic chatbot - retrieves from parameter or environment

2. **LLM Configuration**:
   - Model: `gemini-2.5-flash`
   - Temperature: `0.7` (balanced creativity, lower than basic chatbot for more reliable tool usage)
   - Configured with API key

3. **Tools Integration**:
   - Calls `get_all_tools()` from `core.tools` module
   - Retrieves all available LangChain tools (email, WhatsApp, camera, etc.)

4. **Memory Setup**:
   - Creates `ConversationBufferMemory` with `chat_history` key
   - Initializes with system message about tool capabilities

5. **Agent Creation** (Two Approaches):
   
   **Primary Approach - ReAct Agent:**
   - Uses `create_react_agent` from LangChain
   - Implements ReAct (Reasoning + Acting) pattern
   - Custom prompt template with tool descriptions
   - Creates `AgentExecutor` with:
     - `verbose=True`: Detailed logging
     - `handle_parsing_errors=True`: Graceful error handling
     - `max_iterations=5`: Limits tool call iterations
     - `return_intermediate_steps=True`: Captures reasoning steps
   
   **Fallback Approach - Conversational Agent:**
   - Uses `initialize_agent` with `CHAT_CONVERSATIONAL_REACT_DESCRIPTION` type
   - Includes system message about tool usage guidelines
   - Same configuration parameters

6. **Error Handling**: Catches initialization errors and provides fallback options

##### Method: `chat(message: str, return_reasoning: bool = False) -> dict`

**Purpose**: Processes user messages with tool execution capabilities.

**Parameters:**
- `message` (str): User's input message
- `return_reasoning` (bool): If True, returns detailed reasoning steps

**Return Types:**
- If `return_reasoning=False`: Returns `str` (response text)
- If `return_reasoning=True`: Returns `dict` with:
  - `response`: Final response text
  - `reasoning`: List of reasoning step descriptions
  - `tools_used`: List of tools that were executed

**Process Flow:**

1. **Initialize Reasoning Tracking**:
   - Creates list to track reasoning steps
   - Adds initial "Received request" step

2. **Agent Execution** (Three Paths):

   **Path A - AgentExecutor (Primary):**
   - Invokes agent with input message
   - Extracts `intermediate_steps` from result
   - For each step:
     - Extracts tool name and input parameters
     - Formats tool execution details
     - Formats observation/results
     - Adds formatted steps to reasoning list
   - Extracts final output from result

   **Path B - Initialize Agent (Fallback):**
   - Uses `agent_executor.run()` method
   - Simpler execution path
   - Less detailed step tracking

   **Path C - Generic Invoke (Last Resort):**
   - Generic invoke with chat history
   - Minimal step tracking

3. **Reasoning Formatting**:
   - Emoji-based step indicators (💭, 🤔, 🔧, 📊, ✅, ❌)
   - Human-readable tool names and parameters
   - Truncated observations (100 chars) for readability

4. **Response Construction**:
   - If `return_reasoning=False`: Returns output string
   - If `return_reasoning=True`: Returns dictionary with response and reasoning

5. **Error Handling**:
   - Catches parsing errors (common with tool usage)
   - Provides user-friendly error messages
   - Returns error in appropriate format

**Reasoning Steps Format:**
```
💭 Received request: [user message]
🤔 Analyzing request and determining appropriate tools...
🤔 Step 1: Decided to use [tool_name]
🔧 Executing: [tool_name]([parameters])
📊 Result: [tool output]
✅ Task completed
```

##### Method: `reset()`

**Purpose**: Resets conversation memory and reinitializes system messages.

**Process:**
- Clears all memory
- Re-adds initial system and AI messages
- Restores chatbot identity and tool capabilities context

#### Module-Level Functions

##### `get_chatbot_with_tools() -> SteroSonicChatbotWithTools`

**Purpose**: Singleton pattern to get or create the tools-enabled chatbot instance.

**Behavior:**
- Maintains global `chatbot_with_tools` variable
- Creates instance on first call
- Returns existing instance on subsequent calls

### Dependencies
- `os`: Environment variable access
- `langchain_google_genai.ChatGoogleGenerativeAI`: LLM integration
- `langchain.agents`: Agent creation and execution
- `langchain.prompts.PromptTemplate`: Prompt templates
- `langchain.memory.ConversationBufferMemory`: Memory management
- `core.tools.get_all_tools`: Tool definitions

### Use Cases
1. **Action-Oriented Tasks**: When users want to perform actions (send emails, take screenshots)
2. **Multi-Step Operations**: Complex tasks requiring multiple tools
3. **Reasoning Visibility**: When users want to see how the AI decides to use tools
4. **Production Workflows**: Real-world task automation

### Advantages Over Basic Chatbot
- **Tool Execution**: Can perform actions, not just generate text
- **Reasoning Transparency**: Shows step-by-step decision making
- **Context-Aware Tool Selection**: Chooses appropriate tools based on user intent
- **Error Recovery**: Better error handling for tool failures

### Limitations
- More complex initialization
- Higher API costs (multiple LLM calls for tool selection)
- Requires all tool dependencies to be available
- Potential for infinite loops if tools fail (mitigated by max_iterations)

### Example Usage
```python
from core.chatbot_with_tools import get_chatbot_with_tools

chatbot = get_chatbot_with_tools()

# Simple usage
response = chatbot.chat("Send an email to john@example.com saying hello")
print(response)

# With reasoning
result = chatbot.chat("Take a screenshot and analyze it", return_reasoning=True)
print("Response:", result["response"])
print("Reasoning:", result["reasoning"])
print("Tools used:", result["tools_used"])
```

---

## tools.py

### Overview
`tools.py` is the central module that defines all LangChain tools available to the chatbot. It provides a comprehensive set of tools for email, messaging, system control, data management, and more. Each tool is wrapped as a LangChain `StructuredTool` with proper input schemas.

### Architecture

#### Tool Definition Pattern
Each tool follows this pattern:
1. **Input Schema**: Pydantic model defining required/optional parameters
2. **Tool Function**: Python function that executes the tool logic
3. **LangChain Tool**: Wrapped as `StructuredTool` with description and schema

#### Tool Categories

##### 1. Communication Tools

**`send_email`**
- **Purpose**: Send emails with optional attachments
- **Input Schema**: `SendEmailInput`
  - `to` (str, required): Recipient email address
  - `content` (str, required): Email message content
  - `attachment_path` (str, optional): Path to attachment file
- **Implementation**: Uses `EmailService.send_email()`
- **Returns**: Success/failure message string

**`send_whatsapp`**
- **Purpose**: Send WhatsApp messages via PyWhatKit
- **Input Schema**: `SendWhatsAppInput`
  - `name` (str, optional): Contact name from contacts file
  - `phone_number` (str, optional): Direct phone number with country code
  - `message` (str, required): Message content
  - `_require_name_or_number`: Validator ensures at least one identifier provided
- **Implementation**: Complex wrapper `send_whatsapp_tool()` handles various input formats:
  - Accepts `name`, `phone_number`, `to`, or `recipient` parameters
  - Parses JSON strings if provided
  - Handles nested dictionaries
  - Delegates to `WhatsAppService.send_message()`
- **Returns**: Success/failure message

##### 2. Media Capture Tools

**`capture_camera_image`**
- **Purpose**: Capture image from webcam/camera
- **Input**: None (no parameters)
- **Implementation**: Uses `CameraService.capture_image()`
- **Returns**: Path to saved image or error message

**`take_screenshot`**
- **Purpose**: Capture screenshot of current screen
- **Input**: None
- **Implementation**: Uses `ScreenshotService.take_screenshot()`
- **Returns**: Path to saved screenshot or error message

##### 3. System Information Tools

**`get_current_time`**
- **Purpose**: Get current system time
- **Input**: None
- **Implementation**: Uses `SystemService.get_time()`
- **Returns**: Formatted time string

**`list_running_apps`**
- **Purpose**: List currently running applications
- **Input Schema**: `ListRunningAppsInput`
  - `include_system` (bool, optional, default=False): Include system processes
- **Implementation**: Uses `SystemService.get_running_apps()`
- **Returns**: Formatted list of apps with PID, name, and window title

##### 4. Search Tools

**`search_wikipedia`**
- **Purpose**: Search Wikipedia for information
- **Input Schema**: `SearchWikipediaInput`
  - `query` (str, required): Search query
- **Implementation**: Uses `SystemService.search_wikipedia()`
- **Returns**: Wikipedia summary or error message

**`search_youtube`**
- **Purpose**: Open YouTube search in browser
- **Input Schema**: `SearchYouTubeInput`
  - `query` (str, required): Search query
- **Implementation**: Uses `SystemService.open_youtube()`
- **Returns**: Success message

**`search_google`**
- **Purpose**: Open Google search in browser
- **Input Schema**: `SearchGoogleInput`
  - `query` (str, required): Search query
- **Implementation**: Uses `SystemService.open_google()`
- **Returns**: Success message

**`open_stackoverflow`**
- **Purpose**: Open StackOverflow website
- **Input**: None
- **Implementation**: Uses `SystemService.open_stackoverflow()`
- **Returns**: Success message

##### 5. Application Control Tools

**`open_app`**
- **Purpose**: Open application via Windows search
- **Input Schema**: `OpenAppInput`
  - `app_name` (str, required): Name of application
- **Implementation**: Uses `SystemService.open_windows_search()`
- **Returns**: Success message or error

**`close_processes`**
- **Purpose**: Close processes by executable name
- **Input Schema**: `CloseProcessesInput`
  - `exe_list` (List[str], required): List of executable names (e.g., ['chrome.exe'])
- **Implementation**: Uses `SystemService.close_processes()`
- **Returns**: List of closed processes or error

**`close_apps_by_names`**
- **Purpose**: Close applications by friendly names
- **Input Schema**: `CloseAppsByNamesInput`
  - `names` (List[str], optional): List of app names
  - `app_names` (List[str], optional): Alias for names
  - `_coalesce_names`: Validator merges names/app_names
- **Implementation**: Complex wrapper `close_apps_by_names_tool()`:
  - Accepts multiple input formats (dict, JSON string, list)
  - Handles parameter variations
  - Delegates to `SystemService.close_apps_by_names()`
- **Returns**: List of closed apps or error

**`switch_windows`**
- **Purpose**: Switch between open windows (Alt+Tab)
- **Input**: None
- **Implementation**: Uses `SystemService.switch_windows()`
- **Returns**: Success message

##### 6. Media Playback Tools

**`play_music`**
- **Purpose**: Play music from music directory via Spotify
- **Input**: None
- **Implementation**: Uses `SystemService.play_music()`
- **Returns**: Song name or error
- **Note**: Calling multiple times may toggle playback

##### 7. Data Management Tools

**`store_data`**
- **Purpose**: Store key-value data for later retrieval
- **Input Schema**: `StoreDataInput`
  - `key` (str, required): Storage key
  - `value` (str, required): Data to store
- **Implementation**: Uses `DataService.store_data()`
- **Returns**: Success message with key

**`retrieve_data`**
- **Purpose**: Retrieve stored data by key
- **Input Schema**: `RetrieveDataInput`
  - `key` (str, required): Storage key
- **Implementation**: Uses `DataService.retrieve_data()`
- **Returns**: Retrieved value or error

**`save_note`**
- **Purpose**: Save text as note file
- **Input Schema**: `SaveNoteInput`
  - `text` (str, required): Note content
  - `file_path` (str, optional): Custom file path
- **Implementation**: Uses `DataService.save_note()`
- **Returns**: File path or error

##### 8. Visual Search Tools

**`upload_image_to_lens`**
- **Purpose**: Upload image to Google Lens for visual search
- **Input Schema**: `UploadImageToLensInput`
  - `image_path` (str, required): Path to image file
- **Implementation**: Uses `LensService.upload_image_to_lens()`
- **Returns**: Success message or error

**`scan_screen_with_lens`**
- **Purpose**: Take screenshot and upload to Google Lens
- **Input**: None
- **Implementation**:
  1. Takes screenshot via `ScreenshotService`
  2. Uploads screenshot to Lens via `LensService`
- **Returns**: Combined success message or error

### Input Schema Classes

All input schemas inherit from `pydantic.BaseModel` with:
- **Field Descriptions**: Help LLM understand parameter purpose
- **Type Validation**: Automatic type checking
- **Optional Fields**: Clearly marked with `Optional` and defaults
- **Custom Validators**: Some schemas use `@root_validator` for complex validation

### Tool Wrapper Functions

Several tools have wrapper functions to handle agent input variations:
- `send_whatsapp_tool`: Handles multiple recipient formats
- `close_apps_by_names_tool`: Handles various list input formats

These wrappers:
- Parse JSON strings if provided
- Extract parameters from nested structures
- Handle parameter name variations
- Provide fallback parsing strategies

### Tool Creation Function

#### `get_all_tools() -> List[Tool]`

**Purpose**: Creates and returns list of all available LangChain tools.

**Process:**

1. **Structured Tool Creation** (Primary):
   - Attempts to create `StructuredTool` instances
   - Each tool includes:
     - Function reference
     - Tool name
     - Detailed description for LLM
     - Input schema (Pydantic model)
   - Tools are listed in specific order

2. **Fallback Tool Creation**:
   - If `StructuredTool` fails, uses regular `Tool` class
   - Creates lambda wrappers for parameter parsing
   - Uses `_parse_args()` helper to extract parameters
   - Less type-safe but more compatible

3. **Error Handling**:
   - Catches exceptions during tool creation
   - Prints warning and falls back to regular tools
   - Ensures tool list is always returned

**Tool Descriptions**:
Each tool description is carefully crafted to:
- Explain when to use the tool
- Provide usage examples
- Clarify parameter requirements
- Guide LLM decision-making

### Service Initialization

At module level, all services are imported and initialized:
```python
email_service = EmailService()
whatsapp_service = WhatsAppService()
camera_service = CameraService()
screenshot_service = ScreenshotService()
system_service = SystemService()
data_service = DataService()
lens_service = LensService()
```

These are singleton instances used by all tool functions.

### Dependencies
- `langchain.tools.Tool, StructuredTool`: Tool definitions
- `pydantic.BaseModel, Field, root_validator`: Input validation
- `typing.Optional, List`: Type hints
- `json`: JSON parsing for flexible inputs
- `sys, pathlib.Path`: Path manipulation
- All service modules from `services` package

### Tool Usage Patterns

**Simple Tools** (no parameters):
```python
result = take_screenshot()
```

**Parameterized Tools**:
```python
result = send_email(to="user@example.com", content="Hello", attachment_path=None)
```

**List-Based Tools**:
```python
result = close_apps_by_names(names=["chrome", "spotify"])
```

### Error Handling Strategy

All tools follow consistent error handling:
1. Call service method
2. Check `result.get("success")`
3. Return user-friendly success message
4. Return error message with details if failed

### Example Tool Definition

```python
# Input Schema
class SendEmailInput(BaseModel):
    to: str = Field(description="Email address of the recipient")
    content: str = Field(description="Email content/message")
    attachment_path: Optional[str] = Field(None, description="Path to attachment file")

# Tool Function
def send_email(to: str, content: str, attachment_path: Optional[str] = None) -> str:
    result = email_service.send_email(to, content, attachment_path)
    if result.get("success"):
        return f"Email sent successfully to {to}"
    return f"Failed to send email: {result.get('error', 'Unknown error')}"

# LangChain Tool
StructuredTool.from_function(
    func=send_email,
    name="send_email",
    description="Send an email to a recipient with optional attachment...",
    args_schema=SendEmailInput
)
```

---

## data_analyzer.py

### Overview
`data_analyzer.py` provides a specialized class for analyzing pandas DataFrames using Google's Gemini AI. It generates and executes pandas code based on natural language tasks, making data analysis accessible through conversational interface.

### Key Components

#### Class: `DataFrameAnalyzer`

A specialized analyzer that uses LLM to generate pandas code for data analysis tasks.

##### Initialization (`__init__`)
```python
def __init__(self, api_key: Optional[str] = None)
```

**Parameters:**
- `api_key` (Optional[str]): Google Gemini API key (reads from environment if not provided)

**Initialization Process:**
1. **API Key Setup**: Retrieves from parameter or `GEMINI_API_KEY` environment variable
2. **LLM Configuration**:
   - Model: `gemini-1.5-flash` (different from chatbot models)
   - Temperature: `1.0` (maximum creativity for code generation)
   - Configured with API key

**Why Different Model?**
- `gemini-1.5-flash` may have better code generation capabilities
- Higher temperature encourages creative code solutions

##### Method: `analyze(dataframe_path: str, task: str) -> dict`

**Purpose**: Analyzes a DataFrame based on natural language task description.

**Parameters:**
- `dataframe_path` (str): Path to CSV file containing the DataFrame
- `task` (str): Natural language description of analysis task

**Return Dictionary:**
```python
{
    "code": str,           # Generated pandas code
    "success": bool,       # Whether execution succeeded
    "columns": List[str],  # DataFrame column names
    "shape": Tuple[int],   # DataFrame dimensions (rows, cols)
    "error": str           # Error message if failed (optional)
}
```

**Process Flow:**

1. **DataFrame Loading**:
   - Uses `pandas.read_csv()` to load CSV file
   - Extracts column names for prompt context
   - Stores DataFrame shape information

2. **Prompt Construction**:
   - Creates detailed prompt with:
     - Context about DataFrame structure (columns)
     - User's task description
     - Instructions for code generation:
       - Use pandas operations
       - Use NumPy and Matplotlib for visualizations
       - Clean, well-commented code
       - Print DataFrames if result is a DataFrame
     - Instruction to provide only code (no explanations)

3. **Code Generation**:
   - Invokes LLM with constructed prompt
   - Extracts response content
   - Calls `_extract_code()` to clean the response

4. **Code Execution**:
   - Creates execution context with:
     - `df`: The loaded DataFrame
     - `pd`: pandas module
   - Uses `exec()` to execute generated code
   - Runs in isolated context (limited builtins)

5. **Result Compilation**:
   - Returns dictionary with:
     - Generated code (cleaned)
     - Success status
     - DataFrame metadata (columns, shape)
     - Error message if execution failed

**Error Handling:**
- Catches exceptions during execution
- Preserves generated code even if execution fails
- Returns detailed error messages
- Prevents application crashes

**Security Considerations:**
- Uses `exec()` which has security implications
- Limited builtins context (could be enhanced)
- Code execution is isolated to DataFrame operations
- User should trust the LLM-generated code

##### Method: `_extract_code(text: str) -> str`

**Purpose**: Extracts Python code from LLM response, removing markdown formatting.

**Process:**
1. **Markdown Removal**: Uses regex to remove:
   - ```python code blocks
   - ``` closing markers
   - Leading/trailing whitespace
2. **Returns**: Clean Python code string

**Regex Patterns:**
- `r'```python\n?'`: Removes Python code block markers
- `r'```\n?'`: Removes closing code block markers

### Dependencies
- `os`: Environment variable access
- `pandas`: DataFrame operations
- `langchain_google_genai.ChatGoogleGenerativeAI`: LLM integration
- `typing.Optional`: Type hints
- `re`: Regular expressions for code extraction

### Use Cases
1. **Data Exploration**: "Show me the first 5 rows"
2. **Statistical Analysis**: "Calculate mean and standard deviation of column X"
3. **Data Filtering**: "Show all rows where age > 30"
4. **Visualization**: "Create a bar chart of sales by region"
5. **Data Transformation**: "Add a new column that is the sum of columns A and B"
6. **Aggregation**: "Group by category and calculate total sales"

### Limitations
1. **Security**: Code execution via `exec()` is risky
2. **Error Recovery**: LLM may generate incorrect code
3. **Context Size**: Large DataFrames may exceed token limits
4. **No State Persistence**: Each analysis is independent
5. **Limited Debugging**: Errors may be unclear
6. **CSV Only**: Only supports CSV files, not other formats

### Advantages
1. **Natural Language Interface**: No need to write pandas code
2. **Flexible**: Can handle various analysis tasks
3. **Educational**: Shows generated code for learning
4. **Quick Prototyping**: Fast iteration on data analysis

### Example Usage
```python
from core.data_analyzer import DataFrameAnalyzer

analyzer = DataFrameAnalyzer()

# Analyze data
result = analyzer.analyze(
    dataframe_path="data/sales.csv",
    task="Show me the top 10 products by sales and create a bar chart"
)

if result["success"]:
    print("Generated code:")
    print(result["code"])
    print(f"\nDataFrame has {result['shape'][0]} rows and {result['shape'][1]} columns")
else:
    print(f"Error: {result['error']}")
```

### Prompt Engineering

The prompt is carefully constructed to:
- Provide context about DataFrame structure
- Clearly specify output format (code only)
- Encourage best practices (clean, commented code)
- Include visualization instructions
- Ensure DataFrame printing when appropriate

---

## intent_parser.py

### Overview
`intent_parser.py` provides natural language intent recognition for user commands. It uses spaCy NLP library for advanced parsing, with a keyword-based fallback system.

### Key Components

#### Class: `IntentParser`

A parser that recognizes user intents from natural language commands.

##### Initialization (`__init__`)
```python
def __init__(self)
```

**Initialization Process:**
1. **spaCy Model Loading**:
   - Attempts to load `en_core_web_sm` model
   - If model not found, prints warning and sets `nlp = None`
   - Falls back to simple keyword matching

2. **Error Handling**:
   - Gracefully handles missing spaCy model
   - Provides installation instructions in warning
   - Continues operation with fallback method

**spaCy Model:**
- `en_core_web_sm`: Small English model with:
  - Part-of-speech tagging
  - Named entity recognition
  - Dependency parsing
  - Tokenization

##### Method: `parse_intent(command: str) -> Optional[str]`

**Purpose**: Analyzes user command and returns recognized intent.

**Parameters:**
- `command` (str): User's command/query

**Returns:**
- `Optional[str]`: Intent name if recognized, `None` otherwise

**Process Flow:**

**Path A - spaCy Processing (if available):**
1. **Lowercase Conversion**: Converts command to lowercase
2. **NLP Processing**: Creates spaCy document object
3. **Pattern Matching**: Checks against predefined intent patterns
4. **Pattern Structure**: Each pattern is a list of tuples:
   - `(keyword, POS_tag)`: Word and its part-of-speech
   - Example: `[("search", "VERB"), ("wikipedia", "PROPN")]`
5. **Validation**: Checks if:
   - All keywords exist in command
   - Keywords have matching POS tags
6. **Intent Return**: Returns first matching intent, or `None`

**Path B - Simple Keyword Matching (fallback):**
1. **Lowercase Conversion**: Converts command to lowercase
2. **Keyword Matching**: Checks against keyword lists
3. **Intent Mapping**: Each intent has multiple keyword variations
4. **First Match**: Returns first intent with matching keywords

**Supported Intents:**

| Intent | Keywords/Variations |
|--------|---------------------|
| `wikipedia` | "wikipedia", "wiki" |
| `youtube` | "youtube", "yt" |
| `note down` | "note down", "note" |
| `stackoverflow` | "stackoverflow", "stack overflow" |
| `music` | "play music", "music" |
| `time` | "time", "what time" |
| `mirror` | "mirror", "camera" |
| `store` | "store data", "store" |
| `retrieve` | "retrieve", "get data" |
| `email` | "send email", "email" |
| `selfie` | "selfie", "take selfie" |
| `google` | "google", "search google" |
| `close windows` | "close windows", "close" |
| `research` | "research", "help research" |
| `who are you` | "who are you" |
| `send message` | "send message", "message" |
| `activate chatbot` | "activate chatbot", "chatbot" |
| `switch windows` | "switch windows", "switch" |
| `open lens` | "open lens", "lens" |
| `scan the screen` | "scan screen", "scan" |
| `open` | "open" |
| `analyse data` | "analyse data", "analyze data", "data" |

##### Method: `_simple_intent_mapping(command: str) -> Optional[str]`

**Purpose**: Fallback keyword-based intent recognition.

**Process:**
1. **Lowercase**: Converts command to lowercase
2. **Keyword Dictionary**: Maps intents to keyword lists
3. **Iteration**: Checks each intent's keywords
4. **Substring Match**: Uses `in` operator for keyword matching
5. **First Match**: Returns first matching intent

**Limitations:**
- Less precise than POS tagging
- May match unintended keywords
- No grammatical understanding

### Module-Level Instance

```python
intent_parser = IntentParser()
```

**Purpose**: Global singleton instance for easy access throughout application.

### Dependencies
- `spacy`: Natural language processing library
- `typing.Optional, Dict, Callable`: Type hints

### Use Cases
1. **Command Routing**: Route user commands to appropriate handlers
2. **Voice Interface**: Recognize intents from voice commands
3. **Quick Command Detection**: Fast intent recognition for common tasks
4. **Pre-processing**: Intent recognition before LLM processing

### Limitations
1. **Limited Intents**: Fixed set of predefined intents
2. **No Context**: Doesn't consider conversation context
3. **Single Intent**: Returns only one intent (no multi-intent)
4. **Keyword Conflicts**: Overlapping keywords may cause issues
5. **No Parameters**: Doesn't extract command parameters

### Advantages
1. **Fast**: Quick intent recognition
2. **Lightweight**: Minimal dependencies (with fallback)
3. **Deterministic**: Consistent results
4. **Offline**: Works without API calls
5. **Fallback**: Works even without spaCy

### Example Usage
```python
from core.intent_parser import intent_parser

# Parse intent
intent = intent_parser.parse_intent("Search Wikipedia for AI")
print(intent)  # Output: "wikipedia"

intent = intent_parser.parse_intent("What time is it?")
print(intent)  # Output: "time"

intent = intent_parser.parse_intent("Take a selfie")
print(intent)  # Output: "selfie"

# Unknown intent
intent = intent_parser.parse_intent("Hello, how are you?")
print(intent)  # Output: None
```

### Pattern Matching Example

**spaCy Pattern:**
```python
"wikipedia": [("search", "VERB"), ("wikipedia", "PROPN")]
```

**Command**: "Search Wikipedia for AI"
- Token: "search" → POS: VERB ✓
- Token: "wikipedia" → POS: PROPN ✓
- **Result**: Intent "wikipedia" recognized

**Command**: "I want to search Wikipedia"
- Token: "search" → POS: VERB ✓
- Token: "wikipedia" → POS: PROPN ✓
- **Result**: Intent "wikipedia" recognized

### Integration with Chatbot

The intent parser can be used to:
1. Pre-process user commands before LLM
2. Route to specific handlers
3. Provide hints to LLM about user intent
4. Enable voice command recognition

---

## speech.py

### Overview
`speech.py` provides text-to-speech (TTS) functionality using the `pyttsx3` library. It offers both synchronous and asynchronous speech synthesis with configurable voice settings.

### Key Components

#### Class: `TextToSpeech`

A TTS engine wrapper that provides speech synthesis capabilities.

##### Initialization (`__init__`)
```python
def __init__(self)
```

**Initialization Process:**

1. **Engine Initialization**:
   - Creates `pyttsx3` engine instance
   - Platform-specific initialization (Windows SAPI5, macOS NSSpeechSynthesizer, Linux espeak)

2. **Voice Selection**:
   - Retrieves available voices: `self.engine.getProperty('voices')`
   - Sets female voice if available (usually index 1)
   - Falls back to default voice if only one available
   
   **Voice Selection Logic:**
   ```python
   if len(self.voices) > 1:
       self.engine.setProperty('voice', self.voices[1].id)
   ```

3. **Speech Configuration**:
   - **Rate**: `150` words per minute (moderate speed)
   - **Volume**: `1.0` (maximum volume)

**Platform Support:**
- **Windows**: Uses SAPI5 (built-in Windows voices)
- **macOS**: Uses NSSpeechSynthesizer
- **Linux**: Uses espeak (may need installation)

##### Method: `speak(text: str) -> threading.Thread`

**Purpose**: Speaks text asynchronously in a separate thread.

**Parameters:**
- `text` (str): Text to be spoken

**Returns:**
- `threading.Thread`: Thread object for the speech operation

**Process:**
1. **Thread Creation**: Defines inner function `_speak()` that:
   - Calls `engine.say(text)` to queue speech
   - Calls `engine.runAndWait()` to execute speech
2. **Thread Start**: Creates and starts thread with `_speak` target
3. **Non-Blocking**: Returns immediately, speech continues in background

**Use Cases:**
- UI applications where blocking is undesirable
- Concurrent operations during speech
- Responsive user interfaces

**Thread Management:**
- Caller can use returned thread to:
  - Wait for completion: `thread.join()`
  - Check if alive: `thread.is_alive()`
  - But typically ignored for fire-and-forget usage

##### Method: `speak_sync(text: str)`

**Purpose**: Speaks text synchronously (blocking operation).

**Parameters:**
- `text` (str): Text to be spoken

**Returns:**
- `None`

**Process:**
1. **Queue Speech**: Calls `engine.say(text)`
2. **Wait**: Calls `engine.runAndWait()` to block until speech completes

**Use Cases:**
- Scripts where blocking is acceptable
- Sequential operations where speech must complete before next step
- Simple command-line interfaces

**Blocking Behavior:**
- Function returns only after speech finishes
- No other operations can proceed during speech
- May cause UI freezing if used in GUI thread

### Module-Level Instance

```python
tts = TextToSpeech()
```

**Purpose**: Global singleton instance for easy access throughout application.

### Dependencies
- `pyttsx3`: Cross-platform text-to-speech library
- `threading`: Thread management for async speech

### Voice Configuration

**Available Properties:**
- `rate`: Speech rate (words per minute)
- `volume`: Volume level (0.0 to 1.0)
- `voice`: Voice selection (voice ID)

**Current Settings:**
- Rate: 150 WPM (moderate)
- Volume: 1.0 (maximum)
- Voice: Female voice (if available)

**Customization Example:**
```python
tts = TextToSpeech()
tts.engine.setProperty('rate', 200)  # Faster
tts.engine.setProperty('volume', 0.8)  # Quieter
```

### Use Cases
1. **Voice Assistant**: Spoken responses to user queries
2. **Accessibility**: Screen reader functionality
3. **Notifications**: Audio alerts and announcements
4. **Interactive Applications**: Voice feedback for user actions
5. **Multimodal Interfaces**: Combined text and speech output

### Limitations
1. **Platform Dependency**: Requires platform-specific TTS engines
2. **Voice Quality**: Quality varies by platform and voice
3. **No SSML**: Limited formatting compared to cloud TTS services
4. **Offline Only**: No internet connection required (pro/con)
5. **Limited Languages**: Depends on installed voices
6. **No Emotion**: Robotic, emotionless speech

### Advantages
1. **Offline**: Works without internet connection
2. **Fast**: Immediate speech synthesis
3. **Free**: No API costs
4. **Lightweight**: Minimal dependencies
5. **Configurable**: Adjustable rate, volume, voice

### Example Usage

**Async Speech (Non-blocking):**
```python
from core.speech import tts

# Speak without blocking
thread = tts.speak("Hello, I am Stero Sonic Assistant")
# Continue with other operations
print("This prints immediately")
# Optionally wait for speech to finish
thread.join()
```

**Sync Speech (Blocking):**
```python
from core.speech import tts

# Speak and wait
tts.speak_sync("Processing your request")
print("This prints after speech completes")
```

**Integration with Chatbot:**
```python
from core.chatbot_with_tools import get_chatbot_with_tools
from core.speech import tts

chatbot = get_chatbot_with_tools()
response = chatbot.chat("What is the weather?")
tts.speak(response)  # Speak response asynchronously
```

### Thread Safety

**Considerations:**
- Multiple `speak()` calls create multiple threads
- Threads may overlap (speech may interrupt previous speech)
- For sequential speech, use `speak_sync()` or wait for threads

**Best Practices:**
- Use `speak()` for non-critical, non-blocking speech
- Use `speak_sync()` when speech must complete before continuing
- Consider queueing mechanism for multiple speech requests

### Platform-Specific Notes

**Windows:**
- Uses built-in SAPI5 voices
- Usually has multiple voices (male/female)
- Good quality, natural-sounding voices

**macOS:**
- Uses system voices
- High-quality voices available
- Multiple language options

**Linux:**
- Requires espeak installation: `sudo apt-get install espeak`
- May need additional packages for better voices
- Quality can vary

---

## Summary

The `core` module provides the foundational intelligence and functionality for the Stero Sonic Assistant:

1. **chatbot.py**: Basic conversational AI without tools
2. **chatbot_with_tools.py**: Advanced AI with tool execution capabilities
3. **tools.py**: Comprehensive tool definitions for system interaction
4. **data_analyzer.py**: Specialized DataFrame analysis using LLM
5. **intent_parser.py**: Natural language intent recognition
6. **speech.py**: Text-to-speech functionality

Together, these modules create a powerful AI assistant capable of:
- Understanding natural language
- Executing system commands
- Analyzing data
- Providing voice feedback
- Maintaining conversation context

---

## Module Dependencies Graph

```
chatbot_with_tools.py
    ├── tools.py
    │   ├── services/* (all services)
    │   └── langchain tools
    └── chatbot.py (fallback)

data_analyzer.py
    └── (standalone, uses LLM directly)

intent_parser.py
    └── (standalone, optional spaCy)

speech.py
    └── (standalone, pyttsx3)
```

---

## Future Enhancements

Potential improvements for each module:

1. **chatbot.py**: Add streaming responses, better error recovery
2. **chatbot_with_tools.py**: Add tool result caching, better reasoning visualization
3. **tools.py**: Add more tools, better parameter validation, tool versioning
4. **data_analyzer.py**: Support more file formats, add code validation, better error messages
5. **intent_parser.py**: Add parameter extraction, context awareness, more intents
6. **speech.py**: Add SSML support, emotion/intonation, voice cloning

---

*Documentation generated for Stero Sonic Assistant Core Modules*

