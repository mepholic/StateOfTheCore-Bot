#!/usr/bin/env python3
"""
Script 1: Discord Incremental Scraper (Database Engine)
Crawls Discord channels and threads incrementally, logging new findings to SQLite.
"""

import os
import re
import argparse
import time
import asyncio
import sqlite3
from typing import List, Dict, Any

import discord
from dotenv import load_dotenv

# --------------------------------------------------------------------------- #
# Configuration & Setup
# --------------------------------------------------------------------------- #

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))
DB_PATH = "github_scraper.db"

if not TOKEN or GUILD_ID == 0:
    raise ValueError("Ensure DISCORD_TOKEN and GUILD_ID are configured in .env")

GITHUB_LOOSE_RE = re.compile(
    r"https?://(?:[a-zA-Z0-9_.-]+\.)*github\.com/[^\s<>]+",
    flags=re.IGNORECASE,
)

# --------------------------------------------------------------------------- #
# Database Initialization
# --------------------------------------------------------------------------- #

def init_db():
    """Sets up the tracking and storage schema with a nullable author_id."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Main storage table (author_id is explicitly allowed to be NULL)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mentions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                author_id INTEGER NULL,
                channel_name TEXT,
                channel_type TEXT,
                url TEXT,
                timestamp TEXT,
                UNIQUE(message_id, url)
            );
        """)
        # State tracking table for incremental resume
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channel_state (
                channel_id INTEGER PRIMARY KEY,
                last_message_id INTEGER
            );
        """)
        conn.commit()


def get_last_message_id(channel_id: int) -> int:
    """Retrieves the last processed message checkpoint for a specific channel/thread."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT last_message_id FROM channel_state WHERE channel_id = ?", (channel_id,))
        row = cursor.fetchone()
        return row[0] if row else None


