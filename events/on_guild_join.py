from discord.ext import commands

import ccp

class OnGuildJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        ccp.event(f'{str(guild)} ({str(guild.owner)})', event='GUILD_ADD')

        await self.bot.guilds_.insert(guild.id)
        if guild.system_channel:
            await self.bot.guilds_.update(guild.id, 'system_channel', guild.system_channel.name)

def setup(bot):
    bot.add_cog(OnGuildJoin(bot))