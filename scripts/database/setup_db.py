import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

def setup_database():
    """Set up the database and tables"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Create database if it doesn't exist
    try:
        conn = psycopg2.connect("dbname=postgres user=postgres password=password host=localhost")
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute("CREATE DATABASE blog_automatic;")
        cur.close()
        conn.close()
        print("✅ Database created successfully!")
    except psycopg2.errors.DuplicateDatabase:
        print("✅ Database already exists")
    except Exception as e:
        print(f"Database creation error: {e}")
    
    # Import models and create tables
    try:
        from app.models.blog import Base as BlogBase
        from app.models.newsletter import Base as NewsletterBase
        
        engine = create_engine(DATABASE_URL)
        BlogBase.metadata.create_all(bind=engine)
        NewsletterBase.metadata.create_all(bind=engine)
        print("✅ Tables created successfully!")
    except Exception as e:
        print(f"Table creation error: {e}")

if __name__ == "__main__":
    setup_database()
