# MCP Movies Database Server

## Overview

The MCP Movies Database Server is a **Model Context Protocol (MCP)** server built with FastMCP that exposes comprehensive CRUD (Create, Read, Update, Delete) operations for a movies database. This server provides AI agents and MCP clients with powerful tools to interact with movie data through standardized MCP protocols.

## Architecture

```
┌─────────────────────────────────────────┐
│            MCP Client                   │
│        (movies_chatbot.py)              │
└─────────────┬───────────────────────────┘
              │ MCP Protocol
              │ (HTTP Transport)
┌─────────────▼───────────────────────────┐
│          MCP Server                     │
│      (movies_mcp_server.py)             │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │         FastMCP Tools           │    │
│  │  • create_movie                 │    │
│  │  • search_movies_by_title       │    │
│  │  • get_movies_by_genre          │    │
│  │  • update_movie                 │    │
│  │  • delete_movie                 │    │
│  │  • get_database_statistics      │    │
│  │  • ... and more                 │    │
│  └─────────────────────────────────┘    │
└─────────────┬───────────────────────────┘
              │ SQLite Queries
┌─────────────▼───────────────────────────┐
│         SQLite Database                 │
│          (movies.db)                    │
└─────────────────────────────────────────┘
```

## Features

### 🎬 Complete Movie Database Operations
- **Create**: Add new movies with full metadata
- **Read**: Search, filter, and retrieve movie information
- **Update**: Modify existing movie data and ratings
- **Delete**: Remove movies from the database

### 🔍 Advanced Search Capabilities
- Search by title (partial matching)
- Filter by genre, year, language
- Find top-rated movies with minimum vote thresholds
- Advanced multi-criteria search with rating ranges

### 📊 Analytics & Statistics
- Comprehensive database statistics
- Genre and language distributions
- Rating analytics and popularity metrics
- Temporal analysis by decade

### 🚀 MCP Protocol Integration
- Built with FastMCP for seamless MCP compliance
- HTTP transport with streamable responses
- Standardized tool definitions for AI agents
- Error handling with structured responses

## Installation

### Prerequisites
- Python 3.8+
- SQLite3
- Required Python packages (see `requirements.txt`)

### Setup
1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables** (create `.env` file):
   ```bash
   # Database configuration
   DB_FILE_PATH=./data/movies.db
   CSV_FILE_PATH=./data/mymoviedb.csv
   ```

3. **Initialize the database** (if not already done):
   ```bash
   python utilities/ingest_movies_to_sqlite.py
   ```

## Usage

### Starting the Server

```bash
# Navigate to the server directory
cd server/

# Start the MCP server
python movies_mcp_server.py
```

The server will start on `http://0.0.0.0:4567` and expose the MCP endpoint at `/mcp`.

### Server Configuration

The server is configured in `config/mcp_config.json`:
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

## Available Tools

### Create Operations
- **`create_movie`**: Add a new movie with full metadata
  - Parameters: title*, release_date, overview, popularity, vote_count, vote_average, original_language, genre, poster_url
  - Returns: Movie ID and success status

### Read Operations
- **`get_movie_by_id`**: Retrieve a specific movie by its database ID
- **`search_movies_by_title`**: Find movies by title (supports partial matching)
- **`get_movies_by_genre`**: Filter movies by genre
- **`get_movies_by_year`**: Find movies released in a specific year
- **`get_top_rated_movies`**: Get highest-rated movies with minimum vote threshold
- **`advanced_search_movies`**: Multi-criteria search with various filters

### Update Operations
- **`update_movie`**: Modify existing movie information
- **`add_movie_vote`**: Add a new rating and update the movie's average

### Delete Operations
- **`delete_movie`**: Remove a movie from the database

### Analytics
- **`get_database_statistics`**: Comprehensive database analytics including:
  - Total movie count
  - Date range coverage
  - Rating statistics
  - Top genres and languages
  - Movies by decade

## Database Schema

```sql
CREATE TABLE movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    release_date DATE,
    title TEXT NOT NULL,
    overview TEXT,
    popularity REAL,
    vote_count INTEGER,
    vote_average REAL,
    original_language TEXT,
    genre TEXT,
    poster_url TEXT
);
```

### Indexes
- `idx_title`: For fast title searches
- `idx_release_date`: For date-based queries
- `idx_popularity`: For popularity-based sorting
- `idx_vote_average`: For rating-based filtering

## Example Tool Usage

### Creating a Movie
```python
# Tool call example
{
    "tool": "create_movie",
    "parameters": {
        "title": "The Matrix Resurrections",
        "release_date": "2021-12-22",
        "overview": "Return to a world of two realities...",
        "popularity": 150.5,
        "vote_count": 1500,
        "vote_average": 7.5,
        "original_language": "en",
        "genre": "Science Fiction, Action"
    }
}
```

### Advanced Search
```python
# Tool call example
{
    "tool": "advanced_search_movies",
    "parameters": {
        "genre": "Action",
        "min_rating": 7.0,
        "year_from": 2020,
        "year_to": 2023,
        "limit": 10
    }
}
```

## Error Handling

The server implements comprehensive error handling:
- **Validation errors**: Invalid parameters, date formats, rating ranges
- **Database errors**: Connection issues, constraint violations
- **Not found errors**: Missing movie IDs
- **Structured responses**: All errors return JSON with `success: false` and error messages

## Performance Features

- **Connection pooling**: Efficient database connection management
- **Indexed queries**: Optimized database indexes for fast searches
- **Result limiting**: Configurable result limits to prevent large responses
- **Row factory**: Named column access for better data handling

## Integration with MCP Clients

This server is designed to work with various MCP clients:
- **AI Agents**: LangChain, custom agents using mcp-use
- **Chat interfaces**: Streamlit apps, web interfaces
- **Development tools**: Cursor, Windsurf, Claude Desktop

### Client Configuration Example
```python
from mcp_use import MCPClient

# Create client from config
client = MCPClient.from_config_file("config/mcp_config.json")

# Use with AI agents
agent = MCPAgent(llm=llm, client=client)
result = await agent.run("Find action movies from 2023")
```

## Development

### Code Structure
```
server/
├── __init__.py
├── movies_mcp_server.py    # Main server implementation
└── README.md              # This file
```

### Key Dependencies
- **FastMCP**: MCP server framework
- **SQLite3**: Database operations
- **Python typing**: Type hints for better code quality

### Testing
The server includes built-in validation and error handling. Test the server by:
1. Starting the server
2. Connecting with an MCP client
3. Running tool operations through the client

## Troubleshooting

### Common Issues

1. **Database not found**
   - Ensure `DB_FILE_PATH` environment variable is set
   - Run the database ingestion script first

2. **Port already in use**
   - Change the port in the server startup configuration
   - Check for other processes using port 4567

3. **Connection refused**
   - Verify server is running
   - Check firewall settings
   - Ensure correct URL in client configuration

### Logging
The server provides console output for:
- Server startup confirmation
- Available tools listing
- Database path information
- Connection status

## Contributing

When extending the server:
1. Follow the existing tool pattern using `@mcp.tool()` decorator
2. Implement proper error handling with structured responses
3. Add parameter validation and type hints
4. Update this README with new tool documentation

## License

This project is part of the MCP workshop demonstration and is intended for educational purposes.
