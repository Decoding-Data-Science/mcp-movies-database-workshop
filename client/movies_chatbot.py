import os
import sys
import asyncio
import logging
import hashlib
import time
from pathlib import Path
from typing import Optional, Dict, List, Any
from os.path import dirname as up

sys.path.append(os.path.abspath(os.path.join(up(__file__), os.pardir)))

import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient

from utilities.constants import MCP_CONFIG_FILE_PATH

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Performance optimization constants
CACHE_TTL = 300  # 5 minutes cache TTL
MAX_CACHE_SIZE = 50  # Maximum cached responses

# Available OpenAI models
AVAILABLE_MODELS = {
    "gpt-4o": "GPT-4o",
    "gpt-4o-mini": "GPT-4o Mini",
    "o3": "o3 (Latest)",
    "o3-mini": "o3 Mini",
    "gpt-4": "GPT-4",
    "gpt-4-mini": "GPT-4 Mini",
    "gpt-5": "GPT-5 (Newest)",
    "gpt-5-mini": "GPT-5 Mini",
    "gpt-5-nano": "GPT-5 Nano"
}

# Custom exception classes for better error handling
class MCPConnectionError(Exception):
    """Raised when MCP connection fails"""
    pass

class LLMInitializationError(Exception):
    """Raised when LLM initialization fails"""
    pass

# Caching utilities for performance optimization
def get_query_hash(query: str) -> str:
    """Generate a hash for query caching"""
    return hashlib.md5(query.lower().strip().encode()).hexdigest()

def init_cache() -> None:
    """Initialize response cache in session state"""
    if "response_cache" not in st.session_state:
        st.session_state.response_cache = {}
    if "cache_timestamps" not in st.session_state:
        st.session_state.cache_timestamps = {}

def get_cached_response(query: str) -> Optional[str]:
    """Get cached response if available and not expired"""
    init_cache()
    query_hash = get_query_hash(query)
    
    if query_hash in st.session_state.response_cache:
        timestamp = st.session_state.cache_timestamps.get(query_hash, 0)
        if time.time() - timestamp < CACHE_TTL:
            logger.info(f"Cache hit for query: {query[:50]}...")
            # Track cache hits
            if "cache_hits" not in st.session_state:
                st.session_state.cache_hits = 0
            st.session_state.cache_hits += 1
            return st.session_state.response_cache[query_hash]
        else:
            # Remove expired cache entry
            del st.session_state.response_cache[query_hash]
            del st.session_state.cache_timestamps[query_hash]
    
    return None

def cache_response(query: str, response: str) -> None:
    """Cache response with timestamp"""
    init_cache()
    query_hash = get_query_hash(query)
    
    # Implement LRU-like cache size management
    if len(st.session_state.response_cache) >= MAX_CACHE_SIZE:
        # Remove oldest entry
        oldest_hash = min(st.session_state.cache_timestamps.keys(), 
                         key=lambda k: st.session_state.cache_timestamps[k])
        del st.session_state.response_cache[oldest_hash]
        del st.session_state.cache_timestamps[oldest_hash]
    
    st.session_state.response_cache[query_hash] = response
    st.session_state.cache_timestamps[query_hash] = time.time()
    logger.info(f"Cached response for query: {query[:50]}...")

