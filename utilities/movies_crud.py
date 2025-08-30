import os, sys
from os.path import dirname as up

sys.path.append(os.path.abspath(os.path.join(up(__file__), os.pardir)))

import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
import pandas as pd

from utilities.constants import DB_FILE_PATH

class MoviesCRUD:
    """CRUD operations for movies database"""
    
    def __init__(self, db_path: str = DB_FILE_PATH):
        self.db_path = db_path
    
    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def _execute_query(self, query: str, params: tuple = (), fetch_one: bool = False):
        """Execute a query and return results"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row  # Enable column access by name
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
    
    # CREATE operations
    def create_movie(self, 
                    title: str,
                    release_date: Optional[str] = None,
                    overview: str = '',
                    popularity: float = 0.0,
                    vote_count: int = 0,
                    vote_average: float = 0.0,
                    original_language: str = 'en',
                    genre: str = '',
                    poster_url: str = '') -> int:
        """
        Create a new movie entry
        
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
            int: ID of the created movie
        """
        # Validate required fields
        if not title:
            raise ValueError("Title is required")
        
        # Validate date format if provided
        if release_date:
            try:
                datetime.strptime(release_date, '%Y-%m-%d')
            except ValueError:
                raise ValueError("Release date must be in YYYY-MM-DD format")
        
        # Validate vote average range
        if not 0 <= vote_average <= 10:
            raise ValueError("Vote average must be between 0 and 10")
        
        query = """
        INSERT INTO movies (title, release_date, overview, popularity, vote_count, 
                          vote_average, original_language, genre, poster_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (title, release_date, overview, popularity, vote_count, 
                 vote_average, original_language, genre, poster_url)
        
        movie_id = self._execute_query(query, params)
        print(f"✅ Movie '{title}' created with ID: {movie_id}")
        return movie_id
    
    def create_movies_bulk(self, movies_data: List[Dict[str, Any]]) -> int:
        """
        Create multiple movies at once
        
        Args:
            movies_data: List of dictionaries containing movie data
            
        Returns:
            int: Number of movies created
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = """
        INSERT INTO movies (title, release_date, overview, popularity, vote_count, 
                          vote_average, original_language, genre, poster_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        count = 0
        try:
            for movie in movies_data:
                params = (
                    movie.get('title'),
                    movie.get('release_date'),
                    movie.get('overview', ''),
                    movie.get('popularity', 0.0),
                    movie.get('vote_count', 0),
                    movie.get('vote_average', 0.0),
                    movie.get('original_language', 'en'),
                    movie.get('genre', ''),
                    movie.get('poster_url', '')
                )
                cursor.execute(query, params)
                count += 1
            
            conn.commit()
            print(f"✅ Successfully created {count} movies")
            return count
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    # READ operations
    def get_movie_by_id(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """Get a movie by its ID"""
        query = "SELECT * FROM movies WHERE id = ?"
        result = self._execute_query(query, (movie_id,), fetch_one=True)
        
        if result:
            return dict(result)
        return None
    
    def get_movies_by_title(self, title_search: str) -> List[Dict[str, Any]]:
        """Search movies by title (partial match)"""
        query = """
        SELECT * FROM movies 
        WHERE title LIKE ? 
        ORDER BY popularity DESC
        """
        results = self._execute_query(query, (f'%{title_search}%',))
        return [dict(row) for row in results]
    
    def get_movies_by_genre(self, genre: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get movies by genre"""
        query = """
        SELECT * FROM movies 
        WHERE genre LIKE ? 
        ORDER BY vote_average DESC, vote_count DESC
        LIMIT ?
        """
        results = self._execute_query(query, (f'%{genre}%', limit))
        return [dict(row) for row in results]
    
    def get_movies_by_year(self, year: int) -> List[Dict[str, Any]]:
        """Get movies released in a specific year"""
        query = """
        SELECT * FROM movies 
        WHERE strftime('%Y', release_date) = ? 
        ORDER BY popularity DESC
        """
        results = self._execute_query(query, (str(year),))
        return [dict(row) for row in results]
    
    def get_top_rated_movies(self, min_votes: int = 100, limit: int = 50) -> List[Dict[str, Any]]:
        """Get top-rated movies with minimum vote threshold"""
        query = """
        SELECT * FROM movies 
        WHERE vote_count >= ? 
        ORDER BY vote_average DESC, vote_count DESC
        LIMIT ?
        """
        results = self._execute_query(query, (min_votes, limit))
        return [dict(row) for row in results]
    
    def get_recent_movies(self, days: int = 365) -> List[Dict[str, Any]]:
        """Get movies released in the last N days"""
        query = """
        SELECT * FROM movies 
        WHERE release_date >= date('now', '-' || ? || ' days')
        ORDER BY release_date DESC
        """
        results = self._execute_query(query, (days,))
        return [dict(row) for row in results]
    
    def search_movies(self, 
                     title: Optional[str] = None,
                     genre: Optional[str] = None,
                     language: Optional[str] = None,
                     min_rating: Optional[float] = None,
                     max_rating: Optional[float] = None,
                     year_from: Optional[int] = None,
                     year_to: Optional[int] = None,
                     order_by: str = 'popularity DESC',
                     limit: int = 100) -> List[Dict[str, Any]]:
        """
        Advanced search with multiple filters
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
        ORDER BY {order_by}
        LIMIT ?
        """
        params.append(limit)
        
        results = self._execute_query(query, tuple(params))
        return [dict(row) for row in results]
    
    # UPDATE operations
    def update_movie(self, movie_id: int, **kwargs) -> bool:
        """
        Update movie fields
        
        Args:
            movie_id: ID of the movie to update
            **kwargs: Fields to update (title, release_date, overview, etc.)
            
        Returns:
            bool: True if update was successful
        """
        # Get valid column names
        valid_columns = ['title', 'release_date', 'overview', 'popularity', 
                        'vote_count', 'vote_average', 'original_language', 
                        'genre', 'poster_url']
        
        # Filter out invalid columns
        updates = {k: v for k, v in kwargs.items() if k in valid_columns}
        
        if not updates:
            raise ValueError("No valid fields to update")
        
        # Validate vote_average if provided
        if 'vote_average' in updates and not 0 <= updates['vote_average'] <= 10:
            raise ValueError("Vote average must be between 0 and 10")
        
        # Build update query
        set_clause = ", ".join([f"{col} = ?" for col in updates.keys()])
        query = f"UPDATE movies SET {set_clause} WHERE id = ?"
        
        params = list(updates.values()) + [movie_id]
        
        rows_affected = self._execute_query(query, tuple(params))
        
        if rows_affected > 0:
            print(f"✅ Movie ID {movie_id} updated successfully")
            return True
        else:
            print(f"❌ Movie ID {movie_id} not found")
            return False
    
    def increment_vote(self, movie_id: int, new_rating: float) -> bool:
        """
        Add a new vote to a movie and update average
        
        Args:
            movie_id: ID of the movie
            new_rating: Rating to add (0-10)
            
        Returns:
            bool: True if successful
        """
        if not 0 <= new_rating <= 10:
            raise ValueError("Rating must be between 0 and 10")
        
        # Get current movie data
        movie = self.get_movie_by_id(movie_id)
        if not movie:
            return False
        
        # Calculate new average
        current_count = movie['vote_count']
        current_avg = movie['vote_average']
        
        new_count = current_count + 1
        new_avg = ((current_avg * current_count) + new_rating) / new_count
        
        # Update movie
        return self.update_movie(movie_id, vote_count=new_count, vote_average=round(new_avg, 1))
    
    # DELETE operations
    def delete_movie(self, movie_id: int) -> bool:
        """Delete a movie by ID"""
        # Check if movie exists first
        movie = self.get_movie_by_id(movie_id)
        if not movie:
            print(f"❌ Movie ID {movie_id} not found")
            return False
        
        query = "DELETE FROM movies WHERE id = ?"
        rows_affected = self._execute_query(query, (movie_id,))
        
        if rows_affected > 0:
            print(f"✅ Movie '{movie['title']}' (ID: {movie_id}) deleted successfully")
            return True
        return False
    
    def delete_movies_by_criteria(self, 
                                 before_date: Optional[str] = None,
                                 min_rating: Optional[float] = None,
                                 min_votes: Optional[int] = None) -> int:
        """
        Delete movies matching certain criteria
        
        Args:
            before_date: Delete movies released before this date
            min_rating: Delete movies with rating below this
            min_votes: Delete movies with votes below this
            
        Returns:
            int: Number of movies deleted
        """
        conditions = []
        params = []
        
        if before_date:
            conditions.append("release_date < ?")
            params.append(before_date)
        
        if min_rating is not None:
            conditions.append("vote_average < ?")
            params.append(min_rating)
        
        if min_votes is not None:
            conditions.append("vote_count < ?")
            params.append(min_votes)
        
        if not conditions:
            raise ValueError("At least one deletion criteria must be specified")
        
        where_clause = " AND ".join(conditions)
        
        # First, count movies to be deleted
        count_query = f"SELECT COUNT(*) FROM movies WHERE {where_clause}"
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(count_query, params)
        count = cursor.fetchone()[0]
        
        if count > 0:
            # Confirm deletion
            print(f"⚠️  This will delete {count} movies. Proceeding...")
            
            # Delete movies
            delete_query = f"DELETE FROM movies WHERE {where_clause}"
            cursor.execute(delete_query, params)
            conn.commit()
            print(f"✅ Deleted {count} movies")
        else:
            print("No movies match the deletion criteria")
        
        conn.close()
        return count
    
    # Utility methods
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Total movies
        cursor.execute("SELECT COUNT(*) FROM movies")
        stats['total_movies'] = cursor.fetchone()[0]
        
        # Date range
        cursor.execute("SELECT MIN(release_date), MAX(release_date) FROM movies WHERE release_date IS NOT NULL")
        min_date, max_date = cursor.fetchone()
        stats['date_range'] = {'from': min_date, 'to': max_date}
        
        # Average rating
        cursor.execute("SELECT AVG(vote_average) FROM movies WHERE vote_count > 0")
        stats['average_rating'] = round(cursor.fetchone()[0], 2)
        
        # Most common genres
        cursor.execute("""
            SELECT genre, COUNT(*) as count 
            FROM movies 
            WHERE genre != ''
            GROUP BY genre 
            ORDER BY count DESC 
            LIMIT 5
        """)
        stats['top_genres'] = [{'genre': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Language distribution
        cursor.execute("""
            SELECT original_language, COUNT(*) as count 
            FROM movies 
            GROUP BY original_language 
            ORDER BY count DESC 
            LIMIT 5
        """)
        stats['top_languages'] = [{'language': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        return stats


# Example usage and testing
if __name__ == "__main__":
    # Initialize CRUD object
    crud = MoviesCRUD()
    
    print("Movies Database CRUD Operations")
    print("=" * 50)
    
    # 1. CREATE - Add a new movie
    print("\n1. CREATE - Adding a new movie:")
    new_movie_id = crud.create_movie(
        title="The Matrix Resurrections",
        release_date="2021-12-22",
        overview="Return to a world of two realities: one, everyday life; the other, what lies behind it.",
        popularity=150.5,
        vote_count=1500,
        vote_average=7.5,
        original_language="en",
        genre="Science Fiction, Action",
        poster_url="https://example.com/matrix4.jpg"
    )
    
    # 2. READ - Various read operations
    print("\n2. READ - Fetching movie data:")
    
    # Get by ID
    print(f"\n   a) Get movie by ID {new_movie_id}:")
    movie = crud.get_movie_by_id(new_movie_id)
    if movie:
        print(f"      Title: {movie['title']}, Rating: {movie['vote_average']}")
    
    # Search by title
    print("\n   b) Search movies with 'Spider' in title:")
    spider_movies = crud.get_movies_by_title("Spider")
    for movie in spider_movies[:3]:  # Show first 3
        print(f"      - {movie['title']} ({movie['release_date']})")
    
    # Get by genre
    print("\n   c) Top Action movies:")
    action_movies = crud.get_movies_by_genre("Action", limit=3)
    for movie in action_movies:
        print(f"      - {movie['title']} - Rating: {movie['vote_average']}")
    
    # 3. UPDATE - Update movie data
    print("\n3. UPDATE - Updating movie data:")
    crud.update_movie(new_movie_id, vote_average=8.0, vote_count=2000)
    
    # Add a vote
    print("\n   Adding a new vote:")
    crud.increment_vote(new_movie_id, 9.0)
    
    # 4. DELETE - Delete the test movie
    print("\n4. DELETE - Removing test movie:")
    crud.delete_movie(new_movie_id)
    
    # 5. Statistics
    print("\n5. Database Statistics:")
    stats = crud.get_statistics()
    print(f"   Total movies: {stats['total_movies']}")
    print(f"   Date range: {stats['date_range']['from']} to {stats['date_range']['to']}")
    print(f"   Average rating: {stats['average_rating']}")
    print(f"   Top genres: {', '.join([g['genre'] for g in stats['top_genres'][:3]])}")
    
    print("\n✅ CRUD operations demonstration completed!")
