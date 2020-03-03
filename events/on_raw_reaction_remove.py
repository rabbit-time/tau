from discord.ext import commands

import utils

class OnRawReactionRemove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        emojis = tuple(utils.emoji.values())
        emoji = str(payload.emoji)
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if self.bot.rmenus.get((guild.id, payload.message_id)) and not member.bot:
            if emoji in emojis:
                i = tuple(utils.emoji.keys())[emojis.index(emoji)] - 1
                role_ids = self.bot.rmenus[guild.id, payload.message_id]['role_ids'].split()
                role = guild.get_role(int(role_ids[i]))
                
                if role:
                    await member.remove_roles(role)

def setup(bot):
    bot.add_cog(OnRawReactionRemove(bot))