# Function to initialize MCP agent
async def init_mcp_agent(model: str = "gpt-4o", api_key: Optional[str] = None) -> Optional[MCPAgent]:
    """
    Initialize and return the MCP agent with client and LLM.
    
    Args:
        model: OpenAI model to use (default: gpt-4o)
        api_key: OpenAI API key (optional, uses environment variable if not provided)
    
    Returns:
        MCPAgent: Initialized agent ready for queries
        
    Raises:
        MCPConnectionError: If MCP client initialization fails
        LLMInitializationError: If LLM initialization fails
    """
    try:
        logger.info(f"Initializing MCP agent with model: {model}")
        
        # Validate config file exists
        if not MCP_CONFIG_FILE_PATH or not Path(MCP_CONFIG_FILE_PATH).exists():
            raise MCPConnectionError(f"MCP config file not found: {MCP_CONFIG_FILE_PATH}")
        
        # Create MCPClient from config file
        logger.info(f"Loading MCP config from: {MCP_CONFIG_FILE_PATH}")
        client = MCPClient.from_config_file(str(MCP_CONFIG_FILE_PATH))
        
        # Create LLM with error handling
        logger.info(f"Initializing OpenAI LLM with model: {model}")
        llm_kwargs = {
            "model": model,
            "temperature": 0.1
        }
        
        # Add API key if provided
        if api_key:
            llm_kwargs["api_key"] = api_key
            logger.info("Using provided API key")
        
        llm = ChatOpenAI(**llm_kwargs)
        
        # Create agent with the client
        logger.info("Creating MCP agent...")
        agent = MCPAgent(llm=llm, client=client, max_steps=30)
        
        logger.info("MCP agent initialized successfully!")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to initialize MCP agent: {str(e)}")
        if "config" in str(e).lower():
            raise MCPConnectionError(f"MCP configuration error: {str(e)}")
        elif "openai" in str(e).lower() or "api" in str(e).lower() or "authentication" in str(e).lower():
            raise LLMInitializationError(f"LLM initialization error: {str(e)}")
        else:
            raise MCPConnectionError(f"Unknown initialization error: {str(e)}")

