from math import isnan
import random

from discord import Embed, File
from discord.ext import commands

import perms
import utils

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(cls=perms.Lock, name='ping', aliases=['p'], usage='ping')
    async def ping(self, ctx):
        '''Pong!
        Display the latency.
        Note that this contains network latency and Discord API latency.\n
        **Example:```yml\n.ping```**
        '''
        ping = await ctx.send('Ping?')
        await ping.edit(content=f'Pong! Latency is **{int((ping.created_at-ctx.message.created_at).total_seconds()*1000)}ms**.')

    @commands.command(cls=perms.Lock, name='coin', aliases=['flip'], usage='coin [quantity=1]')
    @commands.bot_has_permissions(external_emojis=True)
    async def coin(self, ctx, n: int = 1):
        '''Flip a coin.
        Enter a positive integer for *quantity* to flip multiple coins.
        Max is 84.\n
        **Example:```yml\n.coin 3```**
        '''
        if not 0 < n <= 84:
            raise commands.BadArgument
        
        val = random.choices(range(2), k=n)

        embed = Embed(description=f'**You got {["tails", "heads"][val[0]]}!**', color=0xfbb041)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        if n == 1:
            embed.set_thumbnail(url='attachment://unknown.png')
            file = File(f'assets/{val[0]}.png', 'unknown.png')
        else:
            file = None
            coins = ''
            for i, v in enumerate(val):
                coins += utils.emoji[f'coin{v}']
                if (i + 1) % 10 == 0:
                    coins += '\n'

            embed.description = f'**You got:\n\n{coins}**'
            embed.add_field(name='\u200b', value=f'**Heads: {val.count(1)}\nTails: {val.count(0)}**')
        
        await ctx.send(file=file, embed=embed)
    
    @commands.command(cls=perms.Lock, name='dice', aliases=['die', 'roll'], usage='dice [quantity=1] [sides=6]')
    async def dice(self, ctx, n: int = 1, sides: int = 6):
        '''Roll a die.
        Enter a positive integer for *quantity* to roll multiple dice.
        *sides* is a positive integer specifying the amount of sides on each die.\n
        **Example:```yml\n.dice 2\n.roll 3 12```**
        '''
        if n < 1 or sides < 1:
            raise commands.BadArgument

        val = ''
        for i in range(n):
            if i == n - 1:
                val += f'and **{random.randint(1, sides)}**'
                if n == 1:
                    val = val[4:]
                elif n == 2:
                    val = val.replace(',', '')
                break
            val += f'**{random.randint(1, sides)}**, '

        await ctx.send(f'**{ctx.author.display_name}** got {val}!')

def setup(bot):
    bot.add_cog(Fun(bot))