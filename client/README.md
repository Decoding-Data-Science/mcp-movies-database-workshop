# MCP Movies Database Client

## Overview

The MCP Movies Database Client is a **Streamlit-based chatbot** that demonstrates how to build interactive AI applications using the **Model Context Protocol (MCP)**. This client connects to the MCP Movies Database Server to provide natural language querying capabilities for a comprehensive movies database.

## Architecture

```
┌─────────────────────────────────────────┐
│         User Interface                  │
│       (Streamlit Web App)               │
└─────────────┬───────────────────────────┘
              │ User Queries
┌─────────────▼───────────────────────────┐
│         MCP Client                      │
│      (movies_chatbot.py)                │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │        MCPAgent                 │    │
│  │   ┌─────────────────────────┐   │    │
│  │   │     ChatOpenAI          │   │    │
│  │   │     (GPT-4o)            │   │    │
│  │   └─────────────────────────┘   │    │
│  │   ┌─────────────────────────┐   │    │
│  │   │     MCPClient           │   │    │
│  │   │  (mcp_config.json)      │   │    │
│  │   └─────────────────────────┘   │    │
│  └─────────────────────────────────┘    │
└─────────────┬───────────────────────────┘
              │ MCP Protocol (HTTP)
┌─────────────▼───────────────────────────┐
│          MCP Server                     │
│      (movies_mcp_server.py)             │
└─────────────────────────────────────────┘
```

## Features

### 🤖 AI-Powered Movie Assistant
- **Natural Language Queries**: Ask questions in plain English about movies
- **Intelligent Tool Selection**: Automatically chooses the right database operations
- **Contextual Responses**: Provides detailed, formatted answers about movies

### 💬 Interactive Chat Interface
- **Streamlit Web UI**: Modern, responsive chat interface
- **Chat History**: Maintains conversation context throughout the session
- **Real-time Responses**: Live streaming of AI responses
- **Error Handling**: Graceful error display and recovery

### 🔍 Comprehensive Movie Queries
- **Search by Title**: "Tell me about The Matrix"
- **Genre Exploration**: "Find action movies with high ratings"
- **Year-based Queries**: "What movies were released in 2023?"
- **Director/Actor Searches**: "Show me movies by Christopher Nolan"
- **Rating Analysis**: "What are the top-rated sci-fi movies?"

### ⚙️ MCP Integration
- **Protocol Compliance**: Full MCP client implementation using mcp-use
- **Tool Discovery**: Automatically discovers available server tools
- **Error Resilience**: Handles server connection issues gracefully
- **Configurable**: Easy server configuration via JSON config

## Installation

### Prerequisites
- Python 3.8+
- OpenAI API key
- Running MCP Movies Database Server
- Required Python packages

### Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables** (create `.env` file):
   ```bash
   # OpenAI API Configuration
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Optional: Database paths (if running utilities)
   DB_FILE_PATH=./data/movies.db
   CSV_FILE_PATH=./data/mymoviedb.csv
   ```

3. **Configure MCP Server connection** (`config/mcp_config.json`):
   ```json
   {
     "mcpServers": {
       "movies-db": {
           "url": "http://0.0.0.0:4567/mcp",
           "transport": "streamable-http"
       }
     }
   }
   ```

4. **Start the MCP Server** (in another terminal):
   ```bash
   cd server/
   python movies_mcp_server.py
   ```

## Usage

### Running the Streamlit App

```bash
# Navigate to the client directory
cd client/

# Start the Streamlit application
streamlit run movies_chatbot.py
```

The app will open in your browser at `http://localhost:8501`.

### Running as a CLI Script

```bash
# Run the standalone version (for testing)
python movies_chatbot.py
```

This will execute a single query: "Tell me the years when Lord of the Rings was released."

## Example Interactions

### Basic Movie Search
```
User: Tell me about The Matrix
Assistant: The Matrix is a groundbreaking 1999 science fiction film...
[Shows details like rating, release date, overview, etc.]
```

### Genre-based Queries
```
User: Find action movies with high ratings
Assistant: Here are some highly-rated action movies:
1. The Dark Knight (2008) - Rating: 9.0
2. Terminator 2 (1991) - Rating: 8.5
...
```

### Year-based Searches
```
User: What movies were released in 2023?
Assistant: Here are movies released in 2023:
- Guardians of the Galaxy Vol. 3
- Spider-Man: Across the Spider-Verse
...
```

### Complex Queries
```
User: Show me sci-fi movies from the 2000s with ratings above 8.0
Assistant: Here are highly-rated sci-fi movies from the 2000s:
[Filtered results with ratings, years, and descriptions]
```

## Code Structure

### Main Components

```
client/
├── __init__.py
├── movies_chatbot.py       # Main application
├── mcp_config.json        # MCP server configuration
└── README.md              # This file
```

### Key Functions

#### `init_mcp_agent()`
Initializes the MCP agent with:
- **MCPClient**: Configured from JSON config file
- **ChatOpenAI**: GPT-4o language model
- **MCPAgent**: Combines client and LLM with max 30 steps

#### `process_query(agent, query)`
Processes user queries through the MCP agent:
- Sends query to the agent
- Handles tool selection and execution
- Returns formatted response

#### `streamlit_app()`
Main Streamlit application:
- Sets up the web interface
- Manages chat history
- Handles user input and responses
- Provides sidebar information

### Dependencies

```python
# Core MCP and AI libraries
from mcp_use import MCPAgent, MCPClient
from langchain_openai import ChatOpenAI

# Web interface
import streamlit as st

# Utilities
import asyncio
from dotenv import load_dotenv
```

