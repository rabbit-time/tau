from math import isnan
from random import randint, choice

from discord.ext import commands

import perms

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

    @commands.command(cls=perms.Lock, name='coin', aliases=['flip'], usage='coin [quantity]')
    async def coin(self, ctx, n: int = 1):
        '''Flip a coin.
        Enter a positive integer for *quantity* to flip multiple coins.\n
        **Example:```yml\n.coin 3```**
        '''
        if n < 1:
            raise commands.BadArgument
        
        coin = ['**heads**', '**tails**']
        res = [choice(coin) for i in range(n)]
        res = ', '.join(res[:-1]) + f' and **{choice(coin)}**' if n > 1 else ', '.join(res)
        if n == 2:
            res = res.replace(',', '')

        await ctx.send(f'**{ctx.author.display_name}** got {res}!')
    
    @commands.command(cls=perms.Lock, name='dice', aliases=['die', 'roll'], usage='dice [quantity] [sides]')
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
                val += f'and **{randint(1, sides)}**'
                if n == 1:
                    val = val[4:]
                elif n == 2:
                    val = val.replace(',', '')
                break
            val += f'**{randint(1, sides)}**, '

        await ctx.send(f'**{ctx.author.display_name}** got {val}!')

def setup(bot):
    bot.add_cog(Fun(bot))