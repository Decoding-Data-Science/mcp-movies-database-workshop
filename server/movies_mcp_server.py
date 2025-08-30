"""
MCP Server for Movies Database CRUD Operations
This server exposes CRUD functions as MCP tools using FastMCP
"""

import os, sys
from os.path import dirname as up

sys.path.append(os.path.abspath(os.path.join(up(__file__), os.pardir)))


from fastmcp import FastMCP
from typing import Optional, List, Dict, Any
import sqlite3
from datetime import datetime
import json

from utilities.constants import DB_FILE_PATH

# Initialize FastMCP server
mcp = FastMCP("Movies Database MCP Server")


# Helper functions
def get_connection():
    """Get database connection"""
    return sqlite3.connect(DB_FILE_PATH)

def execute_query(query: str, params: tuple = (), fetch_one: bool = False):
    """Execute a query and return results"""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute(query, params)
        
        if query.strip().upper().startswith('SELECT'):
            if fetch_one:
                result = cursor.fetchone()
            else:
                result = cursor.fetchall()
            return result
        else:
            conn.commit()
            return cursor.lastrowid if query.strip().upper().startswith('INSERT') else cursor.rowcount
    finally:
        conn.close()

# CREATE Tools
@mcp.tool()
def create_movie(
    title: str,
    release_date: Optional[str] = None,
    overview: str = '',
    popularity: float = 0.0,
    vote_count: int = 0,
    vote_average: float = 0.0,
    original_language: str = 'en',
    genre: str = '',
    poster_url: str = ''
) -> Dict[str, Any]:
    """
    Create a new movie entry in the database
    
    Args:
        title: Movie title (required)
        release_date: Release date in YYYY-MM-DD format
        overview: Movie description
        popularity: Popularity score
        vote_count: Number of votes
        vote_average: Average rating (0-10)
        original_language: Language code (e.g., 'en', 'fr')
        genre: Comma-separated genres
        poster_url: URL to movie poster
        
    Returns:
        Dict with movie_id and success status
    """
    # Validate required fields
    if not title:
        return {"success": False, "error": "Title is required"}
    
    # Validate date format if provided
    if release_date:
        try:
            datetime.strptime(release_date, '%Y-%m-%d')
        except ValueError:
            return {"success": False, "error": "Release date must be in YYYY-MM-DD format"}
    
    # Validate vote average range
    if not 0 <= vote_average <= 10:
        return {"success": False, "error": "Vote average must be between 0 and 10"}
    
    query = """
    INSERT INTO movies (title, release_date, overview, popularity, vote_count, 
                      vote_average, original_language, genre, poster_url)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    params = (title, release_date, overview, popularity, vote_count, 
             vote_average, original_language, genre, poster_url)
    
    try:
        movie_id = execute_query(query, params)
        return {
            "success": True, 
            "movie_id": movie_id,
            "message": f"Movie '{title}' created successfully"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# READ Tools
@mcp.tool()
def get_movie_by_id(movie_id: int) -> Dict[str, Any]:
    """
    Get a movie by its ID
    
    Args:
        movie_id: The ID of the movie to retrieve
        
    Returns:
        Movie data or error message
    """
    query = "SELECT * FROM movies WHERE id = ?"
    result = execute_query(query, (movie_id,), fetch_one=True)
    
    if result:
        return {
            "success": True,
            "movie": dict(result)
        }
    return {"success": False, "error": f"Movie with ID {movie_id} not found"}

@mcp.tool()
def search_movies_by_title(title_search: str, limit: int = 20) -> Dict[str, Any]:
    """
    Search movies by title (partial match)
    
    Args:
        title_search: Search term for movie titles
        limit: Maximum number of results to return
        
    Returns:
        List of matching movies
    """
    query = """
    SELECT * FROM movies 
    WHERE title LIKE ? 
    ORDER BY popularity DESC
    LIMIT ?
    """
    results = execute_query(query, (f'%{title_search}%', limit))
    
    return {
        "success": True,
        "movies": [dict(row) for row in results],
        "count": len(results)
    }

@mcp.tool()
def get_movies_by_genre(genre: str, limit: int = 50) -> Dict[str, Any]:
    """
    Get movies by genre
    
    Args:
        genre: Genre to search for
        limit: Maximum number of results
        
    Returns:
        List of movies in the specified genre
    """
    query = """
    SELECT * FROM movies 
    WHERE genre LIKE ? 
    ORDER BY vote_average DESC, vote_count DESC
    LIMIT ?
    """
    results = execute_query(query, (f'%{genre}%', limit))
    
    return {
        "success": True,
        "movies": [dict(row) for row in results],
        "count": len(results)
    }

@mcp.tool()
def get_movies_by_year(year: int, limit: int = 100) -> Dict[str, Any]:
    """
    Get movies released in a specific year
    
    Args:
        year: The year to search for
        limit: Maximum number of results
        
    Returns:
        List of movies from the specified year
    """
    query = """
    SELECT * FROM movies 
    WHERE strftime('%Y', release_date) = ? 
    ORDER BY popularity DESC
    LIMIT ?
    """
    results = execute_query(query, (str(year), limit))
    
    return {
        "success": True,
        "movies": [dict(row) for row in results],
        "count": len(results)
    }

@mcp.tool()
def get_top_rated_movies(min_votes: int = 100, limit: int = 50) -> Dict[str, Any]:
    """
    Get top-rated movies with minimum vote threshold
    
    Args:
        min_votes: Minimum number of votes required
        limit: Maximum number of results
        
    Returns:
        List of top-rated movies
    """
    query = """
    SELECT * FROM movies 
    WHERE vote_count >= ? 
    ORDER BY vote_average DESC, vote_count DESC
    LIMIT ?
    """
    results = execute_query(query, (min_votes, limit))
    
    return {
        "success": True,
        "movies": [dict(row) for row in results],
        "count": len(results)
    }

@mcp.tool()
def advanced_search_movies(
    title: Optional[str] = None,
    genre: Optional[str] = None,
    language: Optional[str] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Advanced movie search with multiple filters
    
    Args:
        title: Title search term
        genre: Genre filter
        language: Language code filter
        min_rating: Minimum rating filter
        max_rating: Maximum rating filter
        year_from: Start year filter
        year_to: End year filter
        limit: Maximum number of results
        
    Returns:
        List of movies matching the criteria
    """
    conditions = []
    params = []
    
    if title:
        conditions.append("title LIKE ?")
        params.append(f'%{title}%')
    
    if genre:
        conditions.append("genre LIKE ?")
        params.append(f'%{genre}%')
    
    if language:
        conditions.append("original_language = ?")
        params.append(language)
    
    if min_rating is not None:
        conditions.append("vote_average >= ?")
        params.append(min_rating)
    
    if max_rating is not None:
        conditions.append("vote_average <= ?")
        params.append(max_rating)
    
    if year_from:
        conditions.append("strftime('%Y', release_date) >= ?")
        params.append(str(year_from))
    
    if year_to:
        conditions.append("strftime('%Y', release_date) <= ?")
        params.append(str(year_to))
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
    SELECT * FROM movies 
    WHERE {where_clause}
    ORDER BY popularity DESC
    LIMIT ?
    """
    params.append(limit)
    
    results = execute_query(query, tuple(params))
    
    return {
        "success": True,
        "movies": [dict(row) for row in results],
        "count": len(results)
    }

# UPDATE Tools
@mcp.tool()
def update_movie(
    movie_id: int,
    title: Optional[str] = None,
    release_date: Optional[str] = None,
    overview: Optional[str] = None,
    popularity: Optional[float] = None,
    vote_count: Optional[int] = None,
    vote_average: Optional[float] = None,
    original_language: Optional[str] = None,
    genre: Optional[str] = None,
    poster_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update movie information
    
    Args:
        movie_id: ID of the movie to update
        title: New title
        release_date: New release date
        overview: New overview
        popularity: New popularity score
        vote_count: New vote count
        vote_average: New vote average
        original_language: New language
        genre: New genre(s)
        poster_url: New poster URL
        
    Returns:
        Success status and message
    """
    # Build update dictionary
    updates = {}
    if title is not None:
        updates['title'] = title
    if release_date is not None:
        updates['release_date'] = release_date
    if overview is not None:
        updates['overview'] = overview
    if popularity is not None:
        updates['popularity'] = popularity
    if vote_count is not None:
        updates['vote_count'] = vote_count
    if vote_average is not None:
        if not 0 <= vote_average <= 10:
            return {"success": False, "error": "Vote average must be between 0 and 10"}
        updates['vote_average'] = vote_average
    if original_language is not None:
        updates['original_language'] = original_language
    if genre is not None:
        updates['genre'] = genre
    if poster_url is not None:
        updates['poster_url'] = poster_url
    
    if not updates:
        return {"success": False, "error": "No fields to update"}
    
    # Build update query
    set_clause = ", ".join([f"{col} = ?" for col in updates.keys()])
    query = f"UPDATE movies SET {set_clause} WHERE id = ?"
    
    params = list(updates.values()) + [movie_id]
    
    try:
        rows_affected = execute_query(query, tuple(params))
        
        if rows_affected > 0:
            return {
                "success": True,
                "message": f"Movie ID {movie_id} updated successfully"
            }
        else:
            return {
                "success": False,
                "error": f"Movie ID {movie_id} not found"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def add_movie_vote(movie_id: int, rating: float) -> Dict[str, Any]:
    """
    Add a new vote to a movie and update its average rating
    
    Args:
        movie_id: ID of the movie
        rating: New rating to add (0-10)
        
    Returns:
        Success status and new average
    """
    if not 0 <= rating <= 10:
        return {"success": False, "error": "Rating must be between 0 and 10"}
    
    # Get current movie data
    query = "SELECT vote_count, vote_average FROM movies WHERE id = ?"
    result = execute_query(query, (movie_id,), fetch_one=True)
    
    if not result:
        return {"success": False, "error": f"Movie ID {movie_id} not found"}
    
    # Calculate new average
    current_count = result['vote_count']
    current_avg = result['vote_average']
    
    new_count = current_count + 1
    new_avg = ((current_avg * current_count) + rating) / new_count
    new_avg = round(new_avg, 1)
    
    # Update movie
    update_query = "UPDATE movies SET vote_count = ?, vote_average = ? WHERE id = ?"
    rows_affected = execute_query(update_query, (new_count, new_avg, movie_id))
    
    if rows_affected > 0:
        return {
            "success": True,
            "message": f"Vote added successfully",
            "new_average": new_avg,
            "total_votes": new_count
        }
    else:
        return {"success": False, "error": "Failed to update movie"}

# DELETE Tools
@mcp.tool()
def delete_movie(movie_id: int) -> Dict[str, Any]:
    """
    Delete a movie by its ID
    
    Args:
        movie_id: ID of the movie to delete
        
    Returns:
        Success status and message
    """
    # Check if movie exists first
    check_query = "SELECT title FROM movies WHERE id = ?"
    result = execute_query(check_query, (movie_id,), fetch_one=True)
    
    if not result:
        return {"success": False, "error": f"Movie ID {movie_id} not found"}
    
    title = result['title']
    
    # Delete the movie
    delete_query = "DELETE FROM movies WHERE id = ?"
    rows_affected = execute_query(delete_query, (movie_id,))
    
    if rows_affected > 0:
        return {
            "success": True,
            "message": f"Movie '{title}' (ID: {movie_id}) deleted successfully"
        }
    else:
        return {"success": False, "error": "Failed to delete movie"}

# Statistics Tool
@mcp.tool()
def get_database_statistics() -> Dict[str, Any]:
    """
    Get comprehensive statistics about the movies database
    
    Returns:
        Database statistics including counts, averages, and distributions
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    try:
        # Total movies
        cursor.execute("SELECT COUNT(*) FROM movies")
        stats['total_movies'] = cursor.fetchone()[0]
        
        # Date range
        cursor.execute("SELECT MIN(release_date), MAX(release_date) FROM movies WHERE release_date IS NOT NULL")
        min_date, max_date = cursor.fetchone()
        stats['date_range'] = {'from': min_date, 'to': max_date}
        
        # Rating statistics
        cursor.execute("""
            SELECT 
                AVG(vote_average) as avg_rating,
                MIN(vote_average) as min_rating,
                MAX(vote_average) as max_rating,
                AVG(vote_count) as avg_votes
            FROM movies 
            WHERE vote_count > 0
        """)
        result = cursor.fetchone()
        stats['rating_stats'] = {
            'average_rating': round(result[0], 2) if result[0] else 0,
            'min_rating': result[1] or 0,
            'max_rating': result[2] or 0,
            'average_votes': round(result[3], 0) if result[3] else 0
        }
        
        # Most common genres
        cursor.execute("""
            SELECT genre, COUNT(*) as count 
            FROM movies 
            WHERE genre != ''
            GROUP BY genre 
            ORDER BY count DESC 
            LIMIT 10
        """)
        stats['top_genres'] = [{'genre': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Language distribution
        cursor.execute("""
            SELECT original_language, COUNT(*) as count 
            FROM movies 
            GROUP BY original_language 
            ORDER BY count DESC 
            LIMIT 10
        """)
        stats['top_languages'] = [{'language': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Movies by decade
        cursor.execute("""
            SELECT 
                CAST(strftime('%Y', release_date) / 10 * 10 as TEXT) || 's' as decade,
                COUNT(*) as count
            FROM movies 
            WHERE release_date IS NOT NULL
            GROUP BY decade
            ORDER BY decade DESC
            LIMIT 10
        """)
        stats['movies_by_decade'] = [{'decade': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

# Main entry point
if __name__ == "__main__":
    # Run the MCP server
    print("Starting Movies Database MCP Server...")
    print(f"Database: {DB_FILE_PATH}")
    print("\nAvailable tools:")
    print("- create_movie")
    print("- get_movie_by_id")
    print("- search_movies_by_title")
    print("- get_movies_by_genre")
    print("- get_movies_by_year")
    print("- get_top_rated_movies")
    print("- advanced_search_movies")
    print("- update_movie")
    print("- add_movie_vote")
    print("- delete_movie")
    print("- get_database_statistics")
    print("\nServer is running...")
    
    mcp.run(transport="http", host="0.0.0.0", port=4567)
