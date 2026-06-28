# Discord Bot Boilerplate

A clean Python Discord bot boilerplate using [discord.py v2](https://discordpy.readthedocs.io/) with a full **ticket system**.

## Features

- Cog-based architecture for clean command organization
- `/` command prefix (configurable)
- Built-in error handling
- Three starter cogs: `general`, `moderation`, and `tickets`

### Ticket System
- `Open Ticket` panel button — creates a private channel per user
- `Close Ticket` button with reason modal → auto-deletes channel after 5 s
- `Claim` button so a staff member can take ownership
- Transcript saved as `.txt` and posted to a log channel on close
- `/add` and `/remove` to manage members in a ticket
- `/rename` to rename a ticket channel
- Persistent buttons (survive bot restarts)

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

| Variable | Required | Description |
|---|---|---|
| `DISCORD_TOKEN` | ✅ | Bot token from Discord Developer Portal |
| `PREFIX` | optional | Command prefix (default `/`) |
| `TICKET_CATEGORY_ID` | optional | Category ID where ticket channels are created |
| `TICKET_LOG_CHANNEL_ID` | optional | Channel ID for close transcripts/logs |
| `SUPPORT_ROLE_ID` | optional | Role that can see all tickets and use staff commands |

### 3. Create a bot & get your token

1. Go to https://discord.com/developers/applications
2. Click **New Application** → name it → go to **Bot** tab
3. Click **Reset Token** and copy it into `.env`
4. Under **Privileged Gateway Intents**, enable:
   - **Server Members Intent**
   - **Message Content Intent**

### 4. Invite the bot to your server

Use the OAuth2 URL Generator (**OAuth2 → URL Generator**):
- Scopes: `bot`
- Bot Permissions: `Send Messages`, `Read Message History`, `Manage Messages`, `Manage Channels`, `Kick Members`, `Ban Members`

### 5. Run the bot

```bash
python bot.py
```

### 6. Set up the ticket panel

In Discord, run:
```
/ticket-panel
```
(in whichever channel you want the panel to live — requires Administrator)

---

## Project Structure

```
discord-bot/
├── bot.py                  # Entry point — loads cogs and starts the bot
├── cogs/
│   ├── general.py          # ping, hello, info
│   ├── moderation.py       # kick, ban, unban, clear
│   └── tickets.py          # Full ticket system
├── .env.example            # Environment variable template
├── .env                    # Your secrets (never commit this)
├── requirements.txt
└── .gitignore
```

---

## Commands

### General
| Command | Description |
|---|---|
| `/ping` | Shows bot latency |
| `/hello` | Greets the user |
| `/info` | Shows bot stats |

### Moderation
| Command | Permission |
|---|---|
| `/kick @user [reason]` | Kick Members |
| `/ban @user [reason]` | Ban Members |
| `/unban user` | Ban Members |
| `/clear [amount]` | Manage Messages |

### Tickets
| Command | Description | Permission |
|---|---|---|
| `/ticket-panel` | Posts the Open Ticket panel | Administrator |
| `/add @user` | Adds a user to the ticket | Manage Channels |
| `/remove @user` | Removes a user from the ticket | Manage Channels |
| `/rename name` | Renames the ticket channel | Manage Channels |

> **Note:** `/` is used as a text-command prefix here (not Discord's built-in slash commands). If you want native slash commands, the cogs can be adapted to use `app_commands`.

---

## Adding a New Cog

1. Create `cogs/mycog.py`:

```python
from discord.ext import commands

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def mycommand(self, ctx):
        await ctx.send("Hello!")

async def setup(bot):
    await bot.add_cog(MyCog(bot))
```

2. Add `"cogs.mycog"` to the `COGS` list in `bot.py`.