# Function to process user query with caching
async def process_query(agent: MCPAgent, query: str) -> str:
    """
    Process user query using the MCP agent with caching support.
    
    Args:
        agent: Initialized MCP agent
        query: User's query string
        
    Returns:
        str: Agent's response to the query
        
    Raises:
        ValueError: If query is empty or agent is None
        Exception: If query processing fails
    """
    if not agent:
        raise ValueError("Agent is not initialized")
    
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    # Check cache first
    cached_response = get_cached_response(query)
    if cached_response:
        return cached_response
    
    try:
        logger.info(f"Processing query: {query[:100]}...")  # Log first 100 chars
        start_time = time.time()
        
        result = await agent.run(
            query.strip(),
            max_steps=30,
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Query processed successfully in {processing_time:.2f}s")
        
        # Cache the response
        cache_response(query, result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise Exception(f"Failed to process query: {str(e)}")

# Original main function (preserved for testing)
async def main():
    # Load environment variables
    load_dotenv()

    # Create MCPClient from config file
    client = MCPClient.from_config_file(MCP_CONFIG_FILE_PATH)

    # Create LLM
    llm = ChatOpenAI(model="gpt-4o")

    # Create agent with the client
    agent = MCPAgent(llm=llm, client=client, max_steps=30)

    # Run the query
    result = await agent.run(
        "Tell me the years when Lord of the Rings was released.",
        max_steps=30,
    )
    print(f"\nResult: {result}")

# Helper functions for UI
def display_connection_status() -> None:
    """Display MCP connection status in the sidebar"""
    if "agent" in st.session_state and st.session_state.agent:
        current_model = st.session_state.get("selected_model", "gpt-4o")
        st.success(f"🟢 MCP Agent Connected")
        st.info(f"📱 Model: {AVAILABLE_MODELS.get(current_model, current_model)}")
    elif "agent_error" in st.session_state:
        st.error(f"🔴 Connection Failed: {st.session_state.agent_error}")
    else:
        st.warning("🟡 Initializing...")

def display_model_configuration() -> tuple[str, Optional[str]]:
    """Display model and API key configuration UI"""
    st.header("⚙️ Configuration")
    
    # Model selection
    current_model = st.session_state.get("selected_model", "gpt-4o")
    selected_model = st.selectbox(
        "Select OpenAI Model",
        options=list(AVAILABLE_MODELS.keys()),
        index=list(AVAILABLE_MODELS.keys()).index(current_model) if current_model in AVAILABLE_MODELS else 0,
        format_func=lambda x: AVAILABLE_MODELS[x],
        help="Choose the OpenAI model for the chatbot"
    )
    
    # API Key input
    api_key_input = st.text_input(
        "OpenAI API Key (Optional)",
        type="password",
        placeholder="sk-...",
        help="Leave empty to use environment variable OPENAI_API_KEY",
        value=st.session_state.get("custom_api_key", "")
    )
    
    # Configuration changed detection
    config_changed = (
        selected_model != st.session_state.get("selected_model", "gpt-4o") or
        api_key_input != st.session_state.get("custom_api_key", "")
    )
    
    if config_changed:
        st.session_state.selected_model = selected_model
        st.session_state.custom_api_key = api_key_input
        
        # Show apply button if configuration changed
        if st.button("🔄 Apply Configuration", use_container_width=True):
            # Clear existing agent to force reinitialization
            if "agent" in st.session_state:
                del st.session_state.agent
            if "agent_error" in st.session_state:
                del st.session_state.agent_error
            st.rerun()
    
    return selected_model, api_key_input if api_key_input else None

def get_sample_queries() -> List[str]:
    """Get sample queries for user guidance"""
    base_queries = [
        "Tell me about Lord of the Rings movies",
        "What movies were released in 2022?",
        "Find action movies with high ratings",
        "What are the top-rated sci-fi movies?",
        "What animated movies are in the database?",
    ]
    
    # Add contextual queries based on chat history
    if "messages" in st.session_state and st.session_state.messages:
        recent_queries = [m["content"] for m in st.session_state.messages[-6:] if m["role"] == "user"]
        
        # Generate follow-up suggestions based on recent queries
        follow_up_suggestions = []
        for query in recent_queries:
            if "director" in query.lower():
                follow_up_suggestions.append("What are the highest-rated movies by this director?")
            elif "actor" in query.lower() or any(name in query for name in ["tom", "brad", "leonardo", "scarlett"]):
                follow_up_suggestions.append("What other movies feature this actor?")
            elif "year" in query.lower() or any(year in query for year in ["2020", "2021", "2022", "2023", "2024"]):
                follow_up_suggestions.append("What were the top movies of that year?")
            elif "genre" in query.lower() or any(genre in query.lower() for genre in ["action", "comedy", "drama", "sci-fi"]):
                follow_up_suggestions.append("Show me more movies in this genre")
        
        # Add unique follow-up suggestions
        for suggestion in follow_up_suggestions[:2]:  # Limit to 2 follow-ups
            if suggestion not in base_queries:
                base_queries.append(suggestion)
    
    return base_queries

def display_sample_queries() -> None:
    """Display clickable sample queries"""
    st.subheader("💡 Sample Queries")
    queries = get_sample_queries()
    
    # Display in columns for better layout
    cols = st.columns(2)
    for i, query in enumerate(queries):
        with cols[i % 2]:
            if st.button(query, key=f"sample_{i}", use_container_width=True):
                st.session_state.selected_query = query

# Streamlit chatbot application
def streamlit_app() -> None:
    """Main Streamlit chatbot application with enhanced UI/UX"""
    st.set_page_config(
        page_title="MCP Movies Chatbot",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
    }
    .chat-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .status-container {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header
    st.markdown('<h1 class="main-header">🎬 MCP Movies Database Chatbot</h1>', unsafe_allow_html=True)
    st.markdown("### Explore our movie database with natural language queries!")
    
    # Initialize session state variables
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "selected_query" not in st.session_state:
        st.session_state.selected_query = None
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "gpt-4o"
    if "custom_api_key" not in st.session_state:
        st.session_state.custom_api_key = ""
    
    # Initialize MCP agent with better error handling
    if "agent" not in st.session_state and "agent_error" not in st.session_state:
        try:
            with st.spinner("🔄 Initializing MCP agent... This may take a moment."):
                selected_model = st.session_state.get("selected_model", "gpt-4o")
                api_key = st.session_state.get("custom_api_key", "") or None
                st.session_state.agent = asyncio.run(init_mcp_agent(model=selected_model, api_key=api_key))
        except (MCPConnectionError, LLMInitializationError) as e:
            st.session_state.agent_error = str(e)
            st.error(f"❌ Failed to initialize agent: {str(e)}")
        except Exception as e:
            st.session_state.agent_error = f"Unexpected error: {str(e)}"
            st.error(f"❌ Unexpected error: {str(e)}")
    
    # Main chat interface
    chat_container = st.container()
    
    with chat_container:
        # Welcome message for new users
        if not st.session_state.messages and "agent" in st.session_state and st.session_state.agent:
            with st.chat_message("assistant"):
                st.markdown("""
                👋 **Welcome to the MCP Movies Database Chatbot!**
                
                I can help you explore our movie database using natural language. Here are some things you can ask me:
                
                🎬 **Movie Information**: "Tell me about Inception" or "What's the plot of The Matrix?"
                
                🎭 **By Actor/Director**: "Show me Tom Hanks movies" or "What did Christopher Nolan direct?"
                
                📅 **By Year/Era**: "What movies came out in 2023?" or "Best movies from the 90s"
                
                🏆 **Ratings & Reviews**: "Highest rated sci-fi movies" or "Best action movies"
                
                🔍 **Comparisons**: "Compare Marvel and DC movies" or "Which is better: Star Wars or Star Trek?"
                
                Just type your question below and I'll search the database for you! 🚀
                """)
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Handle selected query from sidebar
    prompt = None
    if st.session_state.selected_query:
        prompt = st.session_state.selected_query
        st.session_state.selected_query = None  # Reset after use
    
    # Chat input
    if not prompt:
        prompt = st.chat_input(
            "Ask about movies (e.g., 'Tell me about Lord of the Rings')",
            disabled=("agent" not in st.session_state or st.session_state.agent is None)
        )
    
    if prompt:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            if "agent" not in st.session_state or st.session_state.agent is None:
                st.error("❌ Agent not initialized. Please refresh the page.")
            else:
                with st.spinner("🔍 Searching movies database..."):
                    try:
                        # Process the query
                        response = asyncio.run(process_query(st.session_state.agent, prompt))
                        st.markdown(response)
                        
                        # Add assistant response to chat history
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    except ValueError as e:
                        error_msg = f"❌ Invalid input: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    except Exception as e:
                        error_msg = f"❌ Error processing query: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Enhanced sidebar with multiple sections
    with st.sidebar:
        # Configuration section
        display_model_configuration()
        
        # Connection status
        st.header("🔗 Connection Status")
        display_connection_status()
        
        # Agent info and controls
        if "agent" in st.session_state and st.session_state.agent:
            st.header("🤖 Agent Controls")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Reconnect", use_container_width=True):
                    if "agent" in st.session_state:
                        del st.session_state.agent
                    if "agent_error" in st.session_state:
                        del st.session_state.agent_error
                    # Reinitialize with current configuration
                    try:
                        with st.spinner("🔄 Reconnecting with current settings..."):
                            selected_model = st.session_state.get("selected_model", "gpt-4o")
                            api_key = st.session_state.get("custom_api_key", "") or None
                            st.session_state.agent = asyncio.run(init_mcp_agent(model=selected_model, api_key=api_key))
                        st.success("✅ Reconnected successfully!")
                    except (MCPConnectionError, LLMInitializationError) as e:
                        st.session_state.agent_error = str(e)
                        st.error(f"❌ Reconnection failed: {str(e)}")
                    except Exception as e:
                        st.session_state.agent_error = f"Unexpected error: {str(e)}"
                        st.error(f"❌ Unexpected error: {str(e)}")
                    st.rerun()
            
            with col2:
                if st.button("🗑️ Clear Chat", use_container_width=True):
                    st.session_state.messages = []
                    st.rerun()
            
            # Cache management
            if "response_cache" in st.session_state and st.session_state.response_cache:
                if st.button("🧹 Clear Cache", use_container_width=True):
                    st.session_state.response_cache = {}
                    st.session_state.cache_timestamps = {}
                    if "cache_hits" in st.session_state:
                        st.session_state.cache_hits = 0
                    st.success("Cache cleared!")
                    st.rerun()
        
        # Sample queries section
        st.header("💡 Quick Start")
        display_sample_queries()
        
        # Statistics
        if st.session_state.messages:
            st.header("📊 Chat Statistics")
            user_messages = len([m for m in st.session_state.messages if m["role"] == "user"])
            st.metric("Queries Asked", user_messages)
            st.metric("Total Messages", len(st.session_state.messages))
            
            # Cache statistics
            if "response_cache" in st.session_state:
                cache_size = len(st.session_state.response_cache)
                st.metric("Cached Responses", cache_size)
                if cache_size > 0:
                    cache_hit_rate = st.session_state.get("cache_hits", 0) / max(user_messages, 1) * 100
                    st.metric("Cache Hit Rate", f"{cache_hit_rate:.1f}%")
        
        # About section
        st.header("ℹ️ About")
        with st.expander("How it works"):
            st.markdown("""
            This chatbot uses the **MCP (Model Context Protocol)** to query a movies database.
            
            **Features:**
            - Natural language movie queries
            - Multiple OpenAI model support
            - Custom API key configuration
            - Real-time database search
            - Intelligent response caching
            - Error handling and recovery
            
            **Supported Models:**
            - GPT-4o, GPT-4o Mini
            - o3, o3 Mini (Latest reasoning models)
            - GPT-4, GPT-4 Mini
            - GPT-5, GPT-5 Mini, GPT-5 Nano (Newest generation)
            
            **Powered by:**
            - OpenAI Models (Configurable)
            - MCP Protocol
            - Streamlit UI
            """)
        
        # Model information
        if "agent" in st.session_state and st.session_state.agent:
            current_model = st.session_state.get("selected_model", "gpt-4o")
            with st.expander(f"🤖 Current Model: {AVAILABLE_MODELS.get(current_model, current_model)}"):
                model_info = {
                    "gpt-4o": "Advanced model with excellent reasoning and multimodal capabilities",
                    "gpt-4o-mini": "Faster, cost-effective version of GPT-4o",
                    "o3": "Latest reasoning model with enhanced problem-solving capabilities",
                    "o3-mini": "Efficient version of o3 model",
                    "gpt-4": "Previous generation flagship model",
                    "gpt-4-mini": "Lightweight version of GPT-4",
                    "gpt-5": "Newest generation model with enhanced capabilities",
                    "gpt-5-mini": "Efficient newest generation model",
                    "gpt-5-nano": "Ultra-efficient newest generation model"
                }
                
                st.markdown(f"**Description:** {model_info.get(current_model, 'Advanced language model')}")
                
                # Show info for newest models
                if current_model in ["gpt-5", "gpt-5-mini", "gpt-5-nano"]:
                    st.info("🆕 Using the newest generation GPT-5 model!")
                elif current_model in ["o3", "o3-mini"]:
                    st.info("🧠 Using advanced reasoning model optimized for complex problem-solving!")
        
        # Tips section
        with st.expander("💡 Tips for better results"):
            st.markdown("""
            - Be specific in your queries
            - Ask about genres, actors, directors, or years
            - Use natural language - no need for SQL!
            - Try comparative queries like "best rated movies"
            - Ask for recommendations based on preferences
            - Different models may provide varying response styles
            """)
        
        # Footer
        st.markdown("---")
        st.markdown("*Built with ❤️ using MCP & Streamlit*")

if __name__ == "__main__":
    # Check if running in Streamlit
    if "streamlit" in os.path.basename(os.environ.get("_", "")):
        streamlit_app()
    else:
        # Run original main function for testing
        asyncio.run(main())