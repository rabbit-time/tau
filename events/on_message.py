import random

from discord import Embed
from discord.ext import commands

import utils
from utils import level

class OnMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._cd = commands.CooldownMapping.from_cooldown(1, 120.0, commands.BucketType.user)

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot:
            return

        member = msg.author
        uid = member.id
        guild = msg.guild
        if not self.bot.users_.get(uid):
            await self.bot.users_.insert(uid)

        if not guild:
            return

        chan = msg.channel
        cat_name = chan.category.name if chan.category else None
        if not msg.content.startswith(self.bot.guilds_[guild.id]['prefix']) and cat_name != 'appeals' and (member not in self.bot.suppressed.keys() or self.bot.suppressed.get(member) != chan):
            bucket = self._cd.get_bucket(msg)
            limited = bucket.update_rate_limit()
            if not limited:
                # Add xp to user
                xp = self.bot.users_[uid]['xp']
                newxp = xp + random.randint(10, 20)
                await self.bot.users_.update(uid, 'xp', newxp)
                if level(xp) is not level(newxp):
                    # Send level up message if enabled in guild config.
                    if self.bot.guilds_[guild.id]['levelup_messages']:
                        desc = f'**```yml\n↑ {level(newxp)} ↑ {member.display_name} has leveled up!```**'
                        embed = Embed(description=desc, color=utils.Color.green)
                        await chan.send(embed=embed)

def setup(bot):
    bot.add_cog(OnMessage(bot))