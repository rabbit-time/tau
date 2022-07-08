from __future__ import annotations
from typing import Literal, TYPE_CHECKING

import discord
from discord import Embed, File
from discord.app_commands import checks
from discord.app_commands import command, describe, guilds, Transform
from discord.ext import commands

from utils import Color, Config, GuildTransformer
from utils.xp import XP

config = Config.from_json('config.json')

if TYPE_CHECKING:
    from tau import Tau


class Developer(commands.Cog):
    '''A collection of developer tools'''
    def __init__(self, bot: Tau):
        self.bot = bot

    @command(name='add_xp')
    @guilds(discord.Object(id=config.developer_guild_id))
    @checks.has_permissions(administrator=True)
    async def add_xp(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        guild: Transform[discord.Guild, GuildTransformer],
        xp: int,
        unit: Literal['points', 'levels']
    ):
        '''Add xp to a member (developer use only)'''
        if user.bot:
            return

        member = guild.get_member(user.id)
        if member not in self.bot.members:
            await self.bot.members.add(member)

        member_stats = self.bot.members(member)
        if unit == 'points':
            points = xp
        else:
            # Convert levels to points
            level = member_stats.xp.levels()
            points = XP.level_diff(level, level+xp)

        await member_stats.add_xp(points)

        embed = (
            Embed(color=Color.primary)
            .set_author(name=f'Added {xp} {unit} to {user}', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'))

    @command(name='set_xp')
    @guilds(discord.Object(id=config.developer_guild_id))
    async def set_xp(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        guild: Transform[discord.Guild, GuildTransformer],
        xp: int,
        unit: Literal['points', 'levels']
    ):
        '''Set a member's xp (developer use only)'''
        if user.bot:
            return

        member = guild.get_member(user.id)
        if member not in self.bot.members:
            await self.bot.members.add(member)

        member_stats = self.bot.members(member)
        if unit == 'points':
            points = xp
        else:
            # Convert levels to points
            points = XP.from_(xp).points

        await member_stats.set_xp(points)

        embed = (
            Embed(color=Color.primary)
            .set_author(name=f'{user}\'s XP set to {xp} XP {unit}', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'))

    @command(name='reload')
    @guilds(discord.Object(id=config.developer_guild_id))
    async def reload(self, interaction: discord.Interaction, extension: str):
        '''Reload an extension (developer use only)'''
        try:
            await self.bot.reload_extension(f'ext.{extension}')

            desc = f'ext.{extension} has been reloaded.'
            color = Color.green
            color_name = 'green'
        except Exception as err:
            desc = err
            color = Color.red
            color_name = 'red'

        embed = (
            Embed(color=color)
            .set_author(name=desc, icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File(f'assets/{color_name}dot.png', 'unknown.png'))

    @command(name='remove')
    @guilds(discord.Object(id=config.developer_guild_id))
    @describe(guild='The ID of the guild to be removed')
    async def remove(self, interaction: discord.Interaction, *, guild: Transform[discord.Guild, GuildTransformer]):
        '''Remove a server (developer use only)'''
        guild = self.bot.get_guild(id)

        embed = (
            Embed(color=Color.red)
            .set_author(name=f'{guild.name} has been removed', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/reddot.png', 'unknown.png'))


async def setup(bot: Tau):
    await bot.add_cog(Developer(bot))
