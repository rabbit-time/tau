from __future__ import annotations
from typing import TYPE_CHECKING

from dataclasses import dataclass
import random

import discord
from discord import Embed
from discord.utils import find

from . import aobject, Color
from .xp import Score, XP

if TYPE_CHECKING:
    from tau import Tau


@dataclass
class ModRecord:
    message: discord.Message
    record_message: discord.Message


class ModRecords:
    __slots__ = '_bot',
    _records: list[ModRecord]

    def __init__(self, bot: Tau):
        self._bot: Tau = bot

    async def get_webhook(self, guild: discord.Guild) -> discord.Webhook | None:
        guild_conf = self._bot.guild_confs(guild)
        if guild_conf.log_channel_id is not None:
            channel = guild.get_channel(guild_conf.log_channel_id)
            webhooks = await channel.webhooks()
            webhook = find(lambda wh: wh.user == self._bot.user, webhooks)
            if webhook is None:
                avatar = self._bot.user.avatar.read()
                webhook = await channel.create_webhook(name=self._bot.user.name, avatar=avatar, reason='Mod logging')

            return webhook

    async def reason(self, message: discord.Message, reason: str):
        success = False
        record = find(lambda record: record.message == message, self._records)
        if record is not None:
            result1 = await self._modify_reason(record.message, reason)
            result2 = await self._modify_reason(record.record_message, reason)

            self._records.remove(record)

            success = result1 and result2

        return success

    @staticmethod
    async def _modify_reason(message: discord.Message, reason) -> bool:
        if len(message.embeds) == 1:
            embed = message.embeds[0]
            if len(embed.fields) == 1 and embed.fields[0].name == 'Reason':
                embed.set_field_at(0, name='Reason', value=f'{reason}')
                try:
                    await message.edit(embed=embed)
                except discord.DiscordException:
                    return False

                return True

        return False

    async def log_ban(self, interaction: discord.Interaction, member: discord.Member, reason: str | None):
        webhook = await self.get_webhook(member.guild)
        if webhook is not None:
            message = await interaction.original_message()
            embed = (
                Embed(description=f'Banned {member}', title='Member ban', color=Color.red)
                .set_author(name=interaction.user, icon_url=interaction.user.avatar)
                .add_field(name='Reason', value=f'*{reason}*')
                .add_field(name='Source', value=f'**[Jump!]({message.jump_url})**')
                .set_footer(text=f'Banned user ID: {member.id}')
            )
            record_message = await webhook.send(embed=embed, wait=True)

            message = await interaction.original_message()
            record = ModRecord(message, record_message)
            self._records.append(record)

    async def log_unban(self, interaction: discord.Interaction, member: discord.Member, reason: str | None):
        webhook = await self.get_webhook(member.guild)
        if webhook is not None:
            message = await interaction.original_message()
            embed = (
                Embed(description=f'Unbanned {member}', title='Member unban', color=Color.green)
                .set_author(name=interaction.user, icon_url=interaction.user.avatar)
                .add_field(name='Reason', value=f'*{reason}*')
                .add_field(name='Source', value=f'**[Jump!]({message.jump_url})**')
                .set_footer(text=f'Unbanned user ID: {member.id}')
            )
            record_message = await webhook.send(embed=embed, wait=True)

            message = await interaction.original_message()
            record = ModRecord(message, record_message)
            self._records.append(record)

    async def log_blacklist(self, interaction: discord.Interaction, member: discord.Member, reason: str | None):
        webhook = await self.get_webhook(member.guild)
        if webhook is not None:
            message = await interaction.original_message()
            embed = (
                Embed(description=f'Blacklisted {member}', title='Member blacklist', color=Color.red)
                .set_author(name=interaction.user, icon_url=interaction.user.avatar)
                .add_field(name='Reason', value=f'*{reason}*')
                .add_field(name='Source', value=f'**[Jump!]({message.jump_url})**')
                .set_footer(text=f'Blacklisted user ID: {member.id}')
            )
            record_message = await webhook.send(embed=embed, wait=True)

            message = await interaction.original_message()
            record = ModRecord(message, record_message)
            self._records.append(record)

    async def log_kick(self, interaction: discord.Interaction, member: discord.Member, reason: str | None):
        webhook = await self.get_webhook(member.guild)
        if webhook is not None:
            message = await interaction.original_message()
            embed = (
                Embed(description=f'Kicked {member}', title='Member kick', color=Color.red)
                .set_author(name=interaction.user, icon_url=interaction.user.avatar)
                .add_field(name='Reason', value=f'*{reason}*')
                .add_field(name='Source', value=f'**[Jump!]({message.jump_url})**')
                .set_footer(text=f'Kicked user ID: {member.id}')
            )
            record_message = await webhook.send(embed=embed, wait=True)

            message = await interaction.original_message()
            record = ModRecord(message, record_message)
            self._records.append(record)

    async def log_mute(self, interaction: discord.Interaction, member: discord.Member, reason: str | None):
        webhook = await self.get_webhook(member.guild)
        if webhook is not None:
            message = await interaction.original_message()
            embed = (
                Embed(description=f'Muted {member}', title='Member mute', color=Color.red)
                .set_author(name=interaction.user, icon_url=interaction.user.avatar)
                .add_field(name='Reason', value=f'*{reason}*')
                .add_field(name='Source', value=f'**[Jump!]({message.jump_url})**')
                .set_footer(text=f'Muted user ID: {member.id}')
            )
            record_message = await webhook.send(embed=embed, wait=True)

            message = await interaction.original_message()
            record = ModRecord(message, record_message)
            self._records.append(record)

    async def log_unmute(self, interaction: discord.Interaction, member: discord.Member, reason: str | None):
        webhook = await self.get_webhook(member.guild)
        if webhook is not None:
            message = await interaction.original_message()
            embed = (
                Embed(description=f'Unmuted {member}', title='Member unmute', color=Color.red)
                .set_author(name=interaction.user, icon_url=interaction.user.avatar)
                .add_field(name='Reason', value=f'*{reason}*')
                .add_field(name='Source', value=f'**[Jump!]({message.jump_url})**')
                .set_footer(text=f'Unmuted user ID: {member.id}')
            )
            record_message = await webhook.send(embed=embed, wait=True)

            message = await interaction.original_message()
            record = ModRecord(message, record_message)
            self._records.append(record)

    async def log_warn(self, interaction: discord.Interaction, member: discord.Member, reason: str | None):
        webhook = await self.get_webhook(member.guild)
        if webhook is not None:
            message = await interaction.original_message()
            embed = (
                Embed(description=f'Warned {member}', title='Member warn', color=Color.gold)
                .set_author(name=interaction.user, icon_url=interaction.user.avatar)
                .add_field(name='Reason', value=f'*{reason}*')
                .add_field(name='Source', value=f'**[Jump!]({message.jump_url})**')
                .set_footer(text=f'Warned user ID: {member.id}')
            )
            record_message = await webhook.send(embed=embed, wait=True)

            message = await interaction.original_message()
            record = ModRecord(message, record_message)
            self._records.append(record)

    async def log_verify(self, interaction: discord.Interaction, member: discord.Member):
        webhook = await self.get_webhook(member.guild)
        if webhook is not None:
            message = await interaction.original_message()
            embed = (
                Embed(description=f'Verified {member}', title='Member verify', color=Color.green)
                .set_author(name=interaction.user, icon_url=interaction.user.avatar)
                .add_field(name='Source', value=f'**[Jump!]({message.jump_url})**')
                .set_footer(text=f'Verified user ID: {member.id}')
            )
            record_message = await webhook.send(embed=embed, wait=True)

            message = await interaction.original_message()
            record = ModRecord(message, record_message)
            self._records.append(record)

    async def log_unverify(self, interaction: discord.Interaction, member: discord.Member, reason: str | None):
        webhook = await self.get_webhook(member.guild)
        if webhook is not None:
            message = await interaction.original_message()
            embed = (
                Embed(description=f'Unverified {member}', title='Member unverify', color=Color.red)
                .set_author(name=interaction.user, icon_url=interaction.user.avatar)
                .add_field(name='Reason', value=f'*{reason}*')
                .add_field(name='Source', value=f'**[Jump!]({message.jump_url})**')
                .set_footer(text=f'Unverified user ID: {member.id}')
            )
            record_message = await webhook.send(embed=embed, wait=True)

            message = await interaction.original_message()
            record = ModRecord(message, record_message)
            self._records.append(record)


