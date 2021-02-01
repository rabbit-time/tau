import asyncio
import os
import platform
import time

import psutil
import discord
from discord import Embed, File
from discord.ext import commands
from discord.ext.commands import command, guild_only, dm_only
from discord.utils import find

import config
import utils

class Command(commands.Converter):
    async def convert(self, ctx, arg):
        return find(lambda cmd: cmd.name == arg or arg in cmd.aliases, ctx.bot.commands)

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(name='avatar', aliases=['pfp'], usage='avatar [member]')
    async def avatar(self, ctx, *, member: discord.Member = None):
        '''Retrieve user avatar.\n
        **Example:```yml\n♤avatar\n♤pfp @Tau#4272\n♤pfp 608367259123187741```**
        '''
        if not member:
            member = ctx.author

        png = member.avatar_url_as(format='png')
        jpg = member.avatar_url_as(format='jpg')
        webp = member.avatar_url_as(format='webp')
        formats = [f'[`.png`]({png})', f'[`.jpg`]({jpg})', f'[`.webp`]({webp})']
        if member.is_avatar_animated():
            gif = member.avatar_url_as(format='gif')
            formats.append(f'[`.gif`]({gif})')

        delim = '\u2002|\u2002'
        embed = Embed(description=f':link: **{delim.join(formats)}**', color=utils.Color.cyan)
        embed.set_author(name=member.display_name, icon_url=member.avatar_url)
        embed.set_image(url=member.avatar_url)

        await ctx.send(embed=embed)

    @command(name='accent', usage='accent [color]')
    @guild_only()
    async def accent(self, ctx, *, color: discord.Color = discord.Color.from_rgb(136, 179, 248)):
        '''Modify accent in user profile.
        Leave `color` blank to reset to default\n
        **Example:```yml\n♤accent #88b3f8```**
        '''
        await self.bot.users_.update(ctx.author.id, 'accent', str(color))

        desc = f'**```yml\n+ Accent has been set to {hex(color.value) if color.value != utils.Color.sky else "default"}```**'
        embed = Embed(description=desc, color=color)

        await ctx.send(embed=embed)

    @command(name='bio', usage='bio [bio]')
    @guild_only()
    async def bio(self, ctx, *, bio=''):
        '''Modify bio in user profile.
        Leave `bio` blank to remove bio\n
        **Example:```yml\n♤bio Hello!```**
        '''
        await self.bot.users_.update(ctx.author.id, 'bio', bio)

        res = f'set to: {bio}' if bio else f'removed'
        desc = f'**```yml\n+ Bio has been {res}```**'
        embed = Embed(description=desc, color=utils.Color.green)

        await ctx.send(embed=embed)

    @command(name='commands', aliases=['cmd', 'cmds'], usage='commands [command]')
    async def commands_(self, ctx, cmd: Command = None):
        '''Display the full list of commands.
        When `command` is specified, details on that command will be displayed.
        `command` can be the name of any command or any alias.\n
        **Flags:**
        **`--no-dm` |** forces the response into the current channel.\n
        **Example:```yml\n♤commands\n♤cmd config```**
        '''
        if not cmd:
            cogs = list(filter(lambda cog: cog[1].get_commands(), self.bot.cogs.items()))
            cogs.sort(key=lambda cog: cog[0])

            desc = f'Here\'s a list of available commands. For further detail on a command, use **`{ctx.prefix}cmd [command]`**.'
            embed = Embed(description=desc, color=utils.Color.sky)
            embed.set_author(name='Commands', icon_url='attachment://unknown.png')
            for cog in cogs:
                cmds = cog[1].get_commands()
                cmds.sort(key=lambda cmd: cmd.name)
                cmds = ' '.join(f'`{c.name}`' for c in cmds)
                embed.add_field(name=cog[0], value=f'**{cmds}**', inline=False)
            embed.set_image(url='attachment://unknown1.png')
            embed.set_footer(text='Pro tip! Parameters in angled brackets <> are required while parameters in square brackets [] are optional.', icon_url='attachment://unknown2.png')

            files = [File('assets/dot.png', 'unknown.png'), File(f'assets/bar.png', 'unknown1.png'), File('assets/info.png', 'unknown2.png')]
            if '--no-dm' in ctx.message.content or not ctx.guild:
                await ctx.reply(files=files, embed=embed, mention_author=False)
            else:
                try:
                    await ctx.author.send(files=files, embed=embed)

                    em = Embed(color=utils.Color.green)
                    em.set_author(name='Sent to your DMs', icon_url='attachment://unknown.png')

                    await ctx.reply(file=File('assets/greendot.png', 'unknown.png'), embed=em, mention_author=False)
                except discord.Forbidden:
                    await ctx.reply(files=files, embed=embed, mention_author=False)
        else:
            prefix = self.bot.guilds_[ctx.guild.id]['prefix'] if ctx.guild else self.bot.guilds_.default['prefix']
            aliases = '*`Aliases: ' + ' | '.join(cmd.aliases) + '`*\n' if cmd.aliases else ''
            doc = cmd.help.replace(' '*8, '').replace('♤', prefix)

            desc = f'**```asciidoc\n{prefix}{cmd.usage}```{aliases}**\n{doc}'
            if utils.is_guild_only(cmd):
                desc = '*This command may only be used in servers* ' + desc
            elif utils.is_dm_only(cmd):
                desc = '*This command may only be used in DMs* ' + desc
            embed = Embed(description=desc, color=utils.Color.sky)

            await ctx.reply(embed=embed, mention_author=False)

    @command(name='help', aliases=['h'], usage='help')
    async def help(self, ctx):
        '''Display the help message.\n
        **Example:```yml\n♤help```**
        '''
        p = ctx.prefix
        links = f'**[Invite]({self.bot.url})', f'[Server]({config.invite})', f'[GitHub]({config.repo})**'
        files = [File(f'assets/dot.png', 'unknown.png'), File(f'assets/bar.png', 'unknown1.png')]
        desc = (f'The current prefix is set to: **`{p}`**\n\nIf you\'re just getting started, it is recommended '
                f'that you go through the **`{p}setup`** process before anything else! (admin-only)\n\n'
                f'**Looking for the full list of commands?**\nTry typing **`{p}commands`** or **`{p}cmd`** for short.\n\n'
                f'**Voice your opinion!**\nUse the **`{p}feedback`** command for suggestions and bug reports.\n\n'
                f'**Learn more:**\nFor more information about the bot, use the **`{p}tau`** command.')
        embed = Embed(description=desc, color=utils.Color.sky)
        embed.set_author(name='Help', icon_url='attachment://unknown.png')
        embed.add_field(name='\u200b', value='\u3000\u3000|\u3000\u3000'.join(links))
        embed.set_image(url='attachment://unknown1.png')

        await ctx.reply(files=files, embed=embed, mention_author=False)

    @command(name='setup', usage='setup')
    @guild_only()
    async def setup(self, ctx):
        '''Display the setup guide.\n
        **Example:```yml\n♤setup```**
        '''
        p = ctx.prefix
        files = [File(f'assets/dot.png', 'unknown.png'), File(f'assets/bar.png', 'unknown1.png')]
        fields = [
            ('Welcome to the setup process!', 'This is a non-comprehensive guide to getting started with Tau.'),
            ('Config', f'First things first, use the **`{p}config`** command and edit it as you see fit. Some features require this such as the **`{p}mute`** command, which needs a mute role assigned to it first.'),
            ('Permissions', f'In order for Tau to work properly, you need to give me permissions. The only sure-fire way to prevent permission errors in the future is to move my role to the top of the role hierarchy and enable administrator permissions.'),
            ('Feedback', f'Be sure to leave some **`{p}feedback`**! Your input would be greatly appreciated! :)')
        ]

        embed = Embed(color=utils.Color.sky)
        embed.set_author(name='Setup', icon_url='attachment://unknown.png')
        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)
        embed.set_image(url='attachment://unknown1.png')

        await ctx.reply(files=files, embed=embed, mention_author=False)

    @command(name='tau', usage='tau')
    async def tau(self, ctx):
        '''Display app info.\n
        **Example:```yml\n♤tau```**
        '''
        pid = os.getpid()
        process = psutil.Process(pid)
        mem = process.memory_info()[0] # Mem usage in bytes

        links = f'**[Invite]({self.bot.url})', f'[Server]({config.invite})', f'[GitHub]({config.repo})**'
        info = [
            ('Version', config.version), ('License', 'Apache 2.0'), ('Python', platform.python_version()),
            ('Memory usage', f'{round(mem/1000/1000, 2)} MB'), ('discord.py', discord.__version__),
            ('Code', f'{self.bot.code} lines')
        ]

        embed = Embed(title='Info', color=utils.Color.sky)
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        for name, value in info:
            embed.add_field(name=name, value=value)
        embed.add_field(name='\u200b', value='\u3000\u3000|\u3000\u3000'.join(links))
        embed.set_image(url='attachment://unknown.png')
        embed.set_footer(text='Online since')
        embed.timestamp = self.bot.start_time

        await ctx.send(file=File(f'assets/splash.png', 'unknown.png'), embed=embed)

def setup(bot):
    bot.add_cog(Info(bot))
