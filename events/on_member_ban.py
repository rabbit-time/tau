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

        cache = self.bot.guilds_
        if cache[guild.id]['ban_messages'] and (chan := guild.get_channel(cache[guild.id]['system_channel'])):
            await chan.send(cache[guild.id]['ban_message'].replace('@user', user.display_name).replace('@mention', user.mention).replace('@guild', guild.name))

def setup(bot):
    bot.add_cog(OnMemberBan(bot))