class MemberStats:
    __slots__ = '_bot', '_id', 'guild_id', 'xp', 'credits'

    def __init__(self, bot: Tau, id: int, guild_id: int, xp_points: int = 0, credits: int = 0):
        self._bot: Tau = bot
        self._id: int = id
        self.guild_id: int = guild_id
        self.xp: XP = XP(xp_points)
        self.credits: int = credits

    @property
    def id(self) -> int:
        return self._id

    # For easy comparison using __eq__
    @property
    def guild(self) -> discord.Object:
        return discord.Object(id=self.guild_id)

    async def add_xp(self, points: int):
        self.xp.points += points
        async with self._bot.pool.acquire() as con:
            await con.execute('UPDATE members SET xp_points = $1 WHERE id = $2 AND guild_id = $3', self.xp.points, self._id, self.guild_id)

    async def add_message_xp(self):
        points = random.randint(1, 5)
        await self.add_xp(points)

    async def set_xp(self, points: int):
        self.xp.points = points
        async with self._bot.pool.acquire() as con:
            await con.execute('UPDATE members SET xp_points = $1 WHERE id = $2 AND guild_id = $3', self.xp.points, self._id, self.guild_id)

    async def add_credits(self, credits: int):
        self.credits += credits
        async with self._bot.pool.acquire() as con:
            await con.execute('UPDATE members SET credits = $1 WHERE id = $2 AND guild_id = $3', self.credits, self._id, self.guild_id)

    def __eq__(self, other: discord.Member | MemberStats) -> bool:
        return self.id is other.id and self.guild.id is other.guild.id


