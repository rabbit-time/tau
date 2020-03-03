from discord.ext import commands

import utils

class OnRawReactionAdd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        emojis = tuple(utils.emoji.values())
        emoji = str(payload.emoji)
        member = payload.member
        if self.bot.rmenus.get((member.guild.id, payload.message_id)) and not member.bot:
            if emoji in emojis:
                i = tuple(utils.emoji.keys())[emojis.index(emoji)] - 1
                role_ids = self.bot.rmenus[member.guild.id, payload.message_id]['role_ids'].split()
                role = member.guild.get_role(int(role_ids[i]))

                if role:
                    await member.add_roles(role)

def setup(bot):
    bot.add_cog(OnRawReactionAdd(bot))