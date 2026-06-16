#!/usr/bin/env python3
"""
Discord GitHub URL Scraper (Universal Channel Support)

This script crawls an entire Discord server once and collects every GitHub
repository URL that appears in any text channel, announcement channel, voice 
text chat, stage text chat, thread, or forum post.

It relies on discord.py's native history iterators, which automatically 
manage and respect Discord's rate limits.

Authored by: Gemini (what? it seemed like it knew what it was talking about more)
Poorly reviewed by: Dan Theisen

eat my shorts
"""

import os
import re
from typing import Set

import discord
from dotenv import load_dotenv

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

if not TOKEN:
    raise ValueError("DISCORD_TOKEN not set in .env")
if GUILD_ID == 0:
    raise ValueError("GUILD_ID not set or invalid in .env")

# Clean regex to target valid GitHub repository URLs
GITHUB_RE = re.compile(
    r"https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)",
    flags=re.IGNORECASE,
)

# --------------------------------------------------------------------------- #
# Discord Client Setup
# --------------------------------------------------------------------------- #

intents = discord.Intents.default()
intents.message_content = True  # Crucial for reading message text

client = discord.Client(intents=intents)


def extract_urls(content: str) -> Set[str]:
    """Extracts unique GitHub repository URLs from a text string."""
    return {match.group(0) for match in GITHUB_RE.finditer(content)}


async def scrape_history(target) -> Set[str]:
    """Iterates through the message history of any readable text target."""
    urls = set()
    try:
        # limit=None pulls everything; discord.py handles 429 rate limits natively
        async for msg in target.history(limit=None):
            if "github.com" in msg.content.lower():
                urls.update(extract_urls(msg.content))
    except discord.Forbidden:
        pass  # Quietly bypass channels the bot doesn't have permissions to read
    except discord.HTTPException as exc:
        print(f"    ⚠️ Error reading history in {target.name}: {exc}")
    return urls


async def process_channel(channel) -> Set[str]:
    """Extracts URLs from a parent channel and any nested threads/posts."""
    urls = set()
    print(f"  • Scanning {channel.type} #{channel.name}")

    # 1. Scrape base channel text (if it can hold messages directly)
    if hasattr(channel, "history") and not isinstance(channel, discord.ForumChannel):
        urls.update(await scrape_history(channel))

    # 2. Scrape active threads or forum posts
    if hasattr(channel, "threads"):
        for thread in channel.threads:
            urls.update(await scrape_history(thread))

    # 3. Scrape archived public threads/posts
    if hasattr(channel, "fetch_public_archived_threads"):
        try:
            async for thread in channel.fetch_public_archived_threads(limit=None):
                urls.update(await scrape_history(thread))
        except (discord.Forbidden, discord.HTTPException):
            pass

    # 4. Scrape archived private threads
    if hasattr(channel, "fetch_private_archived_threads"):
        try:
            async for thread in channel.fetch_private_archived_threads(limit=None):
                urls.update(await scrape_history(thread))
        except (discord.Forbidden, discord.HTTPException):
            pass

    return urls


@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user} (ID: {client.user.id})")
    
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("❌ Guild not found – check your GUILD_ID.")
        await client.close()
        return

    print(f"🔍 Compiling targets for '{guild.name}'...")
    
    # Gather ALL possible text-bearing channel types supported by Discord
    channels_to_scan = []
    channels_to_scan.extend(guild.text_channels)   # Text & Announcement channels
    channels_to_scan.extend(guild.forum_channels)  # Forum channels
    channels_to_scan.extend(guild.voice_channels)  # Voice text channels
    channels_to_scan.extend(guild.stage_channels)  # Stage text channels

    all_urls = set()
    for channel in channels_to_scan:
        channel_urls = await process_channel(channel)
        all_urls.update(channel_urls)

    # Save results cleanly sorted
    out_file = "github_urls.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        for url in sorted(all_urls):
            f.write(url + "\n")

    print(f"\n✅ Finished sweep. Found {len(all_urls)} unique GitHub URLs.")
    print(f"✅ Exported to {out_file}")

    await client.close()


# --------------------------------------------------------------------------- #
# Main Execution Entry Point
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    try:
        client.run(TOKEN)
    except KeyboardInterrupt:
        print("\n❌ Execution canceled by user.")

