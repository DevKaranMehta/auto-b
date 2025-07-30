import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from sqlalchemy import text

def fix_meta_description_length():
    """Fix meta_description field length in PostgreSQL"""
    try:
        db = SessionLocal()
        
        # Check current column length
        result = db.execute(text("""
            SELECT character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'blogs' AND column_name = 'meta_description'
        """))
        current_length = result.fetchone()
        
        if current_length:
            print(f"📊 Current meta_description length: {current_length[0]}")
        
        # Increase meta_description length to 300 characters
        db.execute(text("ALTER TABLE blogs ALTER COLUMN meta_description TYPE VARCHAR(300)"))
        
        # Also increase meta_keywords length to handle longer keywords
        db.execute(text("ALTER TABLE blogs ALTER COLUMN meta_keywords TYPE VARCHAR(500)"))
        
        db.commit()
        print("✅ Database schema updated:")
        print("   • meta_description: VARCHAR(300)")
        print("   • meta_keywords: VARCHAR(500)")
        
        # Verify the changes
        result = db.execute(text("""
            SELECT column_name, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'blogs' AND column_name IN ('meta_description', 'meta_keywords')
        """))
        
        columns = result.fetchall()
        for column in columns:
            print(f"   ✅ {column[0]}: {column[1]} characters")
        
    except Exception as e:
        print(f"❌ Error fixing database schema: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_meta_description_length()
