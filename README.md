# TrillBot

[![Build, Test and Deploy](https://github.com/ceptoplex/trillbot-discord/actions/workflows/build-test-deploy.yml/badge.svg)](https://github.com/ceptoplex/trillbot-discord/actions/workflows/build-test-deploy.yml)

This bot manages the [TrilluXe Community](https://discord.gg/trilluxe) Discord server. The server is owned
by [TrilluXe](https://twitter.com/trilluxe). The maintainer of this bot is [ceptoplex](https://twitter.com/ceptoplex).
Found a bug or got an idea for a new
feature? [Community contributions](https://github.com/ceptoplex/trillbot/blob/master/CONTRIBUTING.md) are possible.

[![Discord](https://discordapp.com/api/guilds/314010693084905494/widget.png)](https://discord.gg/trilluxe)
[![Twitter: Follow @trilluxe](https://img.shields.io/twitter/follow/trilluxe?style=social)](https://twitter.com/trilluxe)
[![Twitter: Follow @ceptoplex](https://img.shields.io/twitter/follow/ceptoplex?style=social)](https://twitter.com/ceptoplex)

## 1 Functionality

The bot offers the following functionality:

- __Anti-Abuse:__ Detect and mitigate abuse.
    - Kick users that try to impersonate TrilluXe, the bot or any other VIP.
    - Prevent bot waves to flood the server.
- __Elastic Voice Channels:__ Replicate voice channels automatically. This ensures that there is always one empty voice
  channel available of each existing type (where different types means different names or different user limits).

## 2 Configuration

To configure the bot, use system environment variables. They have to start with the prefix `TRILLBOT_`. The following
settings exist:

- `TRILLBOT_DISCORD_TOKEN` (string)

  The Discord bot token of the Discord developer application that should be used.

## 3 Execution

### Python 3.9

    ~$ pip3 install -r requirements
    ~$ cd src
    ~$ set TRILLBOT_DISCORD_TOKEN={...}
    ~$ python3 -m trillbot

### Docker

    ~$ docker build -t trillbot-discord .
    ~$ docker run -e TRILLBOT_DISCORD_TOKEN={...} trillbot-discord

### Invitation to Discord Server

To invite the bot to a Discord server, the following URL should be used (after filling in the OAuth2 client ID of your
Discord developer application):

    https://discordapp.com/api/oauth2/authorize?client_id={...}&permissions=8&scope=bot

It includes the OAuth2 scope `bot` and the `Administrator` permission.
