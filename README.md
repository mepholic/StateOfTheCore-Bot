# Discord GitHub URL Scraper

A lightweight one‑shot Discord bot that scans a server and extracts every GitHub repository URL mentioned in any message (including forum posts, threads, etc.).  The URLs are stored in `github_urls.txt`.

> **⚠️ Use responsibly** – Only run on servers where you have permission to read all messages.

## Prerequisites

- Python 3.10+
- A Discord bot token with the following permissions:
  - *Read Messages / View Channel* for the target server.
  - The privileged **MESSAGE_CONTENT** intent enabled in the Discord Developer Portal.

## Setup

```bash
# Clone this repository (or just copy the files)
git clone https://github.com/mepholic/StateOfTheCore_Bot.git
cd StateOfTheCore_Bot

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy the example env file and fill in your data
cp .env.example .env
# Edit .env:
#   DISCORD_TOKEN=YOUR_BOT_TOKEN
#   GUILD_ID=123456789012345678

# Run the bot
python main.py
```

After the run, `github_urls.txt` will contain one URL per line.

## License

WTFPL – see the [LICENSE](LICENSE) file. See also: https://www.wtfpl.net/

## Terms of Service & Privacy Policy

See the attached `TERMS_OF_SERVICE.md` and `PRIVACY_POLICY.md` for legal details.

---

