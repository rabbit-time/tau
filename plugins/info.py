import asyncio
import os
import platform
import time

import psutil
import discord
from discord import Embed, File
from discord.ext import commands
from discord.utils import find

import config
import perms
import utils

class Command(commands.Converter):
    async def convert(self, ctx, arg):
        return find(lambda cmd: cmd.name == arg or arg in cmd.aliases, ctx.bot.commands)

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(cls=perms.Lock, name='avatar', aliases=['pfp'], usage='avatar [member]')
    async def avatar(self, ctx, *, member: discord.Member = None):
        '''Retrieve user avatar.\n
        **Example:```yml\n.avatar\n.pfp @Tau#4272\n.pfp 608367259123187741```**
        '''
        if not member:
            member = ctx.author

        embed = Embed(description=f':link: **[Avatar]({member.avatar_url})**')
        embed.set_author(name=member, icon_url=member.avatar_url)
        embed.set_image(url=member.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, guild_only=True, name='accent', aliases=[], usage='accent [color]')
    async def accent(self, ctx, *, color: discord.Color = discord.Color.from_rgb(136, 179, 248)):
        '''Modify accent in user profile.
        Leave `color` blank to reset to default\n
        **Example:```yml\n.accent #88b3f8```**
        '''
        await self.bot.users_.update(ctx.author.id, 'accent', str(color))

        desc = f'**```yml\n+ Accent has been set to {hex(color.value) if color.value != utils.Color.sky else "default"}```**'
        embed = Embed(description=desc, color=color)

        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, guild_only=True, name='bio', aliases=[], usage='bio [bio]')
    async def bio(self, ctx, *, bio=''):
        '''Modify bio in user profile.
        Leave `bio` blank to remove bio\n
        **Example:```yml\n.bio Hello!```**
        '''
        await self.bot.users_.update(ctx.author.id, 'bio', bio)

        res = f'set to: {bio}' if bio else f'removed'
        desc = f'**```yml\n+ Bio has been {res}```**'
        embed = Embed(description=desc, color=utils.Color.green)

        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, name='help', aliases=['cmd', 'h'], usage='help [command]')
    async def help(self, ctx, cmd: Command = None):
        '''Display the help message.
        When `command` is specified, more help on a command will be displayed.
        `command` can be the name of any command or any alias.\n
        **Example:```yml\n.help\n.h config```**
        '''
        if not cmd:
            cogs = list(filter(lambda cog: cog[1].get_commands(), self.bot.cogs.items()))
            cogs.sort(key=lambda cog: cog[0])
            
            res = ''
            for cog in cogs:
                cmds = cog[1].get_commands()
                cmds.sort(key=lambda cmd: cmd.name)
                cmds = ' '.join(f'`{c.name}`' for c in cmds)
                res += f'{cog[0]}\n{cmds}\n\n'

            desc = f'Here\'s a list of commands. For further detail, use **`help [command]`**.\n\n**{res}**'
            embed = Embed(description=desc)
            embed.set_footer(text='Pro tip! Parameters in angled brackets <> are required while parameters in square brackets [] are optional.', icon_url='attachment://unknown.png')

            await ctx.send(file=File('assets/info.png', 'unknown.png'), embed=embed)
        else:
            prefix = self.bot.guilds_[ctx.guild.id]['prefix'] if ctx.guild else self.bot.guilds_.default['prefix']
            aliases = '*`Aliases: ' + ' | '.join(cmd.aliases) + '`*\n' if cmd.aliases else ''
            doc = cmd.help.replace(' '*8, '')

            desc = f'**```asciidoc\n{prefix}{cmd.usage}```{aliases}**\n{doc}'
            if cmd.guild_only:
                desc = '*This command may only be used in servers* ' + desc
            embed = Embed(description=desc)
            embed.set_footer(text=f'Perm level: {cmd.level}')

            return await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, guild_only=True, name='level', aliases=['lvl'], usage='level [member]')
    async def level(self, ctx, *, member: discord.Member = None):
        '''Retrieve permission level.\n
        **Example:```yml\n.level\n.lvl @Tau#4272\n.lvl 608367259123187741```**
        '''
        if member:
            ctx.author = member
        lvl = perms.perm(ctx)

        embed = Embed(description=f'**`{lvl}`** *{list(perms.levels.keys())[lvl]}*')
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, name='tau', usage='tau')
    async def tau(self, ctx):
        '''Display app info.
        This is the introduction command.\n
        **Example:```yml\n.tau```**
        '''
        uptime = time.time() - self.bot.start_time
        
        pid = os.getpid()
        process = psutil.Process(pid)
        mem = process.memory_info()[0] # Mem usage in bytes

        with open('README.md', 'r') as readme:
            desc = [line for line in readme.readlines()[:15] if '#' not in line and line != '\n']
            desc[0] = f'**```md\n# {desc[0]}```**\n'
            desc = ''.join(desc).replace('+', '•')
        
        # \u3000 is an ideographic space. Learn more: https://en.wikipedia.org/wiki/Whitespace_character
        # f'[Donate](https://www.youtube.com/)' add donations later on next to Invite
        divider = '\u3000|\u3000'
        links = [f'**[Invite]({self.bot.url})', f'[Server]({config.invite})', f'[GitHub]({config.repo})**']
        embed = Embed(title='Tau', description=desc)
        embed.add_field(name='Info', value=f'**License:** Apache 2.0\n**Version:** {config.version}\n**Python:** {platform.python_version()}\n**discord.py:** {discord.__version__}\n\n')
        embed.add_field(name='\u200b', value=f'**Uptime:** {uptime//60//60//24:02.0f}:{uptime//60//60%24:02.0f}:{uptime//60%60:02.0f}:{uptime%60:05.2f}\n**Memory Usage:** {round(mem/1000/1000, 2)} MB\n**Code:** {self.bot.code} lines')
        embed.add_field(name='\u200b', value=f'To get started, try **`{self.bot.guilds_[ctx.guild.id]["prefix"]}help`** for a list of commands!', inline=False)
        embed.add_field(name='\u200b', value=divider.join(links), inline=False)
        embed.set_image(url='attachment://unknown.png')
        embed.set_footer(text=f'Now serving {len(self.bot.users):,} users!')

        await ctx.send(file=File(f'assets/splash.png', 'unknown.png'), embed=embed)

def setup(bot):
    bot.add_cog(Info(bot))