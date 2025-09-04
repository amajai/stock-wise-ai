from langchain.chat_models import init_chat_model 
from datetime import datetime
import sqlite3

import os
from dotenv import load_dotenv

load_dotenv()


def create_llm():
    provider = os.getenv("LLM_PROVIDER", "google_genai")
    model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))

    return init_chat_model(
        model=model,
        model_provider=provider,
        temperature=temperature
    )

def get_today_str() -> str:
    """Get current date in a human-readable format."""
    return datetime.now().strftime("%a %b %-d, %Y")

def get_currency_config():
    """Get currency configuration"""
    # You can modify this or make it configurable via environment variables
    currency_configs = {
        "naira": {
            "name": "Naira (₦)",
            "symbol": "₦",
            "example": "₦15,999"
        },
        "dollar": {
            "name": "US Dollar ($)",
            "symbol": "$", 
            "example": "$15.99"
        },
        "pound": {
            "name": "British Pound (£)",
            "symbol": "£",
            "example": "£12.99"
        }
    }
    
    # Default to naira, or get from environment
    currency_type = os.getenv("CURRENCY_TYPE", "naira").lower()
    return currency_configs.get(currency_type, currency_configs["naira"])

def init_db():
    """Initialize database and create tables if they don't exist"""
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    
    # Create inventory table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT UNIQUE NOT NULL,
            quantity INTEGER DEFAULT 0,
            price REAL DEFAULT 0.0,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create sales table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            quantity_sold INTEGER NOT NULL,
            sale_date TEXT NOT NULL,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_all_items():
    "Get all inventory items from db"
    init_db()  # Ensure db and tables exist
    
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()

    items_list = [name[0] for name in cursor.execute('''
    SELECT product_name FROM inventory;
    ''').fetchall()]

    conn.commit()
    conn.close()

    return items_list
    