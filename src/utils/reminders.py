from __future__ import annotations
from typing import TYPE_CHECKING

import asyncio
import datetime

import discord
from discord import Embed, File

from . import aobject, Color

if TYPE_CHECKING:
    from tau import Tau


class Reminder:
    __slots__ = 'user', 'channel', 'delta', 'time', 'text'

    def __init__(self, user: discord.User | discord.Member, channel: discord.TextChannel, time: datetime.datetime, text: str):
        self.user: discord.User = user
        self.channel: discord.TextChannel = channel
        self.delta: datetime.timedelta = time - discord.utils.utcnow()
        self.time: datetime.datetime = time
        self.text: str = text

    @classmethod
    def from_relative(cls, user: discord.User, channel: discord.TextChannel, days: int, hours: int, minutes: int, text: str) -> Reminder:
        time = discord.utils.utcnow() + datetime.timedelta(days=days, hours=hours, minutes=minutes)
        return cls(user, channel, time, text)

    def __str__(self) -> str:
        return self.text


class ReminderHandler(aobject):
    __slots__ = '_bot',

    async def __init__(self, bot: Tau):
        self._bot = bot
        SCHEMA = 'CREATE TABLE IF NOT EXISTS reminders (user_id bigint, channel_id bigint, time timestamptz, reminder text)'
        async with self._bot.pool.acquire() as con:
            await con.execute(SCHEMA)

            # Handle persisting reminders
            records = await con.fetch('SELECT * FROM reminders')
            for user_id, channel_id, time, text in records:
                valid = False
                channel = self._bot.get_channel(channel_id)  # Bot.get_channel is slow, however this is just during start-up.
                if channel:
                    member = channel.guild.get_member(user_id)
                    if member:
                        reminder = Reminder(member, channel, time, text)
                        asyncio.create_task(self.activate(reminder))
                        valid = True

                # In case the channel or user no longer exists
                if not valid:
                    async with self._bot.pool.acquire() as con:
                        stmt = 'DELETE FROM reminders WHERE user_id = $1 AND channel_id = $2 AND time = $3 AND reminder = $4'
                        await con.execute(stmt, user_id, channel_id, time, text)

    async def activate(self, reminder: Reminder):
        now = discord.utils.utcnow()
        remainder = (reminder.time-now).total_seconds()
        await asyncio.sleep(remainder)

        files = [File('assets/dot.png', 'unknown.png'), File('assets/clock.png', 'unknown1.png')]
        embed = (
            Embed(description=f'>>> {reminder}', color=Color.primary)
            .set_author(name='Reminder', icon_url='attachment://unknown.png')
            .set_footer(text='Time\'s up!', icon_url='attachment://unknown1.png')
        )
        await reminder.channel.send(reminder.user.mention, embed=embed, files=files)

        await self.remove(reminder)

    async def add(self, reminder: Reminder):
        async with self._bot.pool.acquire() as con:
            stmt = 'INSERT INTO reminders VALUES ($1, $2, $3, $4)'
            await con.execute(stmt, reminder.user.id, reminder.channel.id, reminder.time, reminder.text)

        asyncio.create_task(self.activate(reminder))

    async def remove(self, reminder: Reminder):
        async with self._bot.pool.acquire() as con:
            stmt = 'DELETE FROM reminders WHERE user_id = $1 AND channel_id = $2 AND time = $3 AND reminder = $4'
            await con.execute(stmt, reminder.user.id, reminder.channel.id, reminder.time, reminder.text)

    async def remove_user(self, user: discord.User):
        async with self._bot.pool.acquire() as con:
            await con.execute('DELETE FROM reminders WHERE user_id = $1', user.id)

    async def remove_channel(self, channel: discord.abc.GuildChannel):
        async with self._bot.pool.acquire() as con:
            await con.execute('DELETE FROM reminders WHERE channel_id = $1', channel.id)
