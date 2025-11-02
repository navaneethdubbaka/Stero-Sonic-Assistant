# Langchain Tools Integration

## Overview

The Stereo Sonic Assistant now uses Langchain tools to enable the LLM to automatically understand and call various services based on user requests. This allows the assistant to be more intelligent and proactive in completing tasks.

## Architecture

### Tools System
- **Location**: `backend/core/tools.py`
- **Purpose**: Defines all available Langchain tools that wrap service functions
- **Count**: 19 tools covering all major services

### Enhanced Chatbot
- **Location**: `backend/core/chatbot_with_tools.py`
- **Purpose**: Chatbot with Langchain agent executor that can automatically use tools
- **Agent Type**: CHAT_CONVERSATIONAL_REACT_DESCRIPTION

### Original Chatbot
- **Location**: `backend/core/chatbot.py`
- **Purpose**: Basic chatbot without tools (fallback)

## Available Tools

### Communication Tools
1. **send_email** - Send email with optional attachment
2. **send_whatsapp** - Send WhatsApp message to contact

### Media Tools
3. **capture_camera_image** - Capture image from camera
4. **take_screenshot** - Take screenshot of screen
5. **upload_image_to_lens** - Upload image to Google Lens
6. **scan_screen_with_lens** - Take screenshot and upload to Google Lens

### System Tools
7. **get_current_time** - Get current time
8. **open_app** - Open Windows application
9. **switch_windows** - Switch between windows
10. **close_processes** - Close specific processes

### Search Tools
11. **search_wikipedia** - Search Wikipedia
12. **search_youtube** - Search YouTube
13. **search_google** - Search Google
14. **open_stackoverflow** - Open StackOverflow

### Data Tools
15. **store_data** - Store key-value data
16. **retrieve_data** - Retrieve stored data
17. **save_note** - Save note to file

### Media Control
18. **play_music** - Play music from directory

## How It Works

### Tool Calling Flow

1. **User Request**: User asks the assistant to perform a task
   ```
   "Send an email to john@gmail.com saying hello"
   ```

2. **LLM Analysis**: The LLM (Gemini) analyzes the request and identifies:
   - Intent: Send email
   - Tool needed: `send_email`
   - Parameters: `to="john@gmail.com"`, `content="hello"`

3. **Tool Execution**: The agent executor calls the `send_email` tool with the extracted parameters

4. **Result**: Tool returns result, LLM formats a response for the user

### Example Interactions

#### Example 1: Email
```
User: "Send an email to navaneeth@gmail.com with the message 'Meeting at 3pm'"
Agent: Uses send_email tool
Result: "Email sent successfully to navaneeth@gmail.com"
```

#### Example 2: Search
```
User: "Search Wikipedia for Python programming"
Agent: Uses search_wikipedia tool with query="Python programming"
Result: "According to Wikipedia, Python is..."
```

#### Example 3: Multi-step
```
User: "Take a screenshot and then search it with Google Lens"
Agent: 
  1. Uses take_screenshot tool
  2. Uses upload_image_to_lens tool with screenshot path
Result: "Screenshot taken and uploaded to Google Lens"
```

## API Usage

### Enable Tools (Default)
```python
POST /api/chatbot/chat
{
    "message": "Send an email to user@example.com saying hello",
    "use_tools": true  # Optional, defaults to true
}
```

### Disable Tools
```python
POST /api/chatbot/chat
{
    "message": "What is Python?",
    "use_tools": false
}
```

## Configuration

### Environment Variables
- `GEMINI_API_KEY` - Required for LLM functionality
- `EMAIL_ADDRESS` - For email tools
- `EMAIL_PASSWORD` - For email tools
- `CONTACTS_FILE_PATH` - For WhatsApp tools

## Tool Descriptions

Each tool has a detailed description that helps the LLM understand:
- When to use the tool
- What parameters are needed
- What the tool does

Example:
```python
StructuredTool.from_function(
    func=send_email,
    name="send_email",
    description="Send an email to a recipient with optional attachment. Use this when user wants to send an email.",
    args_schema=SendEmailInput
)
```

## Error Handling

The agent executor includes:
- `handle_parsing_errors=True` - Gracefully handles tool parsing errors
- `max_iterations=5` - Limits tool call iterations
- Fallback to regular tools if StructuredTool fails

## Benefits

1. **Intelligent Task Understanding**: LLM can understand natural language and determine which tools to use
2. **Automatic Tool Selection**: No need for manual intent mapping
3. **Context Awareness**: LLM can use multiple tools in sequence for complex tasks
4. **Extensibility**: Easy to add new tools by adding them to `tools.py`

## Adding New Tools

1. Create a service function in `backend/services/`
2. Create a wrapper function in `backend/core/tools.py`
3. Add tool definition to `get_all_tools()`
4. Update tool descriptions for LLM understanding

Example:
```python
def new_tool_function(param: str) -> str:
    """Tool function that calls a service"""
    result = service.method(param)
    return result.get("message", "Task completed")

# In get_all_tools():
StructuredTool.from_function(
    func=new_tool_function,
    name="new_tool",
    description="Clear description of when to use this tool",
    args_schema=NewToolInput  # Or None if no structured input
)
```

## Troubleshooting

### Tools Not Working
- Check that `langchain` and `langchain-google-genai` are installed
- Verify `GEMINI_API_KEY` is set
- Check service dependencies (email credentials, etc.)

### LLM Not Using Tools
- Ensure tools are properly described in `get_all_tools()`
- Check tool descriptions are clear about when to use them
- Verify agent executor is initialized correctly

### Import Errors
- Ensure all service modules are importable
- Check path configurations in `tools.py`

## Performance Considerations

- Tool calls add latency (LLM + tool execution)
- Multiple tool calls in sequence increase response time
- Consider caching for frequently used tools
- Monitor max_iterations to prevent infinite loops

