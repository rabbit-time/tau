from discord.ext import commands

import ccp

class OnGuildRemove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        ccp.event(f'{str(guild)} ({str(guild.owner)})', event='GUILD_REM')

        await self.bot.guilds_.delete(guild.id)

        cur = await self.bot.con.execute('SELECT guild_id FROM role_menus')
        guild_ids = await cur.fetchall()
        for guild_id in guild_ids:
            guild_id = guild_id[0]
            if guild.id == guild_id:
                await self.bot.con.execute(f'DELETE FROM role_menus WHERE guild_id = {guild.id}')

        await self.bot.con.commit()

def setup(bot):
    bot.add_cog(OnGuildRemove(bot))