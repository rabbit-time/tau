from __future__ import annotations
from typing import TYPE_CHECKING

import discord
from discord.utils import find

from . import aobject
from .xp import Ranks

if TYPE_CHECKING:
    from tau import Tau


class GuildConf(aobject):
    __slots__ = (
        '_bot', '_id', 'welcome_message', 'goodbye_message', 'starboard_channel_id',
        'starboard_threshold', 'autorole_id', 'verify_role_id', 'log_channel_id', 'leveling', '_ranks'
    )

    async def __init__(
        self,
        bot: Tau,
        id: int,
        welcome_message: str | None = None,
        goodbye_message: str | None = None,
        starboard_channel_id: int | None = None,
        starboard_threshold: int = 3,
        autorole_id: int | None = None,
        verify_role_id: int | None = None,
        log_channel_id: int | None = None,
        leveling: bool = False
    ):
        # Checking if these values are still valid
        guild = bot.get_guild(id)

        self._bot: Tau = bot
        self._id: int = id
        self.welcome_message: str | None = welcome_message
        self.goodbye_message: str | None = goodbye_message

        starboard = guild.get_channel(starboard_channel_id)
        self.starboard_channel_id: int | None = starboard.id if starboard is not None else None

        self.starboard_threshold: int = starboard_threshold

        autorole = guild.get_role(autorole_id)
        self.autorole_id: int | None = autorole.id if autorole is not None else None

        verify_role = guild.get_role(verify_role_id)
        self.verify_role_id: int | None = verify_role.id if verify_role is not None else None

        log_channel = guild.get_channel(log_channel_id)
        self.log_channel_id: int | None = log_channel.id if log_channel is not None else None

        self.leveling: bool = leveling
        self._ranks: Ranks = await Ranks(self._bot, self.id)

    @property
    def id(self) -> int:
        return self._id

    @property
    def ranks(self) -> Ranks:
        return self._ranks

    async def set(self, key: str, value: any):
        setattr(self, key, value)
        async with self._bot.pool.acquire() as con:
            await con.execute(f'UPDATE guilds SET {key} = $1 WHERE id = $2', value, self.id)

    def format(self, guild: discord.Guild) -> dict:
        clipped_welcome_message = self._clip_str(self.welcome_message) if self.welcome_message is not None else None
        clipped_goodbye_message = self._clip_str(self.goodbye_message) if self.goodbye_message is not None else None
        system_channel = guild.system_channel
        starboard = guild.get_channel(self.starboard_channel_id)
        autorole = guild.get_role(self.autorole_id)
        verify_role = guild.get_channel(self.verify_role_id)
        log_channel = guild.get_channel(self.log_channel_id)
        leveling = 'Enabled' if self.leveling else 'Disabled'

        return {
            'Welcome message': clipped_welcome_message,
            'Goodbye message': clipped_goodbye_message,
            'System channel': system_channel.mention if system_channel is not None else None,
            'Starboard channel': starboard.mention if starboard is not None else None,
            'Starboard threshold': self.starboard_threshold,
            'Autorole': autorole.mention if autorole is not None else None,
            'Verify role': verify_role.mention if verify_role is not None else None,
            'Log channel': log_channel.mention if log_channel is not None else None,
            'Leveling': leveling
        }

    def _clip_str(self, string: str) -> str:
        '''Clip a string for formatting purposes'''
        length = 30  # The length that the string should be clipped down to.
        stripped = string.rstrip('.')
        if len(stripped) > length:
            index = stripped[:length+1].rindex(' ')
            clipped = stripped[:index] + '...'

            return clipped
        else:
            return stripped

    def __eq__(self, guild: discord.Guild | GuildConf) -> bool:
        return self.id == guild.id


class GuildHandler(aobject):
    __slots__ = '_bot'
    guild_confs: list[GuildConf] = []

    async def __init__(self, bot: Tau):
        self._bot = bot
        GUILD_SCHEMA = (
            'CREATE TABLE IF NOT EXISTS guilds (id bigint PRIMARY KEY, welcome_message text, goodbye_message text, '
            'starboard_channel_id bigint, starboard_threshold smallint DEFAULT 3, autorole_id bigint, verify_role_id bigint, '
            'log_channel_id bigint, leveling boolean DEFAULT FALSE)'
        )
        RANKS_SCHEMA = (
            'CREATE TABLE IF NOT EXISTS ranks (guild_id bigint PRIMARY KEY, role_ids bigint[] DEFAULT \'{}\', levels bigint[] DEFAULT \'{}\', '
            'CONSTRAINT fk_guild FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE)'
        )
        async with self._bot.pool.acquire() as con:
            await con.execute(GUILD_SCHEMA)
            await con.execute(RANKS_SCHEMA)

            # Check if guilds are still valid and fill the cache
            records = await con.fetch('SELECT * FROM guilds')
            for record in records:
                guild_id = record['id']
                guild = self._bot.get_guild(guild_id)
                if guild is not None:
                    guild_conf = await GuildConf(self._bot, *tuple(record))
                    self.guild_confs.append(guild_conf)
                else:
                    await con.execute('DELETE FROM guilds WHERE id = $1', guild_id)

        # Add any new guilds that were added while bot was offline
        for guild in self._bot.guilds:
            if guild not in self.guild_confs:
                await self.add(guild)

    async def add(self, guild: discord.Guild):
        guild_conf = await GuildConf(self._bot, guild.id)
        self.guild_confs.append(guild_conf)
        async with self._bot.pool.acquire() as con:
            await con.execute('INSERT INTO guilds (id) VALUES ($1)', guild.id)
            await con.execute('INSERT INTO ranks (guild_id) VALUES ($1)', guild.id)

    async def remove(self, guild: discord.Guild):
        self.guild_confs.remove(guild)
        async with self._bot.pool.acquire() as con:
            await con.execute('DELETE FROM guilds WHERE id = $1', guild.id)

    def get(self, guild: discord.Guild) -> GuildConf | None:
        return find(lambda g: g == guild, self.guild_confs)

    def __call__(self, guild: discord.Guild) -> GuildConf | None:
        return self.get(guild)

    def __contains__(self, guild: discord.Guild) -> bool:
        return guild in self.guild_confs

    def __iter__(self) -> list[GuildConf]:
        return self.guild_confs
