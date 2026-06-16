#!/usr/bin/env python3
"""
Discord GitHub URL Scraper (Universal Log Edition)

Crawls a Discord server and captures GitHub URLs across all text, voice, 
stage, and forum channels. Outputs structured timelines with parent-child 
hierarchies for threads and forum posts. Cleans up network loops on exit.
"""

import os
import re
import argparse
import time
import asyncio
from typing import List, Dict, Any

import discord
from dotenv import load_dotenv

# --------------------------------------------------------------------------- #
# Configuration & Argument Parsing
# --------------------------------------------------------------------------- #

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

if not TOKEN:
    raise ValueError("DISCORD_TOKEN not set in .env")
if GUILD_ID == 0:
    raise ValueError("GUILD_ID not set or invalid in .env")

GITHUB_LOOSE_RE = re.compile(
    r"https?://(?:[a-zA-Z0-9_.-]+\.)*github\.com/[^\s<>]+",
    flags=re.IGNORECASE,
)

# --------------------------------------------------------------------------- #
# Core Logic & Helper Functions
# --------------------------------------------------------------------------- #

def extract_clean_urls(content: str) -> List[str]:
    """Extracts GitHub URLs and strips trailing punctuation cleanly."""
    cleaned_urls = []
    for match in GITHUB_LOOSE_RE.finditer(content):
        url = match.group(0)
        while url and url[-1] in ".,;:!?()[]{}'\"":
            url = url[:-1]
        if url:
            cleaned_urls.append(url)
    return cleaned_urls


def determine_detailed_type(target) -> str:
    """Distinguishes regular text channel threads from forum posts."""
    if isinstance(target, discord.Thread):
        if isinstance(target.parent, discord.ForumChannel):
            return "forum_post"
        return "text_thread" if target.type == discord.ChannelType.public_thread else "private_thread"
    return target.type.name


async def scrape_history(target, include_id: bool, parent_name: str = None) -> List[Dict[str, Any]]:
    """Iterates message history and extracts metadata records."""
    records = []
    try:
        async for msg in target.history(limit=None):
            if "github.com" in msg.content.lower():
                urls = extract_clean_urls(msg.content)
                for url in urls:
                    # Apply nested path hierarchy format if dealing with a thread/post
                    channel_display = f"{parent_name}>{target.name}" if parent_name else target.name
                    
                    item = {
                        "timestamp": msg.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        "channel": channel_display,
                        "type": determine_detailed_type(target),
                        "url": url
                    }
                    if include_id:
                        item["author_id"] = str(msg.author.id)
                    records.append(item)
    except discord.Forbidden:
        pass  
    except discord.HTTPException as exc:
        print(f"    ⚠️ Error reading history in {target.name}: {exc}")
    return records

# --------------------------------------------------------------------------- #
# Custom Discord Client
# --------------------------------------------------------------------------- #

