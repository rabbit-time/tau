from discord.ext import commands

import ccp

class OnCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command(self, ctx):
        hostname = ctx.guild.name if ctx.guild else 'dm'
        ccp.event(f'\u001b[1m{str(ctx.author)}@{hostname}\u001b[0m {repr(ctx.message.content)[1:-1]}', event='INVOKE')

def setup(bot):
    bot.add_cog(OnCommand(bot))