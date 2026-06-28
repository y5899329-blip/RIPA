# Discord Bot Boilerplate

Python Discord bot using [discord.py v2](https://discordpy.readthedocs.io/) with slash commands, a ticket system, and moderation image banners.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in DISCORD_TOKEN
python bot.py
```

### Required bot permissions
`Send Messages` · `Read Message History` · `Manage Messages` · `Manage Channels` · `Kick Members` · `Ban Members` · **`Attach Files`** (needed for banner images)

### Required intents
Enable **Server Members Intent** and **Message Content Intent** in the Discord Developer Portal.

## Commands

| Command | Description | Permission |
|---|---|---|
| `/help` | All commands | Everyone |
| `/ping` | Latency | Everyone |
| `/info` | Bot stats | Everyone |
| `/ban @user [reason]` | Ban + red BANNED banner | Ban Members |
| `/kick @user [reason]` | Kick + red KICKED banner | Kick Members |
| `/unban <user>` | Unban + UNBANNED banner | Ban Members |
| `/clear [amount]` | Delete messages | Manage Messages |
| `/ticket_panel` | Post ticket panel | Administrator |
| `/add @user` | Add to ticket | Manage Channels |
| `/remove @user` | Remove from ticket | Manage Channels |
| `/rename <name>` | Rename ticket channel | Manage Channels |
