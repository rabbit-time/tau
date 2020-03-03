from discord.ext import commands

class OnRawMessageDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        if self.bot.rmenus.get((payload.guild_id, payload.message_id)):
            await self.bot.rmenus.delete((payload.guild_id, payload.message_id))

def setup(bot):
    bot.add_cog(OnRawMessageDelete(bot))