## Configuration

### MCP Server Configuration

The client connects to the MCP server using configuration in `config/mcp_config.json`:

```json
{
  "mcpServers": {
    "movies-db": {
        "url": "http://0.0.0.0:4567/mcp",
        "transport": "streamable-http"
    }
  }
}
```

**Configuration Options**:
- **url**: MCP server endpoint
- **transport**: Communication protocol (streamable-http, stdio, sse)
- **Additional servers**: Can configure multiple MCP servers

### Agent Configuration

```python
# LLM Configuration
llm = ChatOpenAI(model="gpt-4o")

# Agent Configuration
agent = MCPAgent(
    llm=llm, 
    client=client, 
    max_steps=30  # Maximum reasoning steps
)
```

## Streamlit Interface Features

### 🎬 Main Chat Interface
- **Title**: "MCP Movies Database Chatbot"
- **Icon**: Movie emoji (🎬)
- **Layout**: Wide layout for better readability
- **Input**: Chat input with placeholder suggestions

### 💬 Chat History Management
- **Session State**: Persistent chat history during session
- **Message Display**: Alternating user/assistant messages
- **Clear History**: Button to reset conversation

### ℹ️ Sidebar Information
- **About Section**: Explains MCP functionality
- **Example Queries**: Provides query suggestions:
  - "Tell me about Lord of the Rings"
  - "What movies were released in 2023?"
  - "Find action movies with high ratings"
  - "Show me movies by Christopher Nolan"

### 🔄 Loading States
- **Initialization**: "Initializing MCP agent..." spinner
- **Query Processing**: "Searching movies database..." spinner
- **Error Handling**: Displays errors in red with error details

## Advanced Features

### Asynchronous Processing
- **Async/Await**: Full async support for MCP operations
- **Non-blocking UI**: Streamlit integration with async operations
- **Concurrent Handling**: Multiple queries can be processed

### Error Handling
```python
try:
    response = asyncio.run(process_query(st.session_state.agent, prompt))
    st.markdown(response)
except Exception as e:
    error_msg = f"Error: {str(e)}"
    st.error(error_msg)
```

### Session Management
- **Agent Persistence**: MCP agent initialized once per session
- **State Management**: Chat history maintained in session state
- **Resource Cleanup**: Proper handling of connections

## Customization

### Adding New Query Types
1. The client automatically supports new server tools
2. No code changes needed for new MCP tools
3. The AI agent will discover and use new tools automatically

### UI Customization
```python
# Page configuration
st.set_page_config(
    page_title="Custom Movie Bot",
    page_icon="🎭",
    layout="wide"
)

# Custom styling
st.markdown("""
<style>
    .main-header { color: #ff6b6b; }
</style>
""", unsafe_allow_html=True)
```

### Agent Behavior
```python
# Modify agent parameters
agent = MCPAgent(
    llm=llm, 
    client=client, 
    max_steps=50,  # More reasoning steps
    verbose=True   # Debug information
)
```

## Integration Examples

### With Other MCP Servers
```json
{
  "mcpServers": {
    "movies-db": {
        "url": "http://0.0.0.0:4567/mcp",
        "transport": "streamable-http"
    },
    "weather-api": {
        "url": "http://0.0.0.0:4568/mcp",
        "transport": "streamable-http"
    }
  }
}
```

### With Different LLMs
```python
# Using different models
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# OpenAI GPT-4
llm = ChatOpenAI(model="gpt-4-turbo")

# Anthropic Claude
llm = ChatAnthropic(model="claude-3-sonnet-20240229")
```

## Troubleshooting

### Common Issues

1. **"MCP server not responding"**
   - Verify server is running on correct port
   - Check `mcp_config.json` URL configuration
   - Ensure no firewall blocking connections

2. **"OpenAI API error"**
   - Verify `OPENAI_API_KEY` is set in environment
   - Check API key has sufficient credits
   - Ensure `.env` file is loaded properly

3. **"Agent initialization failed"**
   - Check all dependencies are installed
   - Verify MCP server is accessible
   - Review console logs for specific errors

4. **"Streamlit won't start"**
   - Ensure port 8501 is available
   - Try specifying different port: `streamlit run --server.port 8502`
   - Check Python environment and dependencies

### Debug Mode
Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Connection Testing
```python
# Test MCP connection
async def test_connection():
    client = MCPClient.from_config_file("config/mcp_config.json")
    tools = await client.list_tools()
    print(f"Available tools: {tools}")
```

## Development

### Local Development
1. Start the MCP server in one terminal
2. Start the Streamlit app in another terminal
3. Make changes and refresh the browser

### Adding Features
- **New UI elements**: Add Streamlit components
- **Enhanced queries**: Modify the agent configuration
- **Custom styling**: Add CSS through `st.markdown()`

### Testing
- **Manual testing**: Use the Streamlit interface
- **CLI testing**: Run the standalone script
- **Unit tests**: Test individual functions

## Performance Considerations

### Optimization Tips
- **Agent caching**: Agent is initialized once per session
- **Response streaming**: Real-time response display
- **Error boundaries**: Graceful error handling prevents crashes
- **Memory management**: Chat history is session-scoped

### Scaling
- **Multiple users**: Streamlit handles concurrent sessions
- **Load balancing**: Can deploy multiple instances
- **Caching**: Consider Redis for shared state across instances

## Contributing

When extending the client:
1. Follow async/await patterns for MCP operations
2. Handle errors gracefully with user-friendly messages
3. Update example queries in the sidebar
4. Test with various query types and edge cases
5. Update this README with new features
