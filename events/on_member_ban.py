from discord import Embed
from discord.ext import commands

import ccp

class OnMemberBan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        ccp.event(f'{str(user)} was banned from {str(guild)}', event='MEMBER_BAN')

        if user.bot:
            return

        if self.bot.members.get((user.id, guild.id)):
            await self.bot.members.delete((user.id, guild.id))

def setup(bot):
    bot.add_cog(OnMemberBan(bot))