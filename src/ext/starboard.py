from __future__ import annotations
from typing import TYPE_CHECKING

import asyncio

import discord
from discord.ext import commands

from utils.starboards import Starboard

if TYPE_CHECKING:
    from tau import Tau


class Starboard_(commands.Cog, name='Starboard'):
    def __init__(self, bot: Tau):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        await self.bot.wait_until_synced()

        guild_conf = self.bot.guild_confs(channel.guild)
        if channel.id == guild_conf.starboard_channel_id:
            await guild_conf.set('starboard_channel_id', None)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.member is None or str(payload.emoji) != '⭐':
            return

        starboard = Starboard(self.bot, payload.member.guild)
        channel = starboard.guild.get_channel(payload.channel_id)
        if starboard.channel is None or channel is None or starboard.channel == channel:
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except (discord.NotFound, discord.Forbidden):
            return

        stars = starboard.count_stars(message)

        if stars < starboard.threshold:
            return

        embed = starboard.embed(message)
        star_emoji = starboard.star_emoji(stars)
        starboard_message = await self.bot.starboards.fetch(message, starboard)
        if starboard_message is not None:
            await starboard_message.edit(f'{star_emoji} **{stars}**', embed=embed)
        else:
            async with asyncio.Lock():
                starboard_message = await starboard.channel.send(f'{star_emoji} **{stars}**', embed=embed)
                await self.bot.starboards.add(message, starboard_message)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.member is None or str(payload.emoji) != '⭐':
            return

        starboard = Starboard(self.bot, payload.member.guild)
        channel = starboard.guild.get_channel(payload.channel_id)
        if starboard.channel is None or channel is None or starboard.channel == channel:
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except (discord.NotFound, discord.Forbidden):
            return

        stars = starboard.count_stars(message)
        embed = starboard.embed(message)
        star_emoji = starboard.star_emoji(stars)
        starboard_message = await self.bot.starboards.fetch(message, starboard)
        if starboard_message is not None:
            await starboard_message.edit(f'{star_emoji} **{stars}**', embed=embed)
        else:
            await self.bot.starboards.remove(message)


async def setup(bot: Tau):
    await bot.add_cog(Starboard_(bot))
