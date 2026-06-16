#!/usr/bin/env python3
"""
Discord GitHub URL Scraper (Universal Log Edition)

This script crawls an entire Discord server once and logs every GitHub URL
found across all text, voice, stage, and forum channels/threads. 

It outputs a structured log file containing the timestamp, channel name,
channel type, and the exact matched URL.

Authored by: Gemini (what? it seemed like it knew what it was talking about more)
Poorly reviewed by: Dan Theisen

eat my shorts
"""

import os
import re
from typing import List, Tuple

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

# Loosened regex to capture any subdomains where github.com is the main domain
GITHUB_LOOSE_RE = re.compile(
    r"https?://(?:[a-zA-Z0-9_.-]+\.)*github\.com/[^\s<>]+",
    flags=re.IGNORECASE,
)

# --------------------------------------------------------------------------- #
# Discord Client Setup
# --------------------------------------------------------------------------- #

intents = discord.Intents.default()
intents.message_content = True  # Required to read message text

client = discord.Client(intents=intents)


def extract_clean_urls(content: str) -> List[str]:
    """Extracts GitHub URLs and strips trailing punctuation cleanly."""
    cleaned_urls = []
    for match in GITHUB_LOOSE_RE.finditer(content):
        url = match.group(0)
        # Strip trailing punctuation common at the end of conversational sentences
        while url and url[-1] in ".,;:!?()[]{}'\"":
            url = url[:-1]
        if url:
            cleaned_urls.append(url)
    return cleaned_urls


async def scrape_history(target) -> List[Tuple[str, str, str, str]]:
    """Iterates message history and extracts metadata records."""
    records = []
    try:
        # limit=None pulls everything; discord.py handles rate limits natively
        async for msg in target.history(limit=None):
            if "github.com" in msg.content.lower():
                urls = extract_clean_urls(msg.content)
                for url in urls:
                    timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    channel_name = target.name
                    channel_type = target.type.name  # Clean string representation (e.g. 'text', 'public_thread')
                    records.append((timestamp, channel_name, channel_type, url))
    except discord.Forbidden:
        pass  # Quietly bypass channels the bot lacks permissions to read
    except discord.HTTPException as exc:
        print(f"    ⚠️ Error reading history in {target.name}: {exc}")
    return records


async def process_channel(channel) -> List[Tuple[str, str, str, str]]:
    """Extracts URL records from a parent channel and its nested threads/posts."""
    channel_records = []
    print(f"  • Scanning {channel.type} #{channel.name}")

    # 1. Scrape base channel text (if it holds messages directly and isn't a forum root)
    if hasattr(channel, "history") and not isinstance(channel, discord.ForumChannel):
        channel_records.extend(await scrape_history(channel))

    # 2. Scrape active threads or forum posts
    if hasattr(channel, "threads"):
        for thread in channel.threads:
            channel_records.extend(await scrape_history(thread))

    # 3. Scrape archived public threads/posts
    if hasattr(channel, "fetch_public_archived_threads"):
        try:
            async for thread in channel.fetch_public_archived_threads(limit=None):
                channel_records.extend(await scrape_history(thread))
        except (discord.Forbidden, discord.HTTPException):
            pass

    # 4. Scrape archived private threads
    if hasattr(channel, "fetch_private_archived_threads"):
        try:
            async for thread in channel.fetch_private_archived_threads(limit=None):
                channel_records.extend(await scrape_history(thread))
        except (discord.Forbidden, discord.HTTPException):
            pass

    return channel_records


@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user} (ID: {client.user.id})")
    
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("❌ Guild not found – check your GUILD_ID.")
        await client.close()
        return

    print(f"🔍 Compiling targets for '{guild.name}'...")
    
    # Gather ALL text-bearing channel types supported by Discord
    valid_types = (discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.ForumChannel)
    channels_to_scan = [ch for ch in guild.channels if isinstance(ch, valid_types)]

    all_records = []
    for channel in channels_to_scan:
        records = await process_channel(channel)
        all_records.extend(records)

    # Sort records chronologically by their timestamp string
    all_records.sort(key=lambda x: x[0])

    out_file = "github_urls.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        for timestamp, channel, ch_type, url in all_records:
            # Outputs clean rows separated by pipes for straightforward parsing
            f.write(f"{timestamp} | #{channel} | {ch_type} | {url}\n")

    print(f"\n✅ Finished sweep. Found {len(all_records)} total GitHub URL mentions.")
    print(f"✅ Exported structured data to {out_file}")

    await client.close()


# --------------------------------------------------------------------------- #
# Main Execution Entry Point
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    try:
        client.run(TOKEN)
    except KeyboardInterrupt:
        print("\n❌ Execution canceled by user.")
