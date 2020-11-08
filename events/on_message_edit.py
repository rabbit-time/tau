from discord.ext import commands

class OnMessageEdit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, _, msg):
        if msg.author.bot:
            return

        await self.bot.process_commands(msg)

def setup(bot):
    bot.add_cog(OnMessageEdit(bot))