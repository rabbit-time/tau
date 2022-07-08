from __future__ import annotations
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord import Embed, File
from discord.app_commands import checks
from discord.app_commands import guild_only, command, Range
from discord.ext import commands

from utils import Color, Emoji, DigitEmoji
from utils.xp import Rank

if TYPE_CHECKING:
    from tau import Tau


@guild_only()
class Ranks(commands.GroupCog, group_name='ranks'):
    '''Manage rank roles'''
    def __init__(self, bot: Tau):
        self.bot = bot
        self._cooldown = commands.CooldownMapping.from_cooldown(10, 120.0, commands.BucketType.member)

        super().__init__()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        member = message.author
        guild = message.guild
        guild_conf = self.bot.guild_confs(guild)
        if member.bot or guild is None or not guild_conf.leveling:
            return

        await self.bot.wait_until_synced()

        if member not in self.bot.members:
            member_stats = await self.bot.members.add(member)
        else:
            member_stats = self.bot.members(member)

        bucket = self._cooldown.get_bucket(message)
        rate_limited = bucket.update_rate_limit()
        if rate_limited is None:
            # Add xp to user
            level = member_stats.xp.levels
            await member_stats.add_message_xp()

            # Rank roles
            new_level = member_stats.xp.levels
            if guild_conf.ranks.enabled:
                rank_roles = guild_conf.ranks.get_roles()
                rank_levels = guild_conf.ranks.levels()

                new_role = None
                for rank, role in zip(reversed(guild_conf.ranks), reversed(rank_roles)):
                    if new_level >= rank.level:
                        new_role = role
                        break

                for role in rank_roles:
                    if role in member.roles:
                        await member.remove_roles(role)

                if new_role not in member.roles:
                    await member.add_roles(new_role)

                # Level up
                if new_level > level:
                    await message.add_reaction(Emoji.level_up)

                    # Rank up
                    if new_level in rank_levels:
                        await message.add_reaction(Emoji.rank_up)

                    # Add digit emojis
                    for digit_emoji in DigitEmoji.from_int(new_level):
                        await message.add_reaction(digit_emoji)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        guild_conf = self.bot.guild_confs(role.guild)
        roles = guild_conf.ranks.get_roles()
        if role in roles:
            await guild_conf.ranks.remove(role)

    @command(name='view')
    @checks.has_permissions(manage_guild=True)
    async def view(self, interaction: discord.Interaction):
        '''Display rank roles'''
        ranks = self.bot.guild_confs(interaction.guild).ranks
        roles = ranks.get_roles()
        if len(roles) > 0:
            embed = (
                Embed(title='Ranks', color=Color.primary)
                .set_author(name=interaction.guild, icon_url=interaction.guild.icon.url)
            )
            for rank, role in zip(ranks, roles):
                embed.add_field(name=f'Level {rank.level}', value=f'{role.mention}')

            await interaction.response.send_message(embed=embed)
        else:
            embed = (
                Embed(description=f'**{interaction.guild} does not have ranks enabled.**', color=Color.red)
                .set_author(name='Ranks unavailable', icon_url='attachment://unknown.png')
            )
            await interaction.response.send_message(embed=embed, file=File('assets/reddot.png', 'unknown.png'), ephemeral=True)

    @command(name='add')
    @checks.has_permissions(manage_guild=True)
    @checks.bot_has_permissions(manage_roles=True)
    async def add(self, interaction: discord.Interaction, role: discord.Role, level: Range[int, 1]):
        '''Add a role to the rank system'''
        # Check if bot role is higher
        if not role.is_assignable():
            # Role is higher than the bot role itself.
            raise app_commands.AppCommandError

        ranks = self.bot.guild_confs(interaction.guild).ranks
        rank = Rank(role.id, level)
        if rank in ranks:
            # Rank with this role or level already exists
            raise app_commands.AppCommandError

        await ranks.add(rank)

        embed = (
            Embed(color=Color.primary)
            .set_author(name='Rank successfully added', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'))

    @command(name='remove')
    @checks.has_permissions(manage_guild=True)
    async def remove(self, interaction: discord.Interaction, role: discord.Role):
        '''Remove a role from the rank system'''
        ranks = self.bot.guild_confs(interaction.guild).ranks

        rank = Rank(role.id, 0)
        await ranks.remove(rank)

        embed = (
            Embed(color=Color.red)
            .set_author(name='Rank successfully removed', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/reddot.png', 'unknown.png'))


async def setup(bot: Tau):
    await bot.add_cog(Ranks(bot))
