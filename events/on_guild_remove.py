from discord.ext import commands

import ccp

class OnGuildRemove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        ccp.event(f'{str(guild)} ({str(guild.owner)})', event='GUILD_REM')

        async with self.bot.pool.acquire() as con:
            await self.bot.guilds_.delete(guild.id)
            await con.execute('DELETE FROM members WHERE guild_id = $1', guild.id)
            await con.execute('DELETE FROM role_menus WHERE guild_id = $1', guild.id)
            await con.execute('DELETE FROM ranks WHERE guild_id = $1', guild.id)

def setup(bot):
    bot.add_cog(OnGuildRemove(bot))