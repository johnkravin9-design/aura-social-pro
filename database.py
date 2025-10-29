import sqlite3
import os
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect('aura_social.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    # Users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            display_name TEXT,
            bio TEXT,
            avatar TEXT DEFAULT '👤',
            created_at TEXT
        )
    ''')
    
    # Posts table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT,
            likes INTEGER DEFAULT 0,
            loves INTEGER DEFAULT 0,
            laughs INTEGER DEFAULT 0,
            wows INTEGER DEFAULT 0,
            username TEXT,
            display_name TEXT,
            avatar TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

def migrate_from_memory():
    """Migrate data from in-memory storage to database"""
    from main import users_db, posts_db
    
    conn = get_db_connection()
    
    # Migrate users
    for username, user in users_db.items():
        conn.execute('''
            INSERT OR REPLACE INTO users (id, username, email, password, display_name, bio, avatar, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user.id, user.username, user.email, user.password, user.display_name, user.bio, user.avatar, user.created_at))
    
    # Migrate posts
    for post in posts_db:
        conn.execute('''
            INSERT OR REPLACE INTO posts (id, user_id, content, timestamp, likes, username, display_name, avatar)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (post.id, post.user_id, post.content, post.timestamp, post.likes, post.username, post.display_name, post.avatar))
    
    conn.commit()
    conn.close()
    print("✅ Data migrated to database successfully!")

if __name__ == '__main__':
    init_db()
    migrate_from_memory()
