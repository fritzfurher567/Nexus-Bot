# All-in-One Discord Bot

**Made by Fritz**

A complete Discord server management bot built with `discord.py` — moderation, tickets, leveling, reaction roles, auto-mod, custom commands, server logs, reminders, an economy system, and YouTube/Twitch alerts, all in one codebase. Feature set is inspired by what VibeBot, Carl-bot, Dyno, MEE6, and YAGPDB each do best.

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create a bot application**
   - Go to the [Discord Developer Portal](https://discord.com/developers/applications)
   - Create an application → add a Bot
   - Under **Privileged Gateway Intents**, enable:
     - Server Members Intent
     - Message Content Intent
   - Copy the bot token

3. **Configure environment variables**
   - Copy `.env.example` to `.env`
   - Paste your bot token into `DISCORD_TOKEN`
   - (Optional) Add `TWITCH_CLIENT_ID` / `TWITCH_CLIENT_SECRET` if you want `/twitch-alert` — free at [dev.twitch.tv/console](https://dev.twitch.tv/console). YouTube alerts need no key at all.

4. **Invite the bot to your server**
   - In the Developer Portal, go to OAuth2 → URL Generator
   - Scopes: `bot`, `applications.commands`
   - Permissions: Administrator (simplest), or pick individual permissions matching the features above

5. **Run the bot**
   ```bash
   python main.py
   ```
   Slash commands sync automatically on startup (can take up to an hour to appear globally the first time — usually much faster).

## Configuration Commands

Run these once as a server admin after inviting the bot:

| Command | Purpose |
|---|---|
| `/setmodlog #channel` | Where moderation actions get logged |
| `/ticket-setup category:<category> log_channel:<channel>` | Configure ticket system |
| `/ticket-panel` | Post the "Create Ticket" panel in the current channel |
| `/welcome-setup #channel` | Set welcome message channel |
| `/goodbye-setup #channel` | Set goodbye message channel |
| `/welcome-dm enabled:true` | Turn on join DMs |
| `/goodbye-dm enabled:true` | Turn on leave DMs |
| `/setserverlog #channel` | Where message edit/delete logs go |
| `/levelup-channel #channel` | Where level-up announcements post |
| `/setlevelrole level:5 role:@Regular` | Auto-grant a role at a level |
| `/automod-toggle feature:... enabled:true` | Turn on invite/caps filters |
| `/automod-mentionlimit limit:5` | Cap mentions per message |
| `/youtube-alert #channel UC...` | Post when a YouTube channel uploads |
| `/twitch-alert #channel <username>` | Post when a streamer goes live |

## Project Structure

```
bot/
├── main.py               # entry point, loads cogs
├── database.py           # SQLite storage layer
├── config.py             # colors, credit line, XP curve, currency, options
├── requirements.txt
├── .env.example
├── cogs/
│   ├── moderation.py
│   ├── automod.py
│   ├── logging_cog.py
│   ├── tickets.py
│   ├── welcome.py
│   ├── leveling.py
│   ├── reactionroles.py
│   ├── customcommands.py
│   ├── reminders.py
│   ├── economy.py
│   ├── socialalerts.py
│   ├── embeds.py
│   └── utility.py
└── LICENSE
```

## Credit

This bot was created by **Fritz**. Attribution is built into the code — it appears in the bot's presence status, embed footers, and the `/credits` command.

## License

MIT License — see [LICENSE](LICENSE). You're free to use, modify, and distribute this code, but the copyright notice must stay intact.