def save_records(records: List[Dict[str, Any]], channel_id: int, max_msg_id: int):
    """Saves newly discovered URLs and updates the channel's crawl checkpoint state."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        if records:
            cursor.executemany("""
                INSERT OR IGNORE INTO mentions (message_id, author_id, channel_name, channel_type, url, timestamp)
                VALUES (:message_id, :author_id, :channel_name, :channel_type, :url, :timestamp)
            """, records)
            
        if max_msg_id:
            cursor.execute("""
                INSERT INTO channel_state (channel_id, last_message_id)
                VALUES (?, ?)
                ON CONFLICT(channel_id) DO UPDATE SET last_message_id = excluded.last_message_id
            """, (channel_id, max_msg_id))
            
        conn.commit()

# --------------------------------------------------------------------------- #
# Core Processing Logic
# --------------------------------------------------------------------------- #

def extract_clean_urls(content: str) -> List[str]:
    """Extracts GitHub URLs and strips trailing conversational punctuation."""
    cleaned_urls = []
    for match in GITHUB_LOOSE_RE.finditer(content):
        url = match.group(0)
        while url and url[-1] in ".,;:!?()[]{}'\"":
            url = url[:-1]
        if url:
            cleaned_urls.append(url)
    return cleaned_urls


def determine_detailed_type(target) -> str:
    if isinstance(target, discord.Thread):
        if isinstance(target.parent, discord.ForumChannel):
            return "forum_post"
        return "text_thread" if target.type == discord.ChannelType.public_thread else "private_thread"
    return target.type.name


async def scrape_history(target, include_id: bool, parent_name: str = None) -> int:
    """Iterates message history from the last checkpoint, saves data, and returns record count."""
    last_id = get_last_message_id(target.id)
    history_kwargs = {"limit": None}
    
    if last_id:
        history_kwargs["after"] = discord.Object(id=last_id)
        
    records = []
    max_seen_id = last_id or 0
    
    try:
        async for msg in target.history(**history_kwargs):
            max_seen_id = max(max_seen_id, msg.id)
            if "github.com" in msg.content.lower():
                urls = extract_clean_urls(msg.content)
                for url in urls:
                    records.append({
                        "message_id": msg.id,
                        # Fallback to None (SQL NULL) if include_id is disabled
                        "author_id": msg.author.id if include_id else None,
                        "channel_name": f"{parent_name}>{target.name}" if parent_name else target.name,
                        "channel_type": determine_detailed_type(target),
                        "url": url,
                        "timestamp": msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    })
    except discord.Forbidden:
        return 0  
    except discord.HTTPException as exc:
        print(f"    ⚠️ Error streaming history in {target.name}: {exc}")
        return 0

    if records or max_seen_id > (last_id or 0):
        save_records(records, target.id, max_seen_id)
        
    return len(records)

# --------------------------------------------------------------------------- #
# Discord Bot Runtime Client
# --------------------------------------------------------------------------- #

class ScraperBot(discord.Client):
    def __init__(self, include_id: bool, **kwargs):
        super().__init__(**kwargs)
        self.include_id = include_id
        self.start_time = None
        self.total_new_matches = 0

    async def close(self):
        try:
            loop = asyncio.get_running_loop()
            loop.set_exception_handler(lambda l, c: None if "Unclosed" in c.get("message", "") else l.default_exception_handler(c))
        except RuntimeError:
            pass
        await super().close()
        await asyncio.sleep(0.5)

    async def process_channel(self, channel) -> int:
        count = 0
        print(f"  • Scanning {channel.type} #{channel.name}")

        if hasattr(channel, "history") and not isinstance(channel, discord.ForumChannel):
            count += await scrape_history(channel, self.include_id)

        if hasattr(channel, "threads") and channel.threads:
            for thread in channel.threads:
                print(f"    -> Entering active {'post' if channel.type == discord.ChannelType.forum else 'thread'}: #{thread.name}")
                count += await scrape_history(thread, self.include_id, parent_name=channel.name)

        if hasattr(channel, "fetch_public_archived_threads"):
            try:
                async for thread in channel.fetch_public_archived_threads(limit=None):
                    print(f"    -> Entering archived public {'post' if channel.type == discord.ChannelType.forum else 'thread'}: #{thread.name}")
                    count += await scrape_history(thread, self.include_id, parent_name=channel.name)
            except (discord.Forbidden, discord.HTTPException):
                pass

        if hasattr(channel, "fetch_private_archived_threads"):
            try:
                async for thread in channel.fetch_private_archived_threads(limit=None):
                    print(f"    -> Entering archived private thread: #{thread.name}")
                    count += await scrape_history(thread, self.include_id, parent_name=channel.name)
            except (discord.Forbidden, discord.HTTPException):
                pass

        return count

    async def on_ready(self):
        self.start_time = time.perf_counter()
        print(f"✅ Logged in as {self.user} (ID: {self.user.id})")
        
        guild = self.get_guild(GUILD_ID)
        if not guild:
            print("❌ Guild not found.")
            await self.close()
            return

        print(f"🔍 Running incremental sync for '{guild.name}' (Fetch User IDs: {self.include_id})...")
        
        channel_groups = {
            "Text Channels": [ch for ch in guild.channels if isinstance(ch, discord.TextChannel)],
            "Forum Channels": [ch for ch in guild.channels if isinstance(ch, discord.ForumChannel)],
            "Voice Channels": [ch for ch in guild.channels if isinstance(ch, discord.VoiceChannel)],
            "Stage Channels": [ch for ch in guild.channels if isinstance(ch, discord.StageChannel)]
        }

        for group_label, channels in channel_groups.items():
            if not channels:
                continue
            print(f"\n📂 Processing Group: {group_label}")
            group_subtotal = 0
            for channel in channels:
                matched = await self.process_channel(channel)
                group_subtotal += matched
            print(f"📊 Subtotal for {group_label}: {group_subtotal} *new* matches added to DB.")
            self.total_new_matches += group_subtotal

        print(f"\n✅ Sync Complete. Captured {self.total_new_matches} new links this run.")
        print(f"⏱️ Total execution wall-clock time: {time.perf_counter() - self.start_time:.2f} seconds")
        await self.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Discord Server GitHub URL Extraction Tool")
    parser.add_argument(
        "--include-id", 
        action="store_true", 
        help="Fetch and store the message sender's Discord ID in the local database database."
    )
    args = parser.parse_args()

    init_db()
    intents = discord.Intents.default()
    intents.message_content = True  
    bot = ScraperBot(include_id=args.include_id, intents=intents)
    bot.run(TOKEN)

