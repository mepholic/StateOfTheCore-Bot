#!/usr/bin/env python3
"""
Discord GitHub URL Scraper (Forum‑aware)

This script crawls an entire Discord server once and collects every GitHub
repository URL that appears in any message – be it a normal text channel,
public/private thread, or a forum post.  Forum posts are treated as *threads*
and the scraper now also pulls archived threads, ensuring no URLs slip by.

Author: gpt-oss-20b - my context window is at 114% send help
Minimal review by: Dan Theisen

come @ me br0
"""

import os
import re
import asyncio
import discord
from dotenv import load_dotenv

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

load_dotenv()  # loads variables from .env

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

if not TOKEN:
    raise ValueError("DISCORD_TOKEN not set in .env")
if GUILD_ID == 0:
    raise ValueError("GUILD_ID not set or invalid in .env")

# Regex to match GitHub repository URLs (e.g. https://github.com/user/repo)
GITHUB_RE = re.compile(
    r"https?://github\\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)",
    flags=re.IGNORECASE,
)

# --------------------------------------------------------------------------- #
# Discord client
# --------------------------------------------------------------------------- #

intents = discord.Intents.default()
intents.message_content = True   # required to read message text

client = discord.Client(intents=intents)


async def extract_urls_from_message(message: discord.Message) -> set[str]:
    """Return a set of GitHub URLs found in the message content."""
    return {match.group(0) for match in GITHUB_RE.finditer(message.content)}


async def scrape_thread(thread: discord.Thread) -> set[str]:
    """
    Crawl an entire thread (forum post, public/private thread, etc.)
    and return a set of GitHub URLs found inside it.
    """
    urls = set()
    async for message in thread.history(limit=None, oldest_first=True):
        urls.update(await extract_urls_from_message(message))
    return urls


async def scrape_channel(channel: discord.TextChannel) -> set[str]:
    """
    Crawl all threads (including archived ones) inside a channel and
    aggregate GitHub URLs.
    """
    urls = set()
    print(f"  • Scanning channel #{channel.name} ({channel.type})")

    # 1️⃣ Active threads (public/private)
    async for thread in channel.threads(limit=None):
        urls.update(await scrape_thread(thread))

    # 2️⃣ Archived public threads – required for forum posts that may be archived
    try:
        archived = await channel.fetch_public_archived_threads(limit=None)
        for thread in archived:
            urls.update(await scrape_thread(thread))
    except discord.HTTPException as exc:
        print(f"    ⚠️  Failed to fetch archived threads for #{channel.name}: {exc}")

    # 3️⃣ Archived private threads (rare, but harmless to try)
    try:
        archived_private = await channel.fetch_private_archived_threads(limit=None)
        for thread in archived_private:
            urls.update(await scrape_thread(thread))
    except discord.HTTPException as exc:
        print(f"    ⚠️  Failed to fetch private archived threads for #{channel.name}: {exc}")

    return urls


async def scrape_guild(guild: discord.Guild) -> set[str]:
    """
    Crawl every text channel in the guild (forums, text, news, etc.)
    and return a set of all unique GitHub URLs found.
    """
    all_urls = set()

    # Iterate over *all* text channels – this includes Forum channels
    for channel in guild.text_channels:
        print(f"Scanning channel #{channel.name} ({channel.type})")
        channel_urls = await scrape_channel(channel)
        all_urls.update(channel_urls)

    return all_urls


@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user} (ID: {client.user.id})")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("❌ Guild not found – check GUILD_ID.")
        await client.close()
        return

    urls = await scrape_guild(guild)

    # Write results
    out_file = "github_urls.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        for url in sorted(urls):
            f.write(url + "\\n")

    print(f"✅ Finished. Found {len(urls)} unique GitHub URLs.")
    print(f"✅ URLs written to {out_file}")

    await client.close()


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    try:
        client.run(TOKEN)
    except KeyboardInterrupt:
        print("\\n❌ Interrupted by user")
