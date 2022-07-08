from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import datetime

import discord
from discord import app_commands
from discord import Embed, File
from discord.app_commands import checks
from discord.app_commands import command, guild_only, Range
from discord.ext import commands

from utils import Color

if TYPE_CHECKING:
    from tau import Tau


class Economy(commands.Cog):
    def __init__(self, bot: Tau):
        self.bot = bot

    @command(name='balance')
    @guild_only()
    async def balance(self, interaction: discord.Interaction, member: discord.Member | None = None):
        '''Display user credit balance'''
        if member is not None and member not in self.bot.members:
            await self.bot.members.add(member)

        member_stats = self.bot.members(member=member if member else interaction.user)
        embed = (
            Embed(color=Color.primary)
            .set_author(name=member_stats.credits, icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/credits.png', 'unknown.png'))

    @command(name='give')
    @guild_only()
    async def give(self, interaction: discord.Interaction, member: discord.Member, amount: Range[int, 1]):
        '''Give your credits to another member'''
        if member.bot or member == interaction.user:
            raise app_commands.AppCommandError

        if member not in self.bot.members:
            await self.bot.members.add(member)

        sender_stats = self.bot.members(interaction.user)
        receiver_stats = self.bot.members(member)
        diff = sender_stats.credits - amount
        if diff < 0:
            raise app_commands.AppCommandError

        await sender_stats.add_credits(-amount)
        await receiver_stats.add_credits(amount)

        embed = (
            Embed(color=Color.primary)
            .set_author(name=f'Gave {amount} credits to {member.mention}!', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/credits.png', 'unknown.png'))

    @command(name='credits')
    @checks.cooldown(1, 86400.0)  # 24-hour cooldown
    @guild_only()
    async def credits(self, interaction: discord.Interaction):
        '''Collect your daily credits (cooldown: 24 hours)'''
        member_stats = self.bot.members(interaction.user)
        amount = 10
        if datetime.today().weekday() == 6:  # Sunday
            amount *= 2

        await member_stats.add_credits(amount)

        embed = (
            Embed(color=Color.primary)
            .set_author(name=f'Collected {amount} credits for a new balance of {member_stats.credits}!', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/credits.png', 'unknown.png'))


async def setup(bot: Tau):
    await bot.add_cog(Economy(bot))
