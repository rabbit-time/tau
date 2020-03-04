import asyncio
import os
import platform
import re
import time

import psutil
import discord
from discord import Embed, File
from discord.ext import commands

import config
import perms
from utils import res_member

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(cls=perms.Lock, name='avatar', aliases=['pfp'], usage='avatar [mention]')
    async def avatar(self, ctx):
        '''Retrieve user avatar.
        *mention* can be a mention or a user ID.\n
        **Example:```yml\n.avatar\n.pfp @Tau#4272\n .pfp 608367259123187741```**
        '''
        member = await res_member(ctx)

        embed = Embed(description=f'**[{member.display_name}]({member.avatar_url})**')
        embed.set_image(url=member.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, guild_only=True, name='edit', aliases=['e'], usage='edit <key> <value>')
    async def edit(self, ctx, key=None, *val):
        '''Modify user profile.\n
        **Example:```yml\n.help config```**
        '''
        editable = ['accent', 'bio']
        if not key:
            bio = self.bot.users_[ctx.author.id]['bio']
            keys = ':\n'.join(editable)
            menu = Embed(title=ctx.author.display_name, description='**Please select one of the below to edit.**')
            menu.add_field(name='\u200b', value=f'**{keys}:**')
            menu.add_field(name='\u200b', value=f'{self.bot.users_[ctx.author.id]["accent"]}\n{bio if len(bio) < 64 else bio[:64] + "..."}')
            menu.set_footer(text=f'{self.bot.guilds_[ctx.guild.id]["prefix"]}help edit for more details.')

            return await ctx.send(embed=menu)

        key = key.lower()
        if key == 'accent':
            code = val[0]
            match = re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', code)
            if match:
                await self.bot.users_.update(ctx.author.id, 'accent', code)
            else:
                return await ctx.send('Must be a hex color code.')
        elif key == 'bio':
            await self.bot.users_.update(ctx.author.id, 'bio', ' '.join(val[1:]))
        elif key:
            return await ctx.send(f'`{key}` is not editable.')

        await ctx.send(f'**`{key}`** successfully set to **`{" ".join(val)}`**.')

    @commands.command(cls=perms.Lock, name='help', aliases=['cmd', 'h'], usage='help [command]')
    async def help(self, ctx, cmd=None):
        '''Display the help message.
        When *command* is specified, more help on a command will be displayed.
        *command* can be the name of any command or any alias.\n
        **Example:```yml\n.help\n.h config```**
        '''
        cogs = list(filter(lambda cog: 'On' not in cog[0], self.bot.cogs.items()))
        if not cmd:
            res = ''
            for cog in cogs:
                cmds = cog[1].get_commands()
                cmds.sort(key=lambda cmd: cmd.name)
                cmds = '\n'.join(f'**`{c.usage}`**\n*{c.short_doc if c.short_doc else "None"}*' for c in cmds)
                res += f'**{cog[0]}**\n{cmds}\n\n'

            desc = f'Here\'s a list of commands. For further detail, use **`help [command]`**.\n\n{res}'
            embed = Embed(description=desc)
            embed.set_footer(text='Pro tip! Parameters in angled brackets <> are required while parameters in square brackets [] are optional.', icon_url='attachment://unknown.png')

            await ctx.send(file=File('assets/info.png', 'unknown.png'), embed=embed)
        else:
            for cog in cogs:
                for c in cog[1].get_commands():
                    if cmd == c.name or cmd in c.aliases:
                        cmd = c
                        prefix = self.bot.guilds_[ctx.guild.id]['prefix'] if ctx.guild else self.bot.guilds_.default['prefix']
                        aliases = 'Aliases: ' + ' | '.join(cmd.aliases) if cmd.aliases else ''
                        if aliases:
                            aliases = f'*`{aliases}`*\n'
                        doc = cmd.help.replace(' '*8, '')
                        desc = f'**```asciidoc\n{prefix}{cmd.usage}```{aliases}**\n{doc}'
                        if cmd.guild_only:
                            desc = '*\\*This command may only be used in guilds* ' + desc
                        embed = Embed(description=desc)
                        embed.set_footer(text=f'Perm Level: {cmd.level}')
            
                        return await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, guild_only=True, name='level', aliases=['lvl'], usage='level [mention]')
    async def level(self, ctx):
        '''Retrieve permission level.
        *mention* can be a mention or a user ID.\n
        **Example:```yml\n.level\n.lvl @Tau#4272\n.lvl 608367259123187741```**
        '''
        ctx.author = member = await res_member(ctx)
        lvl = perms.perm(ctx)

        embed = Embed(description=f'**`{lvl}`** *{list(perms.levels.keys())[lvl]}*')
        embed.set_author(name=member.display_name, icon_url=member.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, guild_only=False, name='tau', usage='tau')
    async def tau(self, ctx):
        '''Display app info.
        This is the introduction command.
        **Example:```yml\n.tau```**
        '''
        uptime = time.time() - self.bot.start_time
        
        pid = os.getpid()
        process = psutil.Process(pid)
        mem = process.memory_info()[0] # Mem usage in bytes

        with open('README.md', 'r') as app_info:
            desc = app_info.readlines()
            for line in desc:
                if line.startswith('#'):
                    desc.remove(line)

            desc[1] = f'**```md\n# {desc[1]}```**\n'
            desc = ''.join(desc).replace('+', '•')

        embed = Embed(title='Tau', description=desc)
        embed.add_field(name='Info', value=f'**License:** Apache 2.0\n**Version:** {config.version}\n**Python:** {platform.python_version()}\n**discord.py:** {discord.__version__}\n\n')
        embed.add_field(name='\u200b', value=f'**Uptime:** {uptime//60//60//24:02.0f}:{uptime//60//60%24:02.0f}:{uptime//60%60:02.0f}:{uptime%60:05.2f}\n**Memory Usage:** {round(mem/1000/1000, 2)} MB\n**Code:** {self.bot.code} lines')
        embed.add_field(name='\u200b', value=f'**[Invite]({self.bot.url}) | [Donate](https://www.youtube.com/) | [Server]({config.invite}) | [GitHub](https://www.youtube.com/)**', inline=False)
        embed.set_image(url='attachment://unknown.png')
        embed.set_footer(text=f'Now serving {len(self.bot.users):,} users!')

        await ctx.send(file=File(f'assets/splash.png', 'unknown.png'), embed=embed)

def setup(bot):
    bot.add_cog(Info(bot))