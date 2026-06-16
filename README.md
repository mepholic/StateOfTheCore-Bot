# Discord GitHub URL Scraper

A lightweight one‑shot Discord bot that scans a server and extracts every GitHub repository URL mentioned in any message (including forum posts, threads, etc.).  The URLs are stored in `github_urls.txt`.

> **⚠️ Use responsibly** – Only run on servers where you have permission to read all messages.

## wat the fuck am i looking at chat???

This bot is 100% slop and I don't care because I tested it and it seems to do what I want to, and nothing more. I probably looked at a dozen or so of the lines of code closely. First pass was through gpt-oss-4 20b using default parameters in LM studio. Inference on that took 30 minutes and the result was unusable. Pasted results at Gemini free prompt (trial tokens or whatever) and iterated through it on multiple passes, copying and pasting into vim, and committing by hand. I mostly reflected in the git commits with stupid messages that I made throughout the creation of this repository. I don't truly care enough about the discord API to want to understand how it works. I just wanted this little analytical helper tool. I did manage to get a full shell script out of gpt-oss running locally that ran first try, and scaffolded most of the repo, including the ToS and Privacy Policies, which I have reviewed and can confirm I will comply to.

This project may eventually store the Discord User ID's of users who sent Github links to a server this bot is in. I'm still trying to decide if it matters enough to store.

I do plan to spend some real effort on writing some higher quality code to crunch the eventual data collected by this bot. This repo is half shitpost and half personal experiment. I gotta say, I'm mildly surprised at my results. It took me almost as long to decipher all of Discord's bot bullshit (and do their dumbass ID verification... ok whatever I kind of understand... for ur prized api...) as it did to prompt the LLM's and copy-paste shit between bot response and vim, then run a quick manual test on a test discord guild I set up with a bunch of the edge cases related to this code (all the god forsaken different kinds of message types). This shit in the readme that you're reading right now is basically the vast majority of my personal textual contribution to this repository, other than the prompts that were used to get to this point, which will probably be lost to the sands of time. Who cares. the code works. /shruggie 

The whole project maybe took me 5 hours of prompt jockeying (50%) and attempting to manually read discord's docs, and set up all the necessary bot bullshit for the first time (50%). The Discord Bot setup part was more annoying by far.

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

