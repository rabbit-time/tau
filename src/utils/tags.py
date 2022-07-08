from __future__ import annotations
from typing import TYPE_CHECKING

from dataclasses import dataclass

import discord
from discord import Embed
from discord.utils import find

from . import aobject

if TYPE_CHECKING:
    from tau import Tau


@dataclass
class Tag:
    guild_id: int
    name: str
    embed: Embed = Embed()
    content: str = ''

    def __iter__(self) -> list[int | str | Embed]:
        attr: list[str] = []
        for anno in self.__annotations__:
            attr.append(getattr(self, anno))

        return attr

    def __eq__(self, other: Tag) -> bool:
        return self.guild_id == other.guild_id and self.name == other.name


class TagHandler(aobject):
    __slots__ = '_bot',
    tags: list[Tag] = []

    async def __init__(self, bot: Tau):
        self._bot = bot
        SCHEMA = (
            'CREATE TABLE IF NOT EXISTS tags (guild_id bigint, name text, embed text, content text, '
            'CONSTRAINT fk_guild FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE)'
        )
        async with self._bot.pool.acquire() as con:
            await con.execute(SCHEMA)

            records = await con.fetch('SELECT * FROM tags')
            for guild_id, name, embed, content in records:
                tag = Tag(guild_id, name, Embed.from_json(embed), content)
                self.tags.append(tag)

    async def add(self, tag: Tag):
        self.tags.append(Tag)
        async with self._bot.pool.acquire() as con:
            await con.execute('INSERT INTO tags VALUES ($1, $2, $3, $4)', *tag)

    async def remove(self, guild: discord.Guild, tag_name: str):
        self.tags.remove(Tag(guild.id, tag_name))
        async with self._bot.pool.acquire() as con:
            await con.execute('DELETE FROM tags WHERE guild_id = $1 AND name = $2', guild.id, tag_name)

    async def get(self, guild: discord.Guild, tag_name: str) -> Tag | None:
        return find(lambda tag: tag.guild_id == guild.id and tag.name == tag_name, self.tags)

    def search(self, guild: discord.Guild, text: str) -> list[Tag]:
        tags = filter(lambda tag: tag.guild_id == guild.id and text in tag.name, self.tags)
        return tags if len(tags) <= 25 else tags[:25]

    def __call__(self, guild: discord.Guild, tag_name: str) -> Tag | None:
        return self.get(guild, tag_name)
