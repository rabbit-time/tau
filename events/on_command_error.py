import sys
import traceback

from discord import Embed
from discord.ext import commands

import ccp
import utils

class OnCommandError(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        error = getattr(error, 'original', error)

        user_error = (commands.MissingRequiredArgument, commands.BadArgument)
        if isinstance(error, user_error):
            desc = (f'It seems like you\'re either missing one or more required arguments, '
                    f'or a bad argument was given.\n\n'
                    f'If you\'re not sure how to use the command, try:'
                    f'**```yml\n{ctx.prefix}help {ctx.command.name}```**\n')
            embed = Embed(description=desc)
            return await ctx.send(f'Hey {ctx.author.mention}!', embed=embed)

        if isinstance(error, utils.RoleNotFound):
            desc = (f'One or more roles needed for this command could not be found. '
                    f'Please ensure that all roles set in the guild\'s config are up-to-date.\n\n'
                    f'Use **`.config`** to edit the guild configuration.')
            embed = Embed(description=desc)
            return await ctx.send(f'Hey {ctx.author.mention}!', embed=embed)

        if isinstance(error, commands.CommandNotFound):
            return ccp.error(f'\u001b[1m{str(ctx.author)}@{str(ctx.guild)}\u001b[0m {ctx.message.content}')

        ccp.error(f'{ctx.command}:')
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

def setup(bot):
    bot.add_cog(OnCommandError(bot))