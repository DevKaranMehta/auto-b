#!/usr/bin/env python3
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            user='n8n_user',
            password='7661607468AAHE5Xc97@123??',
            database='chatwoot_bot'  # Connect to existing database first
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'blockchain_news'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute('CREATE DATABASE blockchain_news')
            print("✅ Database 'blockchain_news' created successfully!")
        else:
            print("ℹ️  Database 'blockchain_news' already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

if __name__ == '__main__':
    create_database()
