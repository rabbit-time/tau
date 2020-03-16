import random

from discord import Embed
from discord.ext import commands

from utils import level, levelxp

class OnMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._cd = commands.CooldownMapping.from_cooldown(1, 120.0, commands.BucketType.user)

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot:
            return

        uid = msg.author.id
        if not self.bot.users_.get(uid):
            await self.bot.users_.insert(uid)

        cat_name = msg.channel.category.name if msg.channel.category else None
        if not msg.content.startswith(self.bot.guilds_[msg.guild.id]['prefix']) and cat_name != 'appeals' and (msg.author not in self.bot.suppressed.keys() or self.bot.suppressed.get(msg.author) != msg.channel):
            bucket = self._cd.get_bucket(msg)
            limited = bucket.update_rate_limit()
            if not limited:
                # Add xp to user
                xp = self.bot.users_[uid]['xp']
                newxp = xp + random.randint(10, 20)
                await self.bot.users_.update(uid, 'xp', newxp)
                if level(xp) is not level(newxp):
                    # Send level up message if enabled in guild config.
                    if self.bot.guilds_[msg.guild.id]['levelup_messages']:
                        embed = Embed(description=f'**```yml\n↑ {level(newxp)} ↑ {msg.author.display_name} has leveled up!```**', color=0x2aa198)
                        await msg.channel.send(embed=embed)

def setup(bot):
    bot.add_cog(OnMessage(bot))