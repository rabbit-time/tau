import datetime
import json
import sys
import traceback

import discord
from discord import Embed, File
from discord.ext import commands

import ccp
import utils

class OnCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, _, msg):
        if msg.author.bot:
            return

        prefix = self.bot.guilds_[msg.guild.id]['prefix'] if msg.guild else self.bot.guilds_.default['prefix']
        if msg.content.startswith(prefix):
            await self.bot.process_commands(msg)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        guild = ctx.guild if ctx.guild else 'dm'
        ccp.event(f'\u001b[1m{ctx.author}@{guild}\u001b[0m {repr(ctx.message.content)[1:-1]}', event='INVOKE')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        error = getattr(error, 'original', error)
        now = datetime.datetime.utcnow()

        # tag checking
        if isinstance(error, commands.CommandNotFound):
            name = ctx.message.content[len(ctx.prefix):]
            if tag := self.bot.tags.get((ctx.guild.id, name)):
                content = tag['content']
                string = tag['embed']
                embed = Embed.from_dict(json.loads(string))
                
                return await ctx.reply(content if content else None, embed=embed, mention_author=False)
            else:
                async with self.bot.pool.acquire() as con:
                    query = f'SELECT * FROM tags WHERE name LIKE \'%{name}%\' ORDER BY name DESC'
                    tags = await con.fetch(query)
                
                if not tags:
                    return

                names = [f'**`{t["name"]}`**' for t in tags]
                embed = Embed(description='\n'.join(names), color=utils.Color.sky)
                embed.set_author(name='Tag not found. Did you mean...', icon_url='attachment://unknown.png')

                return await ctx.reply(embed=embed, file=File('assets/dot.png', 'unknown.png'))

        user_error = commands.MissingRequiredArgument, commands.BadArgument, commands.BadUnionArgument
        if isinstance(error, user_error):
            cmd = ctx.command
            prefix = self.bot.guilds_[ctx.guild.id]['prefix'] if ctx.guild else self.bot.guilds_.default['prefix']
            aliases = '*`Aliases: ' + ' | '.join(cmd.aliases) + '`*\n' if cmd.aliases else ''
            doc = cmd.help.replace(' '*8, '').replace('♤', prefix)

            desc = f'**```asciidoc\n{prefix}{cmd.usage}```{aliases}**\n{doc}'
            if utils.is_guild_only(cmd):
                desc = '*This command may only be used in servers* ' + desc
            elif utils.is_dm_only(cmd):
                desc = '*This command may only be used in DMs* ' + desc

            embed = Embed(description=desc, color=utils.Color.red)
            embed.set_author(name='Invalid command usage', icon_url='attachment://unknown.png')

            return await ctx.reply(file=File('assets/reddot.png', 'unknown.png'), embed=embed)
        
        missing_perms = commands.MissingPermissions, commands.BotMissingPermissions
        if isinstance(error, missing_perms):
            if isinstance(error, commands.MissingPermissions):
                title, noun, verb = 'Missing permissions', 'You', 'use'
            else:
                title, noun, verb = 'Bot missing permissions', 'I', 'perform'

            files = [File('assets/reddot.png', 'unknown.png'), File('assets/redbar.png', 'unknown1.png')]
            perms = ', '.join(sorted(f'**`{perm}`**' for perm in error.missing_perms))
            desc = f'**{noun} lack the following permissions needed to {verb} this command:**\n{perms}'
            embed = Embed(description=desc, color=utils.Color.red)
            embed.set_author(name=title, icon_url='attachment://unknown.png')
            embed.set_image(url='attachment://unknown1.png')
            embed.timestamp = now

            return await ctx.reply(files=files, embed=embed)
        
        # guild only
        if isinstance(error, commands.NoPrivateMessage):
            embed = Embed(color=utils.Color.red)
            embed.set_author(name='This command is only available within servers.', icon_url='attachment://unknown.png')

            return await ctx.reply(file=File('assets/reddot.png', 'unknown.png'), embed=embed)

        # dm only
        if isinstance(error, commands.PrivateMessageOnly):
            embed = Embed(color=utils.Color.red)
            embed.set_author(name='This command is only available within DMs.', icon_url='attachment://unknown.png')

            return await ctx.reply(file=File('assets/reddot.png', 'unknown.png'), embed=embed)

        if isinstance(error, commands.NotOwner):
            files = [File('assets/reddot.png', 'unknown.png'), File('assets/redbar.png', 'unknown1.png')]
            desc = f'**This command may only be used by the bot owner.**'
            embed = Embed(description=desc, color=utils.Color.red)
            embed.set_author(name='Missing permissions', icon_url='attachment://unknown.png')
            embed.set_image(url='attachment://unknown1.png')
            embed.timestamp = now

            return await ctx.reply(files=files, embed=embed)

        if isinstance(error, commands.CommandOnCooldown):
            files = [File('assets/reddot.png', 'unknown.png'), File('assets/redbar.png', 'unknown1.png')]
            embed = Embed(description='**This command is currently on a cooldown.**', color=utils.Color.red)
            embed.set_author(name='Too hot!', icon_url='attachment://unknown.png')
            embed.set_image(url='attachment://unknown1.png')
            embed.set_footer(text='Try again at')
            embed.timestamp = now + datetime.timedelta(seconds=error.retry_after)

            return await ctx.reply(files=files, embed=embed)

        if isinstance(error, discord.HTTPException):
            return ccp.error(f'\u001b[31;1m{error.status} {error.response.reason} (error code {error.code}) {error.text}\u001b[0m')

        if isinstance(error, discord.NotFound):
            embed = Embed(description='Sorry, a message with that ID could not be fetched in this channel.')
            return await ctx.reply(embed=embed)

        if isinstance(error, utils.RoleNotFound):
            desc = (f'One or more roles needed for this command could not be found. '
                    f'Please ensure that all roles set in the guild\'s config are up-to-date.\n\n'
                    f'Use **`.config`** to edit the guild configuration.')
            embed = Embed(description=desc, color=utils.Color.red)
            embed.set_author(name='Role not found', icon_url='attachment://unknown.png')

            return await ctx.reply(file=File('assets/reddot.png', 'unknown.png'), embed=embed)

        if isinstance(error, commands.CheckFailure):
            return

        ccp.error(f'{ctx.command}:')
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

def setup(bot):
    bot.add_cog(OnCommand(bot))