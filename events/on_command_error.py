import sys
import traceback

import discord
from discord import Embed, File
from discord.ext import commands

import ccp
import utils

class OnCommandError(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        error = getattr(error, 'original', error)

        user_error = (commands.MissingRequiredArgument, commands.BadArgument, commands.BadUnionArgument)
        if isinstance(error, user_error):
            cmd = ctx.command
            prefix = self.bot.guilds_[ctx.guild.id]['prefix'] if ctx.guild else self.bot.guilds_.default['prefix']
            aliases = '*`Aliases: ' + ' | '.join(cmd.aliases) + '`*\n' if cmd.aliases else ''
            doc = cmd.help.replace(' '*8, '')

            desc = f'**```asciidoc\n{prefix}{cmd.usage}```{aliases}**\n{doc}'
            if cmd.guild_only:
                desc = '*This command may only be used in guilds* ' + desc

            desc = f'**```diff\n- Invalid command usage```**\n' + desc
            embed = Embed(description=desc)
            embed.set_footer(text=f'Perm level: {cmd.level}')

            return await ctx.send(f'Hey {ctx.author.mention}!', embed=embed)

        if isinstance(error, discord.NotFound):
            embed = Embed(description='Sorry, a message with that ID could not be fetched in this channel.')
            return await ctx.send(f'Hey {ctx.author.mention}!', embed=embed)

        if isinstance(error, utils.RoleNotFound):
            desc = (f'One or more roles needed for this command could not be found. '
                    f'Please ensure that all roles set in the guild\'s config are up-to-date.\n\n'
                    f'Use **`.config`** to edit the guild configuration.')
            embed = Embed(description=desc)
            return await ctx.send(f'Hey {ctx.author.mention}!', embed=embed)

        if isinstance(error, commands.BotMissingPermissions):
            perms = ''
            for perm in error.missing_perms:
                perms += f'\n`{perm}`'

            desc = (f'The following required permissions for this command are missing:**{perms}**\n\n'
                    f'To avoid these messages in the future, please put the Tau role as the highest role '
                    f'and enable admin permissions, as such:')
            embed = Embed(description=desc)
            embed.set_image(url='attachment://unknown.png')
            return await ctx.send(f'Hey {ctx.author.mention}!', file=File('assets/perms.png', 'unknown.png'), embed=embed)

        if isinstance(error, commands.MissingPermissions):
            perms = ''
            for perm in error.missing_perms:
                perms += f'\n`{perm}`'

            embed = Embed(description=f'You lack the following permissions needed to use this command:\n**{perms}**')
            return await ctx.send(f'Hey {ctx.author.mention}!', embed=embed)

        if isinstance(error, commands.CommandNotFound):
            return ccp.error(f'\u001b[1m{ctx.author}@{ctx.guild}\u001b[0m {ctx.message.content}')

        ccp.error(f'{ctx.command}:')
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

def setup(bot):
    bot.add_cog(OnCommandError(bot))