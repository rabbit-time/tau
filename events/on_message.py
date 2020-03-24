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

        member = msg.author
        uid = member.id
        guild = msg.guild
        if not self.bot.users_.get(uid):
            await self.bot.users_.insert(uid)

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
                        embed = Embed(description=desc, color=0x2aa198)
                        await chan.send(embed=embed)
                
            # Rank roles
            if not self.bot.members.get((uid, guild.id)):
                await self.bot.members.insert((uid, guild.id))

            if self.bot.ranks.get(guild.id) and (role_ids := self.bot.ranks[guild.id]['role_ids']):
                xp = self.bot.members[uid, msg.guild.id]['xp'] + 1
                await self.bot.members.update((uid, guild.id), 'xp', xp)

                req = [0, 250, 1000, 2500, 5000, 10000]
                role_ids = role_ids.split()
                roles = [guild.get_role(int(id)) for id in role_ids]
                if None in roles:
                    return await self.bot.ranks.update(guild.id, 'role_ids', '')
                
                for i in range(len(roles)-1, -1, -1):
                    if xp < req[i]:
                        continue
                    
                    rank = roles.pop(i)
                    for role in roles:
                        if role in member.roles:
                            await member.remove_roles(role)
                    
                    if xp == req[i]:
                        desc = f'**```yml\n{member.display_name} has ranked up to {str(roles[i])}!```**'
                        embed = Embed(description=desc, color=0x2aa198)
                        await chan.send(embed=embed)

                    if rank not in member.roles:        
                        await member.add_roles(rank)
                        
                    break

def setup(bot):
    bot.add_cog(OnMessage(bot))