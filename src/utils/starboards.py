from __future__ import annotations
from typing import TYPE_CHECKING

import discord
from discord import Embed

from . import aobject, Color

if TYPE_CHECKING:
    from tau import Tau


class Starboard:
    __slots__ = '_bot', '_guild', '_id', '_threshold', '_channel'

    def __init__(self, bot: Tau, guild: discord.Guild):
        self._bot: Tau = bot
        self._guild: discord.Guild = guild
        self._id: int = self._bot.guild_confs(guild).starboard_channel_id
        self._threshold: int = self._bot.guild_confs(guild).starboard_threshold
        self._channel: discord.TextChannel | None = self.guild.get_channel(self.id)

    @property
    def guild(self) -> discord.Guild:
        return self._guild

    @property
    def id(self) -> int:
        return self._id

    @property
    def threshold(self) -> int:
        return self._threshold

    @property
    def channel(self) -> discord.TextChannel:
        return self._channel

    @staticmethod
    def star_emoji(stars: int) -> str:
        match stars:
            case s if 5 > s >= 0:
                return '⭐'
            case s if 10 > s >= 5:
                return '🌟'
            case s if 25 > s >= 10:
                return '💫'
            case _:
                return '✨'

    @staticmethod
    def count_stars(message: discord.Message) -> int:
        stars: int = 0
        for reaction in message.reactions:
            if str(reaction.emoji) == '⭐':
                stars += reaction.count

        return stars

    @staticmethod
    def embed(message: discord.Message) -> discord.Embed:
        url = None
        if message.attachments:
            file = message.attachments[0]
            if file.url.lower().endswith(('png', 'jpeg', 'jpg', 'gif', 'webp')):
                url = file.url

        embed = (
            Embed(description=message.content, color=Color.yellow)
            .set_author(name=message.author.display_name, icon_url=message.author.avatar)
            .add_field(name='Source', value=f'**[Jump!]({message.jump_url})**')
            .set_footer(text=message.id)
            .set_image(url=url)
        )
        embed.timestamp = message.created_at

        return embed


class StarboardHandler(aobject):
    __slots__ = '_bot',

    async def __init__(self, bot: Tau):
        self._bot = bot
        SCHEMA = (
            'CREATE TABLE IF NOT EXISTS starboard (message_id bigint PRIMARY KEY, starboard_message_id bigint, guild_id bigint, '
            'CONSTRAINT fk_guild FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE)'
        )
        async with self._bot.pool.acquire() as con:
            await con.execute(SCHEMA)

    async def add(self, message: discord.Message, starboard_message: discord.Message):
        async with self._bot.pool.acquire() as con:
            await con.execute('INSERT INTO starboard VALUES ($1, $2, $3)', message.id, starboard_message.id, message.guild.id)

    async def remove(self, message: discord.Message):
        async with self._bot.pool.acquire() as con:
            await con.execute('DELETE FROM starboard WHERE message_id = $1', message.id)

    async def fetch(self, message: discord.Message, starboard: Starboard) -> discord.Message | None:
        starboard_message = None
        async with self._bot.pool.acquire() as con:
            record = await con.fetchrow('SELECT starboard_message_id FROM starboard WHERE message_id = $1', message.id)
            if record is not None:
                starboard_message_id = record['starboard_message_id']
                try:
                    starboard_message = await starboard.channel.fetch_message(starboard_message_id)
                except (discord.NotFound, discord.Forbidden):
                    pass

            return starboard_message