class MemberTracker(aobject):
    __slots__ = '_bot',
    member_stats: list[MemberStats] = []

    async def __init__(self, bot: Tau):
        self._bot = bot
        MEMBERS_SCHEMA = (
            'CREATE TABLE IF NOT EXISTS members (id bigint, guild_id bigint, xp_points bigint DEFAULT 0, credits bigint DEFAULT 0, '
            'CONSTRAINT fk_guild FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE)'
        )
        async with self._bot.pool.acquire() as con:
            await con.execute(MEMBERS_SCHEMA)

            # Check if members still exist and fill the cache
            records = await con.fetch('SELECT * FROM members ORDER BY guild_id')
            if len(records) > 0:
                guild = self._bot.get_guild(records[0]['guild_id'])
                for record in records:
                    guild_id: int = record['guild_id']
                    if guild.id != guild_id:
                        guild = self._bot.get_guild(guild_id)

                    member = guild.get_member(record['id'])
                    if member:
                        member_stats = MemberStats(self._bot, *tuple(record))
                        self.member_stats.append(member_stats)
                    else:
                        await con.execute('DELETE FROM members WHERE id = $1 AND guild_id = $2', member.id, guild.id)

    async def add(self, member: discord.Member) -> MemberStats:
        member_stats = MemberStats(self._bot, member.id, member.guild.id)
        self.member_stats.append(member_stats)
        async with self._bot.pool.acquire() as con:
            await con.execute('INSERT INTO members (id, guild_id) VALUES ($1, $2)', member.id, member.guild.id)

        return member_stats

    async def remove(self, member: discord.Member):
        self.member_stats.remove(member)
        async with self._bot.pool.acquire() as con:
            await con.execute('DELETE FROM members WHERE id = $1 AND guild_id = $2', member.id, member.guild.id)

    def get(self, member: discord.Member) -> MemberStats | None:
        return find(lambda ms: ms == member, self.member_stats)

    async def fetch_highscores(self, guild: discord.Guild) -> tuple[Score]:
        scores: list[Score] = []
        async with self._bot.pool.acquire() as con:
            async for id, xp_points in con.cursor('SELECT id, xp_points FROM members WHERE guild_id = $1 ORDER BY xp_points DESC', guild.id):
                member = guild.get_member(id)
                if member is not None:
                    scores.append(Score(member, XP(xp_points)))
                    if len(scores) == 10:
                        break

        return tuple(scores)

    def __call__(self, member: discord.Member) -> MemberStats | None:
        return self.get(member)

    def __contains__(self, member: discord.Member) -> bool:
        return member in self.member_stats

    def __iter__(self) -> list[MemberStats]:
        return self.member_stats
