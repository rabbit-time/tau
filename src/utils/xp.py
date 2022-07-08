from __future__ import annotations
from typing import Any, TYPE_CHECKING

import heapq
from dataclasses import dataclass
from math import sqrt

import discord

from . import aobject

if TYPE_CHECKING:
    from tau import Tau


@dataclass
class XP:
    points: int

    @property
    def levels(self) -> int:
        return int(sqrt(self.points + 121/4) - 11/2)

    @staticmethod
    def level_diff(u: int, v: int) -> int:
        '''Point difference between two levels'''
        return abs(XP.from_(v) - XP.from_(u))

    @classmethod
    def from_(cls, levels: int) -> XP:
        points = levels ** 2 + 11 * levels
        return cls(points=points)

    def __add__(self, other: XP) -> int:
        return self.points + other.points

    def __sub__(self, other: XP) -> int:
        return self.points - other.points


@dataclass
class Score:
    member: discord.Member
    xp: XP


@dataclass
class Rank:
    id: int
    level: int

    def __eq__(self, other: Rank) -> bool:
        # Guarantees that two ranks never have the same role or level
        return self.id is other.id or self.level is other.level

    def __ge__(self, other: Rank) -> bool:
        return self.level >= other.level

    def __le__(self, other: Rank) -> bool:
        return self.level <= other.level


class Ranks(aobject):
    __slots__ = '_bot', 'guild_id'
    _ranks: list[Rank] = []  # Ascending order by level, implemented as a heapq

    async def __init__(self, bot: Tau, guild_id: int):
        self._bot = bot
        self.guild_id = guild_id
        async with self._bot.pool.acquire() as con:
            record = await con.fetchrow('SELECT role_ids, levels FROM ranks WHERE guild_id = $1 ORDER BY levels ASC', guild_id)
            if record is not None:
                for role_id, level in zip(record['role_ids'], record['levels']):
                    guild = self._bot.get_guild(self.guild_id)
                    role = guild.get_role(role_id)
                    if role is not None:
                        rank = Rank(role_id, level)
                        heapq.heappush(self._ranks, rank)
                    else:
                        await self.remove(role)

    def ids(self) -> list[int]:
        return [rank.id for rank in self._ranks]

    def levels(self) -> list[int]:
        return [rank.level for rank in self._ranks]

    def get_roles(self) -> list[discord.Role]:
        guild = self._bot.get_guild(self.guild_id)

        return [guild.get_role(rank.role_id) for rank in self._ranks]

    async def add(self, rank: Rank):
        heapq.heappush(self._ranks, rank)
        await self._update()

    async def remove(self, rank: Rank):
        try:
            self._ranks.remove(rank)
        except ValueError:
            pass

        await self._update()

    async def _update(self):
        async with self._bot.pool.acquire() as con:
            await con.execute('UPDATE ranks SET role_ids = $1, levels = $2 WHERE guild_id = $3', self.ids(), self.levels(), self.guild_id)

    @property
    def enabled(self):
        return len(self._ranks) > 0

    def __iter__(self) -> list[Rank]:
        return self._ranks

    def __contains__(self, rank: Rank) -> bool:
        return rank in self._ranks

    def __getitem__(self, i: int) -> Rank:
        return self._ranks[i]

    def __len__(self) -> int:
        return len(self._ranks)

    def __eq__(self, other: Any) -> bool:
        return self._ranks == other
