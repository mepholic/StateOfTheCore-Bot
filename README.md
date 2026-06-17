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

This project may eventually store the Discord User ID's of users who sent Github links to a server this bot is in. I'm still trying to decide if it matters enough to store.

---

# SKILLS.md
## ok what the fuck am I looking at here

My professional background includes network engineering (expired (bragging rights) ccna, but also currently emplyed sr. neteng), software escalations support and quality assurance (working weird customer bugs for swdev teams, and writing+debugging+correcting+validating integraion/unit test suites), a fuckload of sysops/devops/sre background (previous aws ops experience, etc), pentensting (and some defensive cybersec), a bit of systems design and arcitecture, and even less software development experience.

I do plan to spend some real effort on writing some higher quality code to crunch the eventual data collected by this bot. This repo is half shitpost and half personal experiment. I'm not really known for posting code that I care about publically, because that stuff is my own personal artwork, for my own walls to bear (there's not literally code written on the walls of my house you psychopath)

The whole project maybe took me 5 hours of prompt jockeying (50%) and attempting to manually read discord's docs, and set up all the necessary bot bullshit for the first time (50%). The Discord Bot setup part was by far the more annoying part of this project. (I guess all I'm saying is that I guess I'd rather be an agentic llm executor bot than an official discord docs injestor)

This shit below here in the readme that you might actually be reading right now is basically the vast majority of my personal textual contribution to this repository, other than the prompts that were used to get to this point in the codebase, via various models, the exact history of which will probably be lost to the sands of time.

(caveat to consider when reading this: most of my prompts had some of my own software engineering background wisdom encoded into it. the "error" factor introduced by my own internalized biases are difficult for me to measure against the "generally executive public" or whoever else the intended audience of these marketing campaigns is.)

_they will always continue to try to tell their business normies that this will replace thir software engineers with them like cobol did in the 60's /j **(/j specifier qualifier: I only added these two characters because most of the people who are old enough to get this joke are also dried out enough to shatter upon exposure to it unless these two specific mythical symbols are added, for some godforsaken reason; anyways <3 to the oldhats, 𒈙 to the newfags 😜)**_

## The concept of this repo 

This bot is 100% slop and I don't care because I tested it and it seems to do what I want to, and nothing more. All I want is a bot that scrapes all github links in all text channels out of a server that it's in. Most of the "emotional flair" you see in this repo is my own, and is best looked at as sarcastic internal monologue with myself as I was shuffling data between webpage or even LMStudio chat windows and terminal windows, writing whole output files over each other, and rerunning them in the venv, pasting output back at the bot and basically just saying "fix it" every time it threw an error.

_**"im blackboxing here???"** -- written by: jesus christ it finally makes sense_

I followed this pattern until the initial prompt project scope was mostly fulfilled by my own standards, based mostly on testing results:
```
Generate a simple repository using the best suited language, APIs or Discord integrations whose intention is to act as a one-shot Discord server scraper to gather all github repository urls mentioned in any chat, channel, post, thread, forum, topic, or other form of discord communication.
```
and then upon encountering first bot to market (read: my own sample set) with the brillintly not failing everywhere solution, I went on to refine logging a bit more via prompt (because I hope to run this against larger discord guilds some day, actually lol, like really actually unironically here), and finally storing context persistantly between scrapes to an sqlite database, along with some sort of key to pick up where it last scraped from in a thread/channel/whatever context since last "run".

_fuck it y'all I know bots are supposed to be "services that just listen and react" or whatever your brain abstracted it to, but we're batch processing up in this biznitch now._

Betweeen all this, I burned many cycles via iterative prompting (like 30 minutes) trying to further "optimize" the code to use `discord search api`, rather than just scraping everything. Scraping an entire guild rather than searching for the shit I care about specifically seems super ineffient for code. `Search` seemed like an obvious answer to reduce api calls to discord for this this specific problem, however, based on my bot prompt interactions, it seems like DISCORD BOTS themselves, even if IDENTITY VALIDATED BY STRIPE ADMINS or whatever the fuck shit I had to go through to even get the goddamned discord bot token in the first place, are fucking BANNED from using the search api.

_ok, fine. fucking WHATEVER..._ I just did what the bot said I should and stopped worrying about how dumb that seems. I didn't even check, because it seemed too dumb to believe, and I don't want to know the real answer because I'm guessing they just scaled too big and now disallowing automated searching of their platform because it is too costly for them to sustain.

Seems like the generalized globo-economic enshittification isn't _just_ my own creation at least!

