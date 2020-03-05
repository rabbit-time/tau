from discord import Embed
from discord.ext import commands

import ccp

class OnMemberJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        ccp.event(f'{str(member)} has joined {str(member.guild)}', event='MEMBER_ADD')

        if member.bot:
            return

        cache = self.bot.guilds_
        guild_id = member.guild.id
        if cache[guild_id]['welcome_messages'] and (chan := member.guild.get_channel(cache[guild_id]['system_channel'])):
            await chan.send(cache[guild_id]['welcome_message'].replace('@user', member.display_name).replace('@mention', member.mention).replace('@guild', member.guild.name))

        if self.bot.mute_tasks.get((member.id, guild_id)):
            role = member.guild.get_role(self.bot.guilds_[guild_id]['bind_role'])
            await member.add_roles(role)

        autorole = self.bot.guilds_[member.guild.id]['autorole']
        if role := member.guild.get_role(autorole):
            await member.add_roles(role)

def setup(bot):
    bot.add_cog(OnMemberJoin(bot))