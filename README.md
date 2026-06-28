# Discord Bot Boilerplate

A clean Python Discord bot boilerplate using [discord.py v2](https://discordpy.readthedocs.io/) with a full **ticket system** and **moderation image banners**.

## Features

- `/` slash commands (appear natively in Discord's command menu)
- Custom `/help` listing every available command
- **Moderation embeds** — ban/kick/unban each generate a red PNG banner image (`BANNED`, `KICKED`, `UNBANNED`) with the target's avatar and the moderator who issued the action
- Full **ticket system** with Open/Close/Claim buttons, transcripts, and logging
- Cog-based architecture — easy to extend

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

| Variable | Required | Description |
|---|---|---|
| `DISCORD_TOKEN` | ✅ | Bot token from the Discord Developer Portal |
| `PREFIX` | optional | Command prefix (default `/`) |
| `TICKET_CATEGORY_ID` | optional | Category ID for ticket channels |
| `TICKET_LOG_CHANNEL_ID` | optional | Channel ID for close transcripts |
| `SUPPORT_ROLE_ID` | optional | Role ID that can see all tickets |

### 3. Create a bot & get your token

1. Go to https://discord.com/developers/applications
2. **New Application** → name it → **Bot** tab → **Reset Token** → paste into `.env`
3. Under **Privileged Gateway Intents** enable:
   - **Server Members Intent**
   - **Message Content Intent**

### 4. Invite the bot

OAuth2 → URL Generator → Scopes: `bot` → Permissions:
`Send Messages`, `Read Message History`, `Manage Messages`, `Manage Channels`, `Kick Members`, `Ban Members`, `Attach Files`

> **Attach Files** is required for the banner images to appear in embeds.

### 5. Run

```bash
python bot.py
```

Slash commands sync automatically on startup (may take up to 1 hour to appear globally; add a guild ID to `tree.sync()` for instant testing).

---

## Project Structure

```
discord-bot/
├── bot.py                  # Entry point
├── cogs/
│   ├── general.py          # /ping  /hello  /info  /help
│   ├── moderation.py       # /ban  /kick  /unban  /clear
│   └── tickets.py          # Full ticket system
├── utils/
│   ├── __init__.py
│   └── images.py           # Pillow banner image generator
├── .env.example
├── requirements.txt
└── .gitignore
```

---

## Commands

### General
| Command | Description |
|---|---|
| `/ping` | Bot latency |
| `/hello` | Greet the user |
| `/info` | Bot stats |
| `/help` | All commands |

### Moderation
| Command | Permission |
|---|---|
| `/ban @user [reason]` | Ban Members |
| `/kick @user [reason]` | Kick Members |
| `/unban <user>` | Ban Members |
| `/clear [amount]` | Manage Messages |

### Tickets
| Command | Permission |
|---|---|
| `/ticket_panel` | Administrator |
| `/add @user` | Manage Channels |
| `/remove @user` | Manage Channels |
| `/rename <name>` | Manage Channels |