_a discord dev probably: **"but it's a good abstraction"**_

## my experience

_**"if the code does what we want do we really care why??"** /shruggie_  ->▪️<-

First real pass of the above prompt was through gpt-oss-4 20b using default parameters in LM studio; Ryzen 3900X+64GB DDR4(1400MHz?)+RTX2070 local hardware inference, which took 30 minutes and the results were unusable. Didn't run, barely even linted.

I made some attempts of working with the OpenAI default homepage chatbot, and got about equally (non)functional code. I tried iterating on both the output of gpt-oss-4 (local model), and the original prompt without further success.

My most successful "next step" came after pasting the original local-model hallucinated bullshit at a Gemini free prompt (trial tokens or whatever). Gemini screamed about invalid utilization of the underlying API. I iterated iterated through it on multiple {prompt, copy-paste, run command, return results to bot} cycles, and then committed by hand when something did "the thing" without me needing to look too hard (mostly comparing outputs, rather than bot slop code, against my own expecatations) and just manually being the human "agent" to run commands for it or whatever for a while.

From my point of view, each set of bot prompt results that ended in running code (without egregious failure) that furthered the hyperspecific goal of this project (to just scrape github urls from discord servers along with some surrounding context) ended up being committed. The content of the commit messages clearly doesn't matter since I wrote them myself(!)

#### (brief) FUUUUUUCK (interlude)
To be clear, this is not an advertisement of Gemini, and it was my first time using their cloud model chat ui thingy. Worked better than the local and remote OpenAI chatbots I tried it against at least.

I probably looked at a dozen or three lines of code closely while building this, and those lines existed in in the discord.py github repository. The code primarly pertained to the... like.. 6 different types of text channels that discord has and the weird container relationships between some of them, cause wot the absolute fok. I used this manually gathered "context" to feed to Gemini in order to draw the rest of the fucking owl, because the local model, the openai homepage bot, and gemini (initially) got stuck on this.

Anyways... I don't truly care enough about the discord API to want to understand how it works. I just wanted this little analytical dataset collector tool. The effort I spent on researching (and then documenting) the last paragraph was excruciating despite being a fraction of the overall "work".

## anyways I digress...

Gemini regular webui chat prompt got me to a first deliverable of "can dump useful bullshit 2 text file" without having to do much more than `Ctrl-c` `Alt-Tab` "`vim filename.piss`" "`dG`" "`i`" `Shift-Insert` "`:q`" `python filename.piss` `Alt-Tab` for each iteration.

_**iykyk**, however if you don't know but pay close attention, you can actually learn how to exit vim from that last idiotic line of text_

Once I got there I was like "go better logging and sqlite backend with restore from last run position" and it was basically just like:
<img width="400" height="260" alt="image" src="https://github.com/user-attachments/assets/2e7ab28d-63d0-4d03-8d4c-f640f2f729af" />

I also checked the SQLite schema after one of my "final" prompts to make sure it was at least semi-sane. I wouldn't build a database schema like the bot did, but I can understand why and how the schema works based on what I told the thing to do. I inspected the generarted database with `sqlite` rather than looking at the code, because it was like 3 commands that I was easily able to find in the sqlite cli help. Why would I look at code anyways? I'm not getting paid for this...

# Summary

I gotta say, I'm mildly surprised at my results. It took me almost as long to decipher all of Discord's bot bullshit (and do their dumbass ID verification... ok whatever I kind of understand... for ur prized api...) as it did to prompt the LLM's and copy-paste shit between bot response and vim, then run a quick manual test on a test discord guild I set up with a bunch of the edge cases related to this code.

## Conclusion
I guess I'd rather be a damn inference bot's little agent bitch rather than a Discord™️anything. Also read your code and test it too (eat your god damned wheaties and like it)

In short:

    "Eat your Wheaties" is a motivating phrase urging someone to muster their strength, prepare, and be ready for an upcoming challenge.
  _Pirated from some place who already fell out of my tab buffer._

**_prediction that this text will be estimated as precisely an 87.3003003% proability of being an AI-generated work of art_**

**if you're offended by any of this for any reason, I cordially invite you to eat my complete _(fully rendered)_ asshole.**
    >Prove Me Wrong<_ -> _as the man with the sign says._

I'm not even sure I proved anything to myself here.

_also my mental health is fine, thanks for asking_

`this is not meant to be conclusory, stop pretending it ever was. closure is for wimps.`

I was absolutely right the whole time!!!!

ah fuck
