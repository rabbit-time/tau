from __future__ import annotations
from typing import TYPE_CHECKING

import platform

import discord
from discord import Embed, File
from discord.app_commands import command, describe
from discord.ext import commands

from utils import Color

if TYPE_CHECKING:
    from tau import Tau


class Info(commands.Cog):
    def __init__(self, bot: Tau):
        self.bot = bot

    @command(name='avatar')
    @describe(user='the target user, defaults to yourself')
    async def avatar(self, interaction: discord.Interaction, *, user: discord.User | None = None):
        '''View user avatar'''
        if user is None:
            user = interaction.user

        png = user.display_avatar.replace(format='png').url
        jpg = user.display_avatar.replace(format='jpg').url
        webp = user.display_avatar.replace(format='webp').url
        formats = [f'[`.png`]({png})', f'[`.jpg`]({jpg})', f'[`.webp`]({webp})']
        if user.display_avatar.is_animated():
            gif = user.display_avatar.replace(format='gif').url
            formats.append(f'[`.gif`]({gif})')

        delimiter = '\u2002|\u2002'  # These are wide spaces
        embed = (
            Embed(description=f':link: **{delimiter.join(formats)}**', color=Color.cyan)
            .set_author(name=user.display_name, icon_url=user.display_avatar.url)
            .set_image(url=user.display_avatar.url)
        )
        await interaction.response.send_message(embed=embed)

    # TODO: Implement
    '''
    @command(name='commands')
    async def commands_(self, interaction: discord.Interaction):
        \'\'\'Display the full list of commands\'\'\'
        cogs = sorted(list(filter(lambda cog: len(cog[1].get_commands()) > 0, self.bot.cogs.items())), key=lambda cog: cog[0])
        description = 'Here\'s a list of available commands. For further detail on a command, use **`/cmd [command]`**.'
        embed = (
            Embed(description=description, color=Color.primary)
            .set_author(name='Commands', icon_url='attachment://unknown.png')
            .set_image(url='attachment://unknown1.png')
        )
        for cog in cogs:
            commands = cog[1].get_commands()
            sorted_commands = sorted(commands, key=lambda command: command.name)
            command_names = ' '.join(f'`{command.name}`' for command in sorted_commands)
            embed.add_field(name=cog[0], value=f'**{command_names}**', inline=False)

        files = [File('assets/dot.png', 'unknown.png'), File(f'assets/bar.png', 'unknown1.png'), File('assets/info.png', 'unknown2.png')]

        await interaction.response.send_message(embed=embed, files=files)

    @command(name='help')
    async def help(self, interaction: discord.Interaction):
        \'\'\'Display the help message\'\'\'
        # links = f'**[Invite]({self.bot.url})', f'[Server]({config.invite})', f'[GitHub]({config.repo})**''
        files = [File(f'assets/dot.png', 'unknown.png'), File(f'assets/bar.png', 'unknown1.png')]
        description = (
            'The current prefix is set to: **`/`**\n\nIf you\'re just getting started, it is recommended '
            'that you go through the **`/setup`** process before anything else! (admin-only)\n\n'
            '**Looking for the full list of commands?**\nTry typing **`/commands`** or **`/cmd`** for short.\n\n'
            '**Voice your opinion!**\nUse the **`/feedback`** command for suggestions and bug reports.\n\n'
            '**Learn more:**\nFor more information about the bot, use the **`/tau`** command.'
        )
        embed = Embed(description=description, color=Color.primary)
        embed.set_author(name='Help', icon_url='attachment://unknown.png')
        embed.add_field(name='Guide', value='Use `/setup` to explore Tau\'s features and how to use them', inline=False)
        embed.add_field(name='Commands', value='For a full list of command, use `/commands`', inline=False)
        embed.set_image(url='attachment://unknown1.png')

        await interaction.response.send_message(embed=embed, files=files)

    @command(name='setup')
    async def setup(self, interaction: discord.Interaction):
        \'\'\'Display the setup guide\'\'\'
        files = [File(f'assets/dot.png', 'unknown.png'), File(f'assets/bar.png', 'unknown1.png')]

        embed = Embed(color=Color.primary)
        embed.set_author(name='Setup', icon_url='attachment://unknown.png')
        # for name, value in fields:
        #     embed.add_field(name=name, value=value, inline=False)
        embed.set_image(url='attachment://unknown1.png')

        await interaction.response.send_message(embed=embed, files=files)
    '''

    @command(name='tau')
    async def tau(self, interaction: discord.Interaction):
        '''Display info about Tau'''
        embed = (
            Embed(title='Info', color=Color.primary)
            .set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
            .add_field(name='Version', value=self.bot.conf.version)
            .add_field(name='License', value='GPL 3.0')
            .add_field(name='Python', value=platform.python_version())
            .add_field(name='Memory usage', value=f'{self.bot.memory_usage()} MB')
            .add_field(name='discord.py', value=discord.__version__)
            .add_field(name=f'Add {self.bot.conf.name}:', value=f'**[Invite]({self.bot.url})**')
            .set_image(url='attachment://unknown.png')
            .set_footer(text='Online since')
        )
        embed.timestamp = self.bot.boot_time

        await interaction.response.send_message(embed=embed, file=File(f'assets/splash.png', 'unknown.png'))


async def setup(bot: Tau):
    await bot.add_cog(Info(bot))
