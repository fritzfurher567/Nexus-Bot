# Complete Discord Bot Guide — Step-by-Step

Made by Fritz

This guide walks you through every single command in the bot with detailed explanations of what each command does and why you'd use it.

---

## Table of Contents

1. [Initial Setup](#initial-setup)
2. [Moderation](#moderation)
3. [Auto-Moderation](#auto-moderation)
4. [Server Logging](#server-logging)
5. [Tickets](#tickets)
6. [Welcome & Goodbye](#welcome--goodbye)
7. [Leveling & XP](#leveling--xp)
8. [Reaction Roles](#reaction-roles)
9. [Custom Commands](#custom-commands)
10. [Reminders](#reminders)
11. [Economy & Shop](#economy--shop)
12. [Social Alerts](#social-alerts)
13. [Permissions](#permissions)
14. [Roblox Verification](#roblox-verification)
15. [Awards & Leave of Absence](#awards--leave-of-absence)
16. [Rank Hierarchy & Divisions](#rank-hierarchy--divisions)
17. [Discharge & Desertions](#discharge--desertions)
18. [Background Checks](#background-checks)
19. [Events](#events)
20. [Audit Log](#audit-log)
21. [Embeds & Messages](#embeds--messages)
22. [Utility & Info](#utility--info)

---

## Initial Setup

### 1. Create Your Discord Application

**What this does:** This creates a bot account on Discord that your code can control.

**Steps:**

1. Open https://discord.com/developers/applications in your browser
2. Click the blue "New Application" button in the top right
3. Enter a name for your bot (e.g., "My Community Bot")
4. Click "Create"
5. You're now in your application's settings page

### 2. Create the Bot User

**What this does:** Turns your application into an actual bot that can join servers.

**Steps:**

1. On the left sidebar, click "Bot"
2. Click the blue "Add Bot" button
3. You should see a section with "USERNAME" and "TOKEN"

### 3. Get Your Bot Token

**What this does:** This is the password that lets your code control the bot. Never share this with anyone.

**Steps:**

1. Under the "TOKEN" section, click "Copy"
2. Open a text file on your computer
3. Paste the token there and save it somewhere safe
4. You'll use this token when you set up the bot code

### 4. Enable Required Intents

**What this does:** Intents tell Discord what events your bot should listen to. Some intents are "privileged" and need to be explicitly enabled.

**Steps:**

1. Scroll down to "PRIVILEGED GATEWAY INTENTS"
2. Toggle ON these three:
   - **Server Members Intent** — lets your bot see when members join/leave
   - **Message Content Intent** — lets your bot read message contents
   - **Presence Intent** — lets your bot see user activity status
3. Save your changes

### 5. Install Python & Dependencies

**What this does:** Downloads and installs Python (the language the bot is written in) and all the libraries it needs.

**Steps:**

Open your terminal/command prompt and run:

```bash
pip install -r requirements.txt
```

This reads the `requirements.txt` file (which contains: discord.py, aiosqlite, python-dotenv, aiohttp) and installs them all.

### 6. Set Up Your Environment File

**What this does:** Creates a `.env` file where you store your bot token securely (not in your code).

**Steps:**

```bash
cp .env.example .env
```

Then open the `.env` file in a text editor and replace `your_token_here` with the token you copied earlier:

```
DISCORD_TOKEN=abc123def456ghi789...
PREFIX=!
```

### 7. Run the Bot

**What this does:** Starts the bot and connects it to Discord.

**Steps:**

```bash
python main.py
```

You should see output like:
```
Syncing commands...
Bot is ready!
```

If you see errors, scroll up and read them — they tell you what went wrong.

### 8. Get Your Bot's Invite Link

**What this does:** Creates a link you can click to add the bot to your server.

**Steps:**

1. Go back to Discord Developer Portal
2. Click "OAuth2" on the left sidebar
3. Click "URL Generator"
4. Under "SCOPES", check these two boxes:
   - `bot`
   - `applications.commands`
5. Under "PERMISSIONS", check:
   - `Administrator` (this gives your bot power to do things)
6. Copy the generated URL at the bottom
7. Open the URL in your browser
8. Select which server you want to add the bot to
9. Click "Authorize"

### 9. Verify Commands Appear

**What this does:** Makes sure all the bot's commands are available in your Discord server.

**Steps:**

1. Go to any channel in your server
2. Type `/` and wait a second
3. You should see a list of commands (ping, help, ban, kick, etc.)
4. Try typing `/help` and hitting enter
5. The bot should send you a list of all available commands

If commands don't appear after 10 minutes, try:
- Restarting the bot (stop it and run `python main.py` again)
- Waiting up to 1 hour (Discord takes time to sync commands globally)

---

## Moderation

Moderation commands help you manage rule-breakers and keep your server safe. All moderation actions are logged so you have a record.

### Set Up Mod Log Channel (Do This First)

**What this does:** Creates a record of every moderation action (kicks, bans, warnings, etc.). This is your evidence if someone claims you were unfair.

**Command:**
```
/setmodlog #mod-logs
```

**How to use it:**

1. Create a channel called #mod-logs (or any private channel for staff only)
2. Type the command above, selecting that channel
3. Now every time you kick/ban/warn someone, it's automatically logged there with timestamps

**Why you need this:** If someone says "I was banned unfairly," you can show the log proving they violated a rule.

---

### Kick a Member

**What this does:** Removes someone from your server but doesn't prevent them from rejoining. It's temporary punishment.

**Command:**
```
/kick @BadUser Spamming in chat
```

**Step-by-step:**

1. Type `/kick`
2. Select the member you want to kick from the dropdown that appears
3. Type a reason (this is logged and sent to the person)
4. Press enter
5. The member is removed and gets a DM explaining why (if their DMs are open)

**Example scenarios:**
- Someone was warned before but kept breaking rules: `/kick @User Warned multiple times, continuing to spam`
- Someone is being disruptive: `/kick @User Disrupting channel with off-topic conversation`

---

### Ban a Member

**What this does:** Removes someone and prevents them from ever rejoining unless you unban them. It's permanent.

**Command:**
```
/ban @Hacker Attempting to hack
/ban @Hacker Attempting to hack delete_days:7
```

**Step-by-step:**

1. Type `/ban`
2. Select the member
3. Type a reason
4. Optionally set `delete_days` (0-7) to delete how many days of their messages
5. Press enter

**delete_days explained:**
- `delete_days:0` — keeps all their messages (they just can't send new ones)
- `delete_days:7` — deletes everything they posted in the last 7 days
- Use 7 if they spammed or posted inappropriate content you want gone

**Example:**
```
/ban @Hacker Hacking attempts delete_days:7
```

---

### Unban a User

**What this does:** Removes a ban so someone can rejoin your server.

**Command:**
```
/unban 123456789 They apologized
```

**How to get their user ID:**

1. Right-click their name/profile anywhere in Discord
2. Click "Copy User ID"
3. Use that number with the unban command

**When to use this:**
- They appealed and showed they understand the rules
- You banned them by accident
- Enough time has passed and they've learned their lesson

---

### Timeout (Mute) a Member

**What this does:** Silences someone temporarily. They can still see messages but can't send new ones, react to things, or join voice channels.

**Command:**
```
/timeout @Spammer 10m Stop advertising
/timeout @User1 1d Being disruptive
```

**Duration format:**
- `10m` = 10 minutes
- `2h` = 2 hours
- `1d` = 1 day
- `1w` = 1 week
- Maximum: 28 days

**When to use:**
- Someone is spamming (timeout instead of kick)
- Someone is being hostile but not ban-worthy (1 hour timeout to cool off)
- Someone violated one rule but can improve (24-hour timeout + warning)

**Example:**
```
/timeout @User1 6h Stop spamming reactions
```

---

### Remove Timeout

**What this does:** Lets someone talk again after a timeout expires (or early if you decide to remove it manually).

**Command:**
```
/untimeout @Spammer
```

**When to use:**
- They appealed via DM and you're giving them a second chance
- The timeout accidentally got applied to wrong person
- They've served their time and you want to let them try again early

---

### Warn a Member

**What this does:** Records a formal warning. These stack up and create a history you can reference.

**Command:**
```
/warn @User1 First warning, read the rules
```

**How it works:**

1. First warning: They get a message explaining the rule they broke
2. Second warning: This shows they were warned before
3. Third warning: You have evidence for a timeout or kick

**When to use:**
- Someone breaks a minor rule (off-topic chat, minor rudeness)
- Before escalating to timeout/kick, warn first
- Building a case for removal

**Examples:**
```
/warn @User1 Posting off-topic content in general
/warn @User2 Disrespectful language toward other members
```

---

### View Warnings

**What this does:** Shows all previous warnings for someone.

**Command:**
```
/warnings @User1
```

**What you see:**
- Warning ID (number)
- The reason they were warned
- When they were warned
- Who warned them

**Why this matters:**
- If you're deciding whether to kick/ban someone, you can see their history
- Proves to them that this isn't your first conversation about this behavior
- Gives you evidence if they claim you're being unfair

---

### Clear All Warnings

**What this does:** Wipes someone's warning record completely.

**Command:**
```
/clearwarnings @User1
```

**When to use:**
- They've been good for 6 months and earned a fresh start
- They were warned by mistake
- You're giving them one final chance

---

### Remove a Single Warning

**What this does:** Deletes one specific warning (useful if it was logged incorrectly).

**Command:**
```
/removewarning 5
```

**How to use:**

1. Run `/warnings @User1` to see their warnings
2. Find the ID number of the warning you want to remove
3. Type `/removewarning [ID]`

---

### Delete Messages (Purge)

**What this does:** Quickly delete multiple messages at once. Useful for cleaning up spam, memes, or off-topic conversations.

**Command:**
```
/purge 50
/purge 25 @Spammer
```

**Examples:**

- Delete 50 most recent messages: `/purge 50`
- Delete 25 messages from one person: `/purge 25 @Spammer`

**Important:** This only deletes recent messages (last 2 weeks). Very old messages can't be deleted by Discord rules.

---

### Lock a Channel

**What this does:** Temporarily prevents @everyone from sending messages. Staff can still send messages, but regular members are silenced.

**Command:**
```
/lock
```

**When to use:**
- A debate is getting heated and you need to cool things down
- Someone posted something inappropriate and you need time to decide
- You're making an announcement and don't want it buried
- A channel is being brigaded with spam

**What happens:**
- Members see the channel but can't type
- They know it's locked (they see a message)
- Staff can still send messages
- You can unlock it anytime

---

### Unlock a Channel

**What this does:** Re-enables messaging for @everyone.

**Command:**
```
/unlock
```

---

### Lock All Channels (Lockdown)

**What this does:** Emergency button that locks EVERY text channel in your server at once.

**Command:**
```
/lockdown
```

**When to use (rare):**
- Raid/attack happening (ton of spam invading)
- Serious situation where you need immediate control
- Server is being compromised

**Important:** Everyone knows this is a serious action. Use only if necessary.

---

### Set Slowmode

**What this does:** Forces a delay between messages (prevents spam).

**Command:**
```
/slowmode 5
/slowmode 0
```

**Examples:**

- 5 seconds between each message: `/slowmode 5`
- Disable slowmode: `/slowmode 0`

**When to use:**
- Channel is being flooded with messages
- Gaming tournament happening (prevents chat lag)
- Announcement channel where you want people to read before commenting

---

### Change Someone's Nickname

**What this does:** Changes how their name appears in your server (doesn't affect their actual Discord username).

**Command:**
```
/nickname @User1 Cool Guy
/nickname @User1
```

**Examples:**

- Give them a nickname: `/nickname @User1 Helpful Helper`
- Reset to their username: `/nickname @User1` (leave blank)

**When to use:**
- They have an offensive username but are otherwise fine
- You want to mark someone (e.g., "/nickname @Admin1 ADMIN")
- Organizing a tournament (assign role abbreviations)

---

### Add a Role

**What this does:** Gives someone a role (they can have multiple roles).

**Command:**
```
/addrole @User1 @VIP
/addrole @User2 @Moderator
```

**When to use:**
- Promoting someone to moderator
- Giving VIP access
- Marking someone with a special status

---

### Remove a Role

**What this does:** Takes away a role from someone.

**Command:**
```
/removerole @User1 @VIP
```

---

## Auto-Moderation

Auto-mod runs automatically on every message. You don't type commands — the bot watches for rule-breaking and acts.

### Set Banned Words

**What this does:** Automatically deletes messages containing certain words and warns the sender.

**Command:**
```
/automod-bannedwords add spam, abuse, badword
/automod-bannedwords list
/automod-bannedwords remove badword
```

**Step-by-step:**

1. Type `/automod-bannedwords add`
2. Type the words separated by commas: `spam, abuse, slur`
3. Press enter
4. Now any message with those words is automatically deleted

**How it works:**

- Someone types a banned word
- Bot immediately deletes the message
- Bot warns them automatically
- It's logged in mod-log

**When to use:**
- Slurs or hate speech (zero tolerance)
- Common spam phrases
- Advertising links you don't want

---

### Toggle Invite Filter

**What this does:** Auto-deletes Discord invite links (prevents people from advertising other servers).

**Command:**
```
/automod-toggle feature:Invite_link_filter enabled:true
/automod-toggle feature:Invite_link_filter enabled:false
```

**Examples:**

- Turn it ON: `/automod-toggle feature:Invite_link_filter enabled:true`
- Turn it OFF: `/automod-toggle feature:Invite_link_filter enabled:false`

---

### Toggle Caps Filter

**What this does:** Auto-deletes messages that are MOSTLY UPPERCASE (prevents screaming).

**Command:**
```
/automod-toggle feature:Excessive_caps_filter enabled:true
```

**What "mostly uppercase" means:** If a message is more than 70% capital letters, it gets deleted.

**Examples that would be deleted:**
- `THIS IS SPAM`
- `STOP TALKING ABOUT THIS`
- `EVERYONE LOOK AT THIS` (but `Hello EVERYONE` wouldn't be)

---

### Set Mention Limit

**What this does:** Deletes messages that mention too many people (prevents mass-tagging harassment).

**Command:**
```
/automod-mentionlimit 5
/automod-mentionlimit 0
```

**Examples:**

- Allow max 5 mentions: `/automod-mentionlimit 5`
  - Messages with 6+ @mentions get deleted
- Disable (allow unlimited): `/automod-mentionlimit 0`

---

## Server Logging

### Set Server Log Channel

**What this does:** Logs general server activity (not moderation, separate log). Captures message edits/deletes and channel management.

**Command:**
```
/setserverlog #logs
```

**What gets logged:**

- Someone edits a message (shows old and new text)
- Someone deletes a message (shows who deleted what)
- A channel is created
- A channel is deleted

**Why this matters:**
- See if someone deleted messages to cover something up
- Track channel changes (useful for accountability)
- Separate from mod-log (this is activity, not enforcement)

---

## Tickets

Support ticket system where members create private channels to get help.

### Initial Setup

**Command:**
```
/ticket-setup #Tickets #ticket-logs
```

**Step-by-step:**

1. Create two channels:
   - `#Tickets` (category where ticket channels get created)
   - `#ticket-logs` (where closed tickets get archived)
2. Run the command above, selecting those channels
3. Done (do this once per server)

---

### Post the Ticket Panel

**What this does:** Posts a button in a channel. Members click it to create a support ticket.

**Command:**
```
/ticket-panel
```

**Step-by-step:**

1. Go to your #support channel (or wherever you want the button)
2. Type `/ticket-panel`
3. A message with a "Create Ticket" button appears
4. Members click it to start

---

### How Tickets Work (Member's View)

**What the member does:**

1. Click the "Create Ticket" button
2. Select a category (General Support, Technical, Billing, Report a User, Other)
3. Select priority (Low, Medium, High, Urgent)
4. A private channel is created: `ticket-john` or similar
5. Only they and staff can see it

**What they do in the ticket:**

1. Type their question/issue
2. Staff responds and helps
3. When resolved, staff types `/ticket-close`
4. The channel is deleted and a transcript is saved

---

### Inside a Ticket Channel (Staff Commands)

**Add someone to the ticket:**
```
/ticket-add @Helper
```

This lets another staff member see and help.

**Remove someone:**
```
/ticket-remove @Helper
```

**Change priority:**
```
/ticket-priority urgent
```

(Options: low, medium, high, urgent)

**Close the ticket:**
```
/ticket-close
```

This saves a transcript (a text file of the entire conversation) to your #ticket-logs channel, then deletes the channel.

**Claim button:** Click the "Claim" button on the first message so other staff know you're handling it.

---

## Welcome & Goodbye

### Set Welcome Message

**What this does:** Posts a message every time someone joins your server. Makes them feel welcome and can include rules/info.

**Command:**
```
/welcome-setup #welcome Welcome {user} to {server}! We now have {membercount} members.
```

**Placeholders (these get replaced automatically):**
- `{user}` — becomes a mention: @NewMember
- `{username}` — becomes their name: john
- `{server}` — becomes server name: My Cool Server
- `{membercount}` — becomes member count: 523

**Example:**
```
/welcome-setup #welcome Thanks {user} for joining {server}! Read #rules and #introductions. We now have {membercount} members!
```

---

### Set Goodbye Message

**Command:**
```
/goodbye-setup #goodbye {user} has left {server}. We now have {membercount} members.
```

Posts when someone leaves. Same placeholders work.

---

### Send Welcome DM

**What this does:** Sends a personal message to new members (in addition to channel message).

**Command:**
```
/welcome-dm enabled:true Welcome to {server}! Check out #rules and #introductions.
```

**When to use:**
- Want to give them direct instructions
- Want to point them toward important channels
- Want a more personal touch

---

### Send Goodbye DM

**Command:**
```
/goodbye-dm enabled:true Sorry to see you leave {server}! Hope to see you again someday.
```

---

## Leveling & XP

Members earn XP (experience points) by chatting. As they gain XP, they level up. This gamifies your server and encourages participation.

### How XP Works

**Earning XP:**
- Members get 15-25 XP per message
- But only once every 60 seconds (prevents spam)
- Commands don't earn XP (only real messages)

**Leveling up:**
- Level 1 requires 155 XP
- Level 5 requires 630 XP
- Level 10 requires 1,600 XP
- Gets harder as they progress

**Announcement:**
- When they level up, the bot announces it (either in channel or dedicated #level-ups channel)

---

### Check Your Rank

**Command:**
```
/rank
/rank @User1
```

**What you see:**
- Current level
- Total XP earned
- Progress bar to next level
- XP needed for next level

**Example output:**
```
Level 5 (630 / 850 XP)
[=========>    ] 250 XP to Level 6
```

---

### See the Leaderboard

**Command:**
```
/leaderboard
```

**What you see:**
- Top 10 members ranked by XP
- Their level and total XP
- Medals for top 3 (if enabled)

---

### Set Rank-Up Announcement Channel

**What this does:** When someone levels up, a message is posted to this channel instead of wherever they were chatting.

**Command:**
```
/levelup-channel #level-ups
```

**Example:** Someone reaches level 10 in #general. Without this, bot posts in #general. With this, bot posts in #level-ups instead.

---

### Auto-Grant Role at a Level

**What this does:** When someone reaches a specific level, they automatically get a role.

**Command:**
```
/setlevelrole level:5 role:@Member
/setlevelrole level:10 role:@Regular
/setlevelrole level:25 role:@VIP
```

**How it works:**

1. Level 5 reached → Auto-grant @Member role
2. Level 10 reached → Auto-grant @Regular role
3. Level 25 reached → Auto-grant @VIP role
4. They can have multiple roles

**Why use this:**
- Rewards active members automatically
- No manual role management
- Gamifies participation

---

### Remove a Level Role

**Command:**
```
/removelevelrole level:5
```

Stops giving @Member at level 5.

---

## Reaction Roles

Members react with an emoji to get a role. No commands needed.

### Link Emoji to Role

**What this does:** When someone reacts to a specific message with an emoji, they get a role. When they remove the reaction, they lose the role.

**Command:**
```
/reactionrole-add 987654321 emoji:gear role:@Support
/reactionrole-add 987654321 emoji:art role:@Artist
```

**How to get message ID:**

1. Right-click any message in Discord
2. Click "Copy Message ID"
3. Paste it into the command

**Example workflow:**

1. Post in #roles: "React with gear for Support role, or art for Artist role"
2. Run: `/reactionrole-add [message_id] emoji:gear role:@Support`
3. Run: `/reactionrole-add [message_id] emoji:art role:@Artist`
4. Now when someone reacts with gear, they get @Support
5. When they remove the reaction, role is removed

---

### Unlink an Emoji

**Command:**
```
/reactionrole-remove 987654321 emoji:gear
```

Stops granting @Support for gear emoji.

---

## Custom Commands

Create your own prefix commands (like `!rules` or `!hello`) without any coding.

### Add a Custom Command

**Command:**
```
/customcommand-add trigger:rules Check #rules for our guidelines!
/customcommand-add trigger:hello Welcome to the server!
```

**How it works:**

1. Someone types: `!rules`
2. Bot replies with: "Check #rules for our guidelines!"
3. That's it

**When to use:**
- FAQs you answer constantly
- Links you post repeatedly
- Server info you want easy access to

**Examples:**
```
/customcommand-add trigger:rules Read #rules and #moderation-policy
/customcommand-add trigger:donate We don't accept donations, thanks for offering
/customcommand-add trigger:links YouTube: youtube.com/c/ourserver | Website: ourserver.com
```

---

### Remove a Custom Command

**Command:**
```
/customcommand-remove trigger:rules
```

---

### List Custom Commands

**Command:**
```
/customcommand-list
```

Shows all custom commands in your server.

---

## Reminders

Personal reminders that DM you when time's up.

### Set a Reminder

**Command:**
```
/remind duration:10m Check the oven
/remind duration:2h Call the dentist
/remind duration:1d Pay bills
```

**Duration format:**
- `10m` = 10 minutes
- `2h` = 2 hours
- `1d` = 1 day
- `1w` = 1 week

**How it works:**

1. You set a reminder: `/remind duration:1h Finish project`
2. Bot checks every 30 seconds
3. After 1 hour, bot DMs you: "Finish project"
4. If your DMs are closed, it posts in the channel instead

---

## Economy & Shop

Server-wide currency system. Members earn coins and spend them.

### Check Balance

**Command:**
```
/balance
/balance @User1
```

Shows how many coins someone has.

---

### Claim Daily Reward

**Command:**
```
/daily
```

Get 200 coins once per 24 hours. Same time each day.

---

### Work

**Command:**
```
/work
```

Earn 50-150 coins randomly. 1 hour cooldown. Random job messages:
- "You delivered packages and earned 87 coins"
- "You busked in the town square and earned 112 coins"

---

### Send Money

**Command:**
```
/pay @User1 100
```

Send someone coins.

---

### Economy Leaderboard

**Command:**
```
/economy-leaderboard
```

Top 10 richest members.

---

### View the Shop

**Command:**
```
/shop
```

Shows all items for sale and their prices.

---

### Buy an Item

**Command:**
```
/buy item_name:Member
/buy item_name:VIP
```

Spend coins on an item. If it's linked to a role, you get it automatically.

---

### Add Item to Shop (Admin)

**Command:**
```
/shop-add item_name:Member price:500
/shop-add item_name:VIP price:1000 role:@VIP
```

**Examples:**

- Item with no role: `/shop-add item_name:Badge price:250` (cosmetic)
- Item with role reward: `/shop-add item_name:VIP price:5000 role:@VIP` (gives role when bought)

---

### Remove Item from Shop (Admin)

**Command:**
```
/shop-remove item_name:Member
```

---

## Social Alerts

Get notified when content creators post new videos or go live.

### YouTube Alerts

**What this does:** Bot checks a YouTube channel every 5 minutes. When they upload a new video, posts it to your channel.

**Command:**
```
/youtube-alert #streams UCddiUEpYJcSLOAekIKcyNAA
```

**How to find YouTube channel ID:**

1. Go to any YouTube channel
2. Look at the URL: `youtube.com/@channelname` or `youtube.com/c/channelname`
3. Go to their "About" tab
4. Copy the custom URL or channel ID
5. Channel IDs start with "UC" and are 24 characters long

**Example:**
```
/youtube-alert #content-drops UCddiUEpYJcSLOAekIKcyNAA
```

**What happens:**
- Video is uploaded to that channel
- Bot finds it (checks every 5 minutes)
- Posts announcement to #content-drops with title and link
- No API key needed (uses public RSS feed)

---

### Remove YouTube Alert

**Command:**
```
/youtube-alert-remove UCddiUEpYJcSLOAekIKcyNAA
```

---

### Twitch Alerts

**What this does:** Bot checks Twitch every 3 minutes. When someone goes live, posts to your channel.

**Command:**
```
/twitch-alert #streams ninja
```

**Setup required:**
1. Go to dev.twitch.tv/console (free)
2. Create an application
3. Copy your Client ID and Client Secret
4. Add to your .env file:
```
TWITCH_CLIENT_ID=your_id_here
TWITCH_CLIENT_SECRET=your_secret_here
```
5. Restart bot

**Example:**
```
/twitch-alert #live-streams pokimane
```

Now when pokimane goes live, bot posts in #live-streams.

---

### Remove Twitch Alert

**Command:**
```
/twitch-alert-remove pokimane
```

---

## Permissions

Restrict commands to specific roles. Only certain roles can use certain commands.

### Restrict a Command

**What this does:** Only people with a specific role (plus owner/admins) can use this command.

**Command:**
```
/permission-restrict command:ban role:@Moderator
/permission-restrict command:ticket-close role:@Support
```

**After this:**
- Only @Moderator role can use `/ban` (plus owner/admins, they always bypass)
- Only @Support role can use `/ticket-close`

**When to use:**
- Don't want random members kicking people
- Only certain staff can manage tickets
- Only leadership can discharge members

---

### Remove a Role from a Command

**Command:**
```
/permission-unrestrict command:ban role:@Moderator
```

Takes @Moderator off the allowed list. Now no one except owner/admins can use it.

---

### Remove All Restrictions from a Command

**Command:**
```
/permission-clear command:ban
```

Opens `/ban` back up (subject to normal Discord permissions).

---

### See What's Restricted

**Command:**
```
/permission-list
/permission-list command:ban
```

Shows which commands have restrictions and which roles can use them.

---

### Add or Remove Roles (Dedicated Command)

**What this does:** Pure role management (separate from moderation).

**Command:**
```
/role add @User1 @VIP
/role remove @User1 @VIP
```

---

## Roblox Verification

Link Discord members to their Roblox accounts.

### Verify Your Account

**What this does:** Member links their Discord to their Roblox account. Can auto-grant a verified role.

**Command:**
```
/verify roblox_username:your_username
```

**How it works:**

1. Member types: `/verify roblox_username:john_dev`
2. Bot looks up that Roblox account (uses public API, no key needed)
3. Links their Discord ID to that Roblox account
4. If you've set up `/verified-role`, they get it automatically
5. Member gets a DM confirming they're verified

**When to use:**
- Want to confirm members actually play Roblox
- Want Roblox-specific features tied to Discord roles

---

### Unverify Yourself

**Command:**
```
/unverify
```

Removes the verification link.

**Admins can unverify others:**
```
/unverify member:@User1
```

---

### Look Up Someone's Account

**Command:**
```
/whois
/whois member:@User1
```

Shows:
- Their linked Roblox username
- Their Roblox ID
- When they verified
- Their Roblox avatar

---

### Set the Verified Role

**Command:**
```
/verified-role role:@Verified
```

Auto-grant @Verified role when someone verifies.

---

## Awards & Leave of Absence

### Give Someone an Award

**What this does:** Publicly recognize someone for something they did well. They get a DM and it's logged.

**Command:**
```
/award member:@User1 title:Outstanding_Contribution reason:Helped many new members this week
```

**How it works:**

1. You award someone
2. They get a DM: "You received award: Outstanding Contribution"
3. It can post to an announcements channel
4. It's logged in their award history (you can see it with `/awards`)

**Examples:**
```
/award member:@User1 title:Helper reason:Answered 50 questions this month
/award member:@User2 title:Community_Ambassador reason:Brought 10 new members
```

---

### View Someone's Awards

**Command:**
```
/awards
/awards member:@User1
```

Shows all awards they've received with titles, reasons, and dates.

---

### Request Time Off

**What this does:** Member submits a vacation/absence request. Staff approves or denies with buttons.

**Command:**
```
/loa-request start_date:2026-09-01 end_date:2026-09-10 reason:Going on vacation
```

**How it works:**

1. Member submits request
2. Message goes to your #loa-requests channel (you set this up)
3. Staff sees Approve/Deny buttons
4. If approved, they show up in `/loa-list`
5. Member gets DM about the decision

---

### See Who's On Leave

**Command:**
```
/loa-list
```

Shows all currently approved leave-of-absences (useful for knowing who's away).

---

### Set Awards Channel

**Command:**
```
/awards-channel #announcements
```

Awards get posted here in addition to DM.

---

### Set LOA Review Channel

**Command:**
```
/loa-channel #loa-requests
```

Where LOA requests post for staff review.

---

## Rank Hierarchy & Divisions

Build a ranked ladder (Private → Corporal → Sergeant) and organize members into units.

### Add Ranks

**What this does:** Create an ordered hierarchy of ranks tied to Discord roles.

**Command:**
```
/rank-add rank_name:Private role:@Private order:1
/rank-add rank_name:Corporal role:@Corporal order:2
/rank-add rank_name:Sergeant role:@Sergeant order:3
```

**Order explained:**
- Order 1 = lowest rank
- Order 2 = middle rank
- Order 3 = highest rank
- Higher order = higher rank

**When to use:**
- Milsim/military servers (ranks)
- Teams (managers > leads > members)
- Guilds/clans (ranks)

---

### See All Ranks

**Command:**
```
/rank-list
```

Shows the full hierarchy from lowest to highest.

---

### Promote Someone

**Command:**
```
/promote member:@User1
```

Moves them up one rank:
- Private → Corporal
- Corporal → Sergeant
- etc.

Bot automatically removes old rank role, adds new one.

---

### Demote Someone

**Command:**
```
/demote member:@User1
```

Moves them down one rank.

---

### Set Specific Rank

**Command:**
```
/setrank member:@User1 rank_name:Sergeant
```

Jump straight to that rank (bypasses the ladder).

---

### Add Divisions

**What this does:** Non-hierarchical groupings (squads, teams, departments). Different from ranks.

**Command:**
```
/division-add division_name:Alpha role:@Alpha_Squad
/division-add division_name:Bravo role:@Bravo_Squad
```

**Difference from ranks:**
- Ranks are hierarchical (Private < Corporal < Sergeant)
- Divisions are flat (Alpha and Bravo are equal, just different)
- Someone can have a rank AND a division

---

### See Divisions

**Command:**
```
/division-list
```

---

### Transfer Someone

**Command:**
```
/transfer member:@User1 division_name:Bravo
```

Removes them from their current division, adds them to Bravo.

---

## Discharge & Desertions

Remove members from ranks/divisions and track who leaves while ranked.

### Discharge a Member

**What this does:** Strip someone's rank/division roles and log the reason. Optionally kick them too.

**Command:**
```
/discharge member:@User1 reason:Inactive for 30 days
/discharge member:@User1 reason:Violated server rules kick:true
```

**How it works:**

1. Removes all rank/division roles
2. Logs the discharge with reason
3. They get a DM explaining why
4. If `kick:true`, they're kicked from server

**When to use:**
- Someone has been inactive too long
- Someone violated rules seriously
- Someone is leaving voluntarily

---

### View Discharge History

**Command:**
```
/discharges member:@User1
```

Shows all past discharges for that member.

---

### Automatic Desertion Detection

**What this does:** If someone with a rank/division role leaves the server on their own, it's automatically logged as a desertion. No command needed — it's automatic.

**Example:**
- @User1 has @Sergeant rank
- They leave the server
- Bot automatically logs: "Desertion: @User1 left while holding Sergeant rank"

---

### See Recent Desertions

**Command:**
```
/desertions
```

Shows members who left while ranked/divisioned.

---

### Set Discharge Log Channel

**Command:**
```
/discharge-channel #discharge-logs
```

Discharges and desertions get posted there.

---

## Background Checks

### Run a Background Check

**What this does:** Pulls everything the bot knows about someone into one report.

**Command:**
```
/backgroundcheck member:@User1
```

**What you see:**
- When they joined
- When their Discord account was created
- Their current rank (if any)
- Their current division (if any)
- Their linked Roblox account (if verified)
- Number of warnings they have
- Number of awards they have
- Past discharges

**When to use:**
- Before promoting someone to staff
- Before giving trusted role
- Checking someone's history before important decision

---

## Events

Schedule server activities and track attendance.

### Create an Event

**Command:**
```
/event-create name:Server_Tournament description:1v1 bracket when:Next Saturday 8PM EST channel:#events
```

**How it works:**

1. Posts announcement to #events with details
2. Includes three RSVP buttons: Attending, Maybe, Can't Make It
3. Members click to RSVP
4. You can check attendance anytime

**Examples:**
```
/event-create name:Game_Night description:Multiplayer co-op when:Friday 7PM EST channel:#events
/event-create name:Community_Meeting description:Discuss server direction when:Sunday 6PM EST channel:#announcements
```

---

### See Upcoming Events

**Command:**
```
/event-list
```

Shows all scheduled events.

---

### Check Attendance

**Command:**
```
/event-attendance event_id:1
```

Shows:
- Who's attending
- Who said maybe
- Who declined
- Total count for each

---

## Audit Log

Track every single command run in your server.

### Set Audit Log Channel

**Command:**
```
/auditlog-channel #audit-logs
```

Every command someone runs gets logged there in real-time:
- Who ran it
- What command
- When

---

### Check Recent Commands

**Command:**
```
/auditlog
```

Shows the 15 most recent commands and who ran them.

**Why useful:**
- Catch staff abuse
- See who made what change
- Dispute resolution ("I didn't do that")

---

## Embeds & Messages

### Build a Custom Embed

**What this does:** Create a fancy formatted message with colors, images, titles, descriptions.

**Command:**
```
/embed channel:#announcements
```

**How it works:**

1. Pops up a form
2. Fill in:
   - Title (main heading)
   - Description (main text)
   - Color (hex code like 5865F2, or leave blank for default)
   - Footer (small text at bottom)
   - Image URL (optional banner)
3. Bot posts the formatted embed

**Example:**
- Title: `New Feature Released`
- Description: `We just added the new economy system!`
- Color: `57F287` (green)
- Image: https://example.com/banner.png

---

### Send Plain Text

**Command:**
```
/say message:Hello everyone!
/say message:Update coming soon! channel:#announcements
```

Make the bot say something as plain text.

---

## Utility & Info

### Check Bot Latency

**Command:**
```
/ping
```

Shows ping in milliseconds. If it's high (>500ms), your bot is slow.

---

### Server Info

**Command:**
```
/serverinfo
```

Shows:
- Server owner
- Member count
- Text/voice channel count
- Number of roles
- When server was created

---

### Member Info

**Command:**
```
/userinfo
/userinfo member:@User1
```

Shows:
- When they joined your server
- When their Discord account was created
- All their roles

---

### Get Avatar

**Command:**
```
/avatar
/avatar member:@User1
```

Gets someone's profile picture (useful for saving them).

---

### Credits

**Command:**
```
/credits
```

Shows who made the bot (Made by Fritz).

---

### Help

**Command:**
```
/help
```

Lists all available commands organized by category.

---

## Database

Everything the bot tracks is stored in `bot_data.db` (a local database file):
- XP and levels
- Warnings
- Economy/coins
- Tickets and transcripts
- Roles and permissions
- Everything else

**Backing up:**
1. Close the bot
2. Copy `bot_data.db` to a safe location
3. If bot crashes, replace `bot_data.db` with your backup
4. Restart bot

---

## Troubleshooting

**Commands don't show up:**
- Make sure you enabled Server Members and Message Content intents in Developer Portal
- Restart the bot: stop it and run `python main.py` again
- Wait up to 1 hour (usually appears in 5-10 min)

**Bot can't see messages:**
- Enable Message Content Intent in Developer Portal
- Restart bot

**XP not working:**
- Members must send real messages (not commands)
- There's a 60-second cooldown between messages
- Bot must have permission to see the channels

**Tickets won't create:**
- Run `/ticket-setup` first with valid category
- Bot needs "Create Channel" permission
- Category must exist

**YouTube/Twitch alerts not working:**
- YouTube: Verify channel ID starts with UC and is 24 characters
- Twitch: Check TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET in .env

---

Made by Fritz. MIT License. Attribution required.
