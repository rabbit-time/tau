import time
import datetime

from discord import Embed, File
from discord.ext import commands
from discord.utils import escape_markdown

import perms
import utils

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(cls=perms.Lock, name='remind', aliases=[], usage='remind <time> <reminder>')
    async def remind(self, ctx, limit, *, reminder):
        '''Set a reminder.
        Reminders are capped at 6 months to prevent memory leaks.\n
        **Example:```yml\n.remind 2h clean room\n.remind 1h fix bugs```**
        '''
        await ctx.message.delete()

        time_, delay = utils.parse_time(limit)
        now = int(time.time())

        SEMIYEAR = 1555200
        if delay > SEMIYEAR:
            raise commands.BadArgument
        
        await self.bot.reminders.update((ctx.author.id, delay+now), 'channel_id', ctx.channel.id)
        await self.bot.reminders.update((ctx.author.id, delay+now), 'reminder', reminder)
        self.bot.loop.create_task(utils.remind(self.bot, ctx.author, ctx.channel, reminder, delay+now))

        embed = Embed(description=f'Reminder to **{reminder}** has been set for {time_}!')
        embed.set_author(name=escape_markdown(ctx.author.display_name), icon_url=ctx.author.avatar_url)
        embed.set_footer(text=time_, icon_url='attachment://unknown.png')
        embed.timestamp = datetime.datetime.fromtimestamp(delay+now)

        await ctx.send(file=File('assets/clock.png', 'unknown.png'), embed=embed)

def setup(bot):
    bot.add_cog(Utilities(bot))