class ScraperClient(discord.Client):
    def __init__(self, include_id: bool, **kwargs):
        super().__init__(**kwargs)
        self.include_id = include_id
        self.start_time = None

    async def close(self):
        """Overrides client closure to properly shut down and mute lingering network connectors."""
        try:
            # Set a loop exception handler to silence benign aiohttp teardown complaints
            loop = asyncio.get_running_loop()
            def clean_exit_handler(loop, context):
                msg = context.get("message", "")
                if "Unclosed connector" in msg or "Unclosed connection" in msg:
                    return
                loop.default_exception_handler(context)
            loop.set_exception_handler(clean_exit_handler)
        except RuntimeError:
            pass

        # Perform the base client teardown sequence
        await super().close()
        
        # Give the event loop a moment to cycle out lingering network sockets
        await asyncio.sleep(0.5)

    async def process_channel(self, channel) -> List[Dict[str, Any]]:
        """Extracts records from a parent channel and explicitly logs thread navigation."""
        channel_records = []
        print(f"  • Scanning {channel.type} #{channel.name}")

        # 1. Base channel text 
        if hasattr(channel, "history") and not isinstance(channel, discord.ForumChannel):
            channel_records.extend(await scrape_history(channel, self.include_id))

        # 2. Active threads / forum posts
        if hasattr(channel, "threads") and channel.threads:
            for thread in channel.threads:
                print(f"    -> Entering active {'post' if channel.type == discord.ChannelType.forum else 'thread'}: #{thread.name}")
                channel_records.extend(await scrape_history(thread, self.include_id, parent_name=channel.name))

        # 3. Archived public threads/posts
        if hasattr(channel, "fetch_public_archived_threads"):
            try:
                async for thread in channel.fetch_public_archived_threads(limit=None):
                    print(f"    -> Entering archived public {'post' if channel.type == discord.ChannelType.forum else 'thread'}: #{thread.name}")
                    channel_records.extend(await scrape_history(thread, self.include_id, parent_name=channel.name))
            except (discord.Forbidden, discord.HTTPException):
                pass

        # 4. Archived private threads
        if hasattr(channel, "fetch_private_archived_threads"):
            try:
                async for thread in channel.fetch_private_archived_threads(limit=None):
                    print(f"    -> Entering archived private thread: #{thread.name}")
                    channel_records.extend(await scrape_history(thread, self.include_id, parent_name=channel.name))
            except (discord.Forbidden, discord.HTTPException):
                pass

        return channel_records

    async def on_ready(self):
        self.start_time = time.perf_counter()
        print(f"✅ Logged in as {self.user} (ID: {self.user.id})")
        
        guild = self.get_guild(GUILD_ID)
        if not guild:
            print("❌ Guild not found – check your GUILD_ID.")
            await self.close()
            return

        print(f"🔍 Compiling targets for '{guild.name}'...")
        
        # Categorize channels into structural blocks for isolated metric analysis
        channel_groups = {
            "Text Channels": [ch for ch in guild.channels if isinstance(ch, discord.TextChannel)],
            "Forum Channels": [ch for ch in guild.channels if isinstance(ch, discord.ForumChannel)],
            "Voice Channels": [ch for ch in guild.channels if isinstance(ch, discord.VoiceChannel)],
            "Stage Channels": [ch for ch in guild.channels if isinstance(ch, discord.StageChannel)]
        }

        all_records = []

        # Process each channel block dynamically
        for group_label, channels in channel_groups.items():
            if not channels:
                continue
                
            print(f"\n📂 Processing Group: {group_label}")
            group_subtotal = 0
            
            for channel in channels:
                records = await self.process_channel(channel)
                all_records.extend(records)
                group_subtotal += len(records)
                
            print(f"📊 Subtotal for {group_label}: {group_subtotal} matches found.")

        # Final sorting index based chronologically on timestamps
        all_records.sort(key=lambda x: x["timestamp"])

        out_file = "github_urls.txt"
        with open(out_file, "w", encoding="utf-8") as f:
            for r in all_records:
                if self.include_id:
                    f.write(f"{r['timestamp']} | {r['author_id']} | #{r['channel']} | {r['type']} | {r['url']}\n")
                else:
                    f.write(f"{r['timestamp']} | #{r['channel']} | {r['type']} | {r['url']}\n")

        print(f"\n✅ Finished sweep. Found {len(all_records)} total GitHub URL mentions.")
        print(f"✅ Exported structured data to {out_file}")

        # Benchmark processing speed
        elapsed_time = time.perf_counter() - self.start_time
        print(f"⏱️ Total execution wall-clock time: {elapsed_time:.2f} seconds")

        await self.close()

# --------------------------------------------------------------------------- #
# Main Execution Entry Point
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Discord Server GitHub URL Extraction Tool")
    parser.add_argument(
        "--include-id", 
        action="store_true", 
        help="Include the message sender's Discord ID in the final export schema."
    )
    args = parser.parse_args()

    intents = discord.Intents.default()
    intents.message_content = True  

    client = ScraperClient(include_id=args.include_id, intents=intents)
    
    try:
        client.run(TOKEN)
    except KeyboardInterrupt:
        print("\n❌ Execution terminated via user keyboard break.")

