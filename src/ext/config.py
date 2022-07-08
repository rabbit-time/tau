from __future__ import annotations
from typing import TYPE_CHECKING

import discord
from discord import Embed, File
from discord.app_commands import checks
from discord.app_commands import command, choices, describe, guild_only, rename, Choice, Range
from discord.ext import commands

from utils import Color

if TYPE_CHECKING:
    from tau import Tau


@guild_only()
class Config(commands.GroupCog, group_name='config'):
    def __init__(self, bot: Tau):
        self.bot = bot

        super().__init__()

    @command(name='view')
    @checks.has_permissions(administrator=True)
    async def view(self, interaction: discord.Interaction):
        guild_conf = self.bot.guild_confs(interaction.guild)
        formatted_config = guild_conf.format(interaction.guild)
        embed = (
            Embed(color=Color.primary)
            .set_author(name='Config', icon_url='attachment://unknown.png')
        )
        for key, value in formatted_config.items():
            embed.add_field(name=key, value=value)

        await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'))

    @command(name='starboard')
    @describe(threshold='The number of star reactions needed to be pinned to the starboard')
    @checks.has_permissions(administrator=True)
    async def starboard(self, interaction: discord.Interaction, channel: discord.TextChannel, threshold: Range[int, 1, 256] = None):  # TODO: annotate | None
        '''Modify the starboard'''
        guild_conf = self.bot.guild_confs(interaction.guild)
        await guild_conf.set('starboard_channel_id', channel.id)
        if threshold is not None:
            await guild_conf.set('starboard_threshold', threshold)

        embed = (
            Embed(color=Color.primary)
            .set_author(name=f'star threshold has been set to {threshold}', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'))

    @command(name='welcome')
    @describe(system_channel='The channel used for welcome/goodbye messages. Can be modified in the server settings')
    @checks.has_permissions(administrator=True)
    @checks.bot_has_permissions(manage_guild=True)
    async def welcome(self, interaction: discord.Interaction, text: Range[str, 1, 4096], system_channel: discord.TextChannel | None = None):
        '''Modify the welcome message
        The following are dynamic flags that may be used:
        **`%name  `** - The user's display name.
        **`%user  `** - The user's name and tag (name#0000 format).
        **`%server`** - The server's name.
        '''
        await self.bot.guild_confs(interaction.guild).set('welcome_message', text)
        if system_channel is not None:
            await interaction.guild.edit(system_channel=system_channel)

        embed = (
            Embed(description=text, color=Color.primary)
            .set_author(name=f'Welcome message has been set to:', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'))

    @command(name='goodbye')
    @describe(system_channel='The channel used for welcome/goodbye messages. Can be modified in the server settings')
    @checks.has_permissions(administrator=True)
    @checks.bot_has_permissions(manage_guild=True)
    async def goodbye(self, interaction: discord.Interaction, text: Range[str, 1, 4096], system_channel: discord.TextChannel | None = None):
        '''Modify the goodbye message'''
        await self.bot.guild_confs(interaction.guild).set('goodbye_message', text)
        if system_channel is not None:
            await interaction.guild.edit(system_channel=system_channel)

        embed = (
            Embed(description=text, color=Color.primary)
            .set_author(name=f'Goodbye message has been set to:', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'))

    @command(name='autorole')
    @checks.has_permissions(administrator=True)
    @checks.bot_has_permissions(manage_roles=True)
    async def autorole(self, interaction: discord.Interaction, role: discord.Role):
        '''Modify the autorole. This role is assigned when a user joins'''
        await self.bot.guild_confs(interaction.guild).set('autorole_id', role.id)

        embed = (
            Embed(color=Color.primary)
            .set_author(name=f'Autorole has been set to {role.mention}', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'))

    @command(name='verify_role')
    @checks.has_permissions(administrator=True)
    @checks.bot_has_permissions(manage_roles=True)
    async def verify_role(self, interaction: discord.Interaction, role: discord.Role):
        '''Modify the verify role'''
        await self.bot.guild_confs(interaction.guild).set('verify_role_id', role.id)

        embed = (
            Embed(color=Color.primary)
            .set_author(name=f'Verify role has been set to {role.mention}', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'))

    @command(name='logging')
    @checks.has_permissions(administrator=True)
    @checks.bot_has_permissions(manage_webhooks=True)
    async def logging(self, interaction: discord.Interaction, channel: discord.TextChannel):
        '''Modify the log channel'''
        await self.bot.guild_confs(interaction.guild).set('log_channel_id', channel.id)

        embed = (
            Embed(color=Color.primary)
            .set_author(name=f'Log channel has been set to {channel.mention}', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'))

    @command(name='leveling')
    @rename(enabled='enable')
    @checks.has_permissions(administrator=True)
    @checks.bot_has_permissions(add_reactions=True, external_emojis=True)
    async def leveling(self, interaction: discord.Interaction, enabled: bool):
        '''Toggle XP and leveling'''
        await self.bot.guild_confs(interaction.guild).set('leveling', enabled)

        result = 'enabled' if enabled else 'disabled'
        embed = (
            Embed(color=Color.primary)
            .set_author(name=f'Leveling has been {result}', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'))

    @command(name='disable')
    @choices(option=[
        Choice(name='Welcome messages', value='welcome_message'),
        Choice(name='Goodbye message', value='goodbye_message'),
        Choice(name='Starboard', value='starboard_channel_id'),
        Choice(name='Autorole', value='autorole_id'),
        Choice(name='Verify role', value='verify_role_id'),
        Choice(name='Logging', value='log_channel_id')
    ])
    @checks.has_permissions(administrator=True)
    async def disable(self, interaction: discord.Interaction, option: Choice[str]):
        '''Disable a config option'''
        await self.bot.guild_confs(interaction.guild).set(option.value, None)

        embed = (
            Embed(color=Color.red)
            .set_author(name=f'{option.name} has been disabled', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/reddot.png', 'unknown.png'))


async def setup(bot: Tau):
    await bot.add_cog(Config(bot))
