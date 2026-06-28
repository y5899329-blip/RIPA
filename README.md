# Discord Bot

Python Discord bot (discord.py v2) with slash commands, a full configurable ticket system, and red moderation image banners.

---

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env      # paste your DISCORD_TOKEN
python bot.py
```

Slash commands sync automatically on startup.  
> They may take up to **1 hour** to appear globally. For instant testing, hard-code your guild ID in `bot.tree.sync(guild=...)`.

---

## Required bot permissions

`Send Messages` · `Read Message History` · `Manage Messages` · `Manage Channels` · `Kick Members` · `Ban Members` · **`Attach Files`**

Enable under **Privileged Gateway Intents**: **Server Members Intent** + **Message Content Intent**

---

## Ticket System Setup (in Discord)

Run these slash commands after inviting the bot:

| Step | Command | Who |
|------|---------|-----|
| 1 | `/ticket_setlog #log-channel` | Admin |
| 2 | `/ticket_setsupport @Support` | Admin |
| 3 | `/ticket_setcategory <category_id>` | Admin |
| 4 | `/ticket_setconfigrole @Staff` | Admin |
| 5 | `/ticket_setmessage Your message here` | Config Role |
| 6 | `/ticket_setbutton text:Open color:green emoji:🎫` | Config Role |
| 7 | `/ticket_panel` in your support channel | Admin |

> All settings are saved in `ticket_config.json` — no restart needed.

**Button colors:** `primary` (blue) · `green` · `red` · `grey`  
**Button emoji:** any single emoji, or leave blank to remove it.

---

## All Commands

### General
| Command | Description |
|---------|-------------|
| `/help` | All commands |
| `/ping` | Latency |
| `/info` | Bot stats |

### Moderation
| Command | Permission |
|---------|------------|
| `/ban @user [reason]` | Ban Members |
| `/kick @user [reason]` | Kick Members |
| `/unban <user>` | Ban Members |
| `/clear [amount]` | Manage Messages |

### Tickets — User
| Command | Description | Permission |
|---------|-------------|------------|
| `/ticket_panel` | Post Open Ticket panel | Administrator |
| `/add @user` | Add user to ticket | Manage Channels |
| `/remove @user` | Remove user from ticket | Manage Channels |
| `/rename <name>` | Rename ticket channel | Manage Channels |

### Tickets — Setup
| Command | Description | Permission |
|---------|-------------|------------|
| `/ticket_setmessage <text>` | Welcome message in new tickets | Config Role |
| `/ticket_setbutton [text] [color] [emoji]` | Customise Open Ticket button | Config Role |
| `/ticket_setconfigrole <role>` | Who can edit ticket settings | Admin |
| `/ticket_setsupport <role>` | Staff role for tickets | Admin |
| `/ticket_setlog <channel>` | Log channel | Admin |
| `/ticket_setcategory <id>` | Category for ticket channels | Admin |

---

## Project Structure

```
discord-bot/
├── bot.py
├── ticket_config.json      ← all ticket settings (auto-created)
├── cogs/
│   ├── general.py          ← /ping /hello /info /help
│   ├── moderation.py       ← /ban /kick /unban /clear
│   └── tickets.py          ← full ticket system
├── utils/
│   ├── __init__.py
│   └── images.py           ← Pillow banner generator
├── assets/
│   └── bold.ttf            ← bundled font (always works)
├── .env.example
├── requirements.txt
└── .gitignore
```
