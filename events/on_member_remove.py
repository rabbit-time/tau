from discord import Embed
from discord.ext import commands

import ccp

class OnMemberRemove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        ccp.event(f'{str(member)} has left {str(member.guild)}', event='MEMBER_REM')

        if member.bot:
            return

        cache = self.bot.guilds_
        guild_id = member.guild.id
        if cache[guild_id]['goodbye_messages'] and (chan := member.guild.get_channel(cache[guild_id]['system_channel'])):
                await chan.send(cache[guild_id]['goodbye_message'].replace('@user', member.display_name).replace('@mention', member.mention).replace('@guild', member.guild.name))

def setup(bot):
    bot.add_cog(OnMemberRemove(bot))