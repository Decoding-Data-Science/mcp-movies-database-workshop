import os, sys
from os.path import dirname as up

sys.path.append(os.path.abspath(os.path.join(up(__file__), os.pardir)))

from utilities.constants import DB_FILE_PATH, CSV_FILE_PATH

import sqlite3
import pandas as pd


def create_database():
    """Create SQLite database and table"""
    # Connect to database (creates it if it doesn't exist)
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    
    # Drop table if it exists (for fresh import)
    cursor.execute("DROP TABLE IF EXISTS movies")
    
    # Create movies table with appropriate schema
    cursor.execute("""
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
        )
    """)
    
    # Create indexes for better query performance
    cursor.execute("CREATE INDEX idx_title ON movies(title)")
    cursor.execute("CREATE INDEX idx_release_date ON movies(release_date)")
    cursor.execute("CREATE INDEX idx_popularity ON movies(popularity)")
    cursor.execute("CREATE INDEX idx_vote_average ON movies(vote_average)")
    
    conn.commit()
    return conn

def ingest_csv_to_sqlite():
    """Read CSV file and insert data into SQLite database"""
    print(f"Starting ingestion from: {CSV_FILE_PATH}")
    
    # Create database and table
    conn = create_database()
    
    try:
        # Read CSV file with proper quoting configuration
        print("Reading CSV file...")
        
        # First, try to detect the file encoding
        import chardet
        with open(CSV_FILE_PATH, 'rb') as f:
            raw_data = f.read(100000)  # Read first 100KB
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            print(f"Detected encoding: {encoding}")
        
        # Read with detected encoding and proper CSV handling
        df = pd.read_csv(CSV_FILE_PATH, 
                        encoding=encoding or 'utf-8',
                        quotechar='"',
                        on_bad_lines='warn',  # Warn about bad lines
                        engine='python',  # Use Python engine for better error handling
                        skipinitialspace=True)  # Skip spaces after delimiter
        
        # Display info about the dataset
        print(f"\nDataset info:")
        print(f"Total rows: {len(df)}")
        print(f"Columns: {', '.join(df.columns)}")
        
        # Convert Release_Date to proper date format (handling potential errors)
        df['Release_Date'] = pd.to_datetime(df['Release_Date'], errors='coerce')
        
        # Drop rows with missing titles (required field)
        df = df.dropna(subset=['Title'])
        print(f"Rows after dropping missing titles: {len(df)}")
        
        # Handle NaN values for other fields
        df = df.fillna({
            'Overview': '',
            'Popularity': 0.0,
            'Vote_Count': 0,
            'Vote_Average': 0.0,
            'Original_Language': '',
            'Genre': '',
            'Poster_Url': ''
        })
        
        # Rename columns to match database schema
        df_renamed = df.rename(columns={
            'Release_Date': 'release_date',
            'Title': 'title',
            'Overview': 'overview',
            'Popularity': 'popularity',
            'Vote_Count': 'vote_count',
            'Vote_Average': 'vote_average',
            'Original_Language': 'original_language',
            'Genre': 'genre',
            'Poster_Url': 'poster_url'
        })
        
        # Insert data into SQLite
        print("Inserting data into SQLite database...")
        df_renamed.to_sql('movies', conn, if_exists='append', index=False)
        
        # Verify the data was inserted
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM movies")
        count = cursor.fetchone()[0]
        print(f"\nSuccessfully inserted {count} movies into the database!")
        
        # Show sample data
        print("\nSample data from database:")
        cursor.execute("SELECT title, release_date, vote_average FROM movies ORDER BY vote_average DESC LIMIT 5")
        for row in cursor.fetchall():
            print(f"  - {row[0]} ({row[1]}) - Rating: {row[2]}")
        
        # Show database statistics
        cursor.execute("SELECT MIN(release_date), MAX(release_date) FROM movies WHERE release_date IS NOT NULL")
        min_date, max_date = cursor.fetchone()
        print(f"\nDate range: {min_date} to {max_date}")
        
        cursor.execute("SELECT COUNT(DISTINCT original_language) FROM movies")
        lang_count = cursor.fetchone()[0]
        print(f"Number of languages: {lang_count}")
        
        cursor.execute("SELECT COUNT(DISTINCT genre) FROM movies")
        genre_count = cursor.fetchone()[0]
        print(f"Number of unique genre combinations: {genre_count}")
        
    except Exception as e:
        print(f"Error during ingestion: {e}")
        conn.rollback()
    finally:
        conn.close()
        
    print(f"\nDatabase created at: {DB_FILE_PATH}")

def test_queries():
    """Run some test queries to verify the database"""
    print("\n" + "="*50)
    print("Running test queries...")
    print("="*50)
    
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    
    # Test query 1: Top 5 highest rated movies with at least 100 votes
    print("\nTop 5 highest rated movies (min 100 votes):")
    cursor.execute("""
        SELECT title, vote_average, vote_count, release_date 
        FROM movies 
        WHERE vote_count >= 100 
        ORDER BY vote_average DESC 
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]} - Rating: {row[1]} ({row[2]} votes) - Released: {row[3]}")
    
    # Test query 2: Most popular recent movies
    print("\nMost popular movies from 2022:")
    cursor.execute("""
        SELECT title, popularity, release_date 
        FROM movies 
        WHERE release_date >= '2022-01-01' AND release_date < '2023-01-01'
        ORDER BY popularity DESC 
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]} - Popularity: {row[1]:.1f} - Released: {row[2]}")
    
    # Test query 3: Genre distribution
    print("\nTop 10 most common genres:")
    cursor.execute("""
        SELECT genre, COUNT(*) as count 
        FROM movies 
        WHERE genre != ''
        GROUP BY genre 
        ORDER BY count DESC 
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} movies")
    
    conn.close()

if __name__ == "__main__":
    # Check if CSV file exists
    if not os.path.exists(CSV_FILE_PATH):
        print(f"Error: CSV file not found at {CSV_FILE_PATH}")
        exit(1)
    
    # Run the ingestion
    ingest_csv_to_sqlite()
    
    # Run test queries
    test_queries()
    
    print("\n✅ Movie database ingestion completed successfully!")
