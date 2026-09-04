import asyncio
import logging
import os
from typing import Any

import aiohttp
import discord

log = logging.getLogger("bot.actions")


class ConvexActionWorker:
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.base_url = os.getenv("CONVEX_SITE_URL", "").rstrip("/")
        self.secret = os.getenv("BOT_ACTION_SECRET")

    async def run(self):
        if not self.base_url or not self.secret:
            log.warning("Convex action worker disabled: CONVEX_SITE_URL and BOT_ACTION_SECRET are required")
            return

        headers = {"Authorization": f"Bearer {self.secret}"}
        async with aiohttp.ClientSession(headers=headers) as session:
            while not self.bot.is_closed():
                try:
                    async with session.get(f"{self.base_url}/bot/actions") as response:
                        if response.status != 200:
                            log.error("Convex action poll failed with status %s", response.status)
                        else:
                            for action in await response.json():
                                await self.process(session, action)
                except Exception:
                    log.exception("Convex action worker failed")
                await asyncio.sleep(3)

    async def process(self, session: aiohttp.ClientSession, action: dict[str, Any]):
        action_id = action["_id"]
        await self.post(session, "/bot/actions/claim", {"id": action_id})
        try:
            if action["type"] == "send_message":
                await self.send_message(action)
            elif action["type"] == "send_embed":
                await self.send_embed(action)
            else:
                raise ValueError(f"Unsupported action type: {action['type']}")
        except Exception as error:
            await self.post(session, "/bot/actions/complete", {
                "id": action_id,
                "status": "failed",
                "error": str(error),
            })
            return
        await self.post(session, "/bot/actions/complete", {
            "id": action_id,
            "status": "completed",
        })

    async def send_message(self, action: dict[str, Any]):
        payload = action["payload"]
        channel = self.bot.get_channel(int(payload["channel_id"]))
        if not isinstance(channel, discord.abc.Messageable):
            raise ValueError("Channel not found or not messageable")
        await channel.send(payload["content"])

    async def send_embed(self, action: dict[str, Any]):
        payload = action["payload"]
        channel = self.bot.get_channel(int(payload["channel_id"]))
        if not isinstance(channel, discord.abc.Messageable):
            raise ValueError("Channel not found or not messageable")
        embed = discord.Embed(colour=int(payload.get("color", 0x5865F2)))
        if payload.get("title"):
            embed.title = payload["title"]
        if payload.get("description"):
            embed.description = payload["description"]
        if payload.get("footer"):
            embed.set_footer(text=payload["footer"])
        await channel.send(embed=embed)

    async def post(self, session: aiohttp.ClientSession, path: str, body: dict[str, Any]):
        async with session.post(f"{self.base_url}{path}", json=body) as response:
            if response.status >= 300:
                raise RuntimeError(f"Convex request failed with status {response.status}")
