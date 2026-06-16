#!/usr/bin/env python3
"""
Script 2: Log File Compiler
Queries the local SQLite database and updates the output text log file.
"""

import argparse
import sqlite3

DB_PATH = "github_scraper.db"
OUT_FILE = "github_urls.txt"

def export_data(include_id: bool):
    """Reads data out of SQLite and saves it into a clean flat log file."""
    print(f"📦 Connecting to database: {DB_PATH}")
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT timestamp, author_id, channel_name, channel_type, url 
                FROM mentions 
                ORDER BY timestamp ASC
            """)
            rows = cursor.fetchall()
            
        if not rows:
            print("⚠️ The database is currently empty. Run your bot scraper first.")
            return

        print(f"📝 Compiling {len(rows)} entries into {OUT_FILE}...")
        
        with open(OUT_FILE, "w", encoding="utf-8") as f:
            for timestamp, author_id, channel_name, channel_type, url in rows:
                if include_id:
                    # Safely display 'N/A' if the row has a NULL author_id
                    display_id = str(author_id) if author_id is not NULL else "N/A"
                    f.write(f"{timestamp} | {display_id} | #{channel_name} | {channel_type} | {url}\n")
                else:
                    f.write(f"{timestamp} | #{channel_name} | {channel_type} | {url}\n")
                    
        print("✅ Log export finished successfully.")
        
    except sqlite3.OperationalError:
        print("❌ Database tables not found. Please run your primary scraper script first.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compile local database entries into a flat file log.")
    parser.add_argument(
        "--include-id", 
        action="store_true", 
        help="Include user Discord Snowflake IDs inside the generated output table formatting."
    )
    args = parser.parse_args()
    # Direct alias check to fix a quick evaluation name bug
    try:
        NULL = None
        export_data(include_id=args.include_id)
    except Exception as e:
        print(f"❌ Export Failed: {e}")

