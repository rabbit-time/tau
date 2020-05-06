import asyncio
import random

from discord import Embed, File
from discord.ext import commands
import requests

import perms
import utils

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def _img(self, ctx, path: str, name: str = None) -> Embed:
        name = name if name else path.title()
        res = requests.get(f'https://some-random-api.ml/img/{path}')
        url = res.json()['link']
        
        embed = Embed(description=f':link: **[{name}]({url})**', color=random.choice(utils.Color.rainbow))
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_image(url=url)

        return embed

    @commands.command(cls=perms.Lock, name='bird', aliases=[], usage='bird')
    async def bird(self, ctx):
        '''Get a random bird.\n
        **Example:```yml\n.bird```**
        '''
        await ctx.send(embed=self._img(ctx, 'birb', 'Bird'))

    @commands.command(cls=perms.Lock, name='cat', aliases=[], usage='cat')
    async def cat(self, ctx):
        '''Get a random cat.\n
        **Example:```yml\n.cat```**
        '''
        await ctx.send(embed=self._img(ctx, 'cat'))

    @commands.command(cls=perms.Lock, name='dog', aliases=[], usage='dog')
    async def dog(self, ctx):
        '''Get a random dog.\n
        **Example:```yml\n.dog```**
        '''
        await ctx.send(embed=self._img(ctx, 'dog'))
    
    @commands.command(cls=perms.Lock, name='fox', aliases=[], usage='fox')
    async def fox(self, ctx):
        '''Get a random fox.\n
        **Example:```yml\n.fox```**
        '''
        await ctx.send(embed=self._img(ctx, 'fox'))
    
    @commands.command(cls=perms.Lock, name='koala', aliases=[], usage='koala')
    async def koala(self, ctx):
        '''Get a random koala.\n
        **Example:```yml\n.koala```**
        '''
        await ctx.send(embed=self._img(ctx, 'koala'))
    
    @commands.command(cls=perms.Lock, name='panda', aliases=[], usage='panda')
    async def panda(self, ctx):
        '''Get a random panda.\n
        **Example:```yml\n.panda```**
        '''
        await ctx.send(embed=self._img(ctx, 'panda'))
    
    @commands.command(cls=perms.Lock, name='redpanda', aliases=[], usage='redpanda')
    async def red_panda(self, ctx):
        '''Get a random red panda.\n
        **Example:```yml\n.redpanda```**
        '''
        await ctx.send(embed=self._img(ctx, 'red_panda', 'Red panda'))

    @commands.command(cls=perms.Lock, name='ping', aliases=['p'], usage='ping')
    async def ping(self, ctx):
        '''Pong!
        Display the latency.
        Note that this contains network latency and Discord API latency.\n
        **Example:```yml\n.ping```**
        '''
        embed = Embed(description='**Ping?**', color=utils.Color.gold)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        ping = await ctx.send(embed=embed)

        await asyncio.sleep(0.2)

        embed.colour = utils.Color.green
        embed.description = '**Pong!**'
        embed.add_field(name='Latency', value=f'**{self.bot.latency*1000:.2f}**ms')

        await ping.edit(embed=embed)

    @commands.command(cls=perms.Lock, name='coin', aliases=['flip'], usage='coin [quantity=1]')
    @commands.bot_has_permissions(external_emojis=True)
    async def coin(self, ctx, n: int = 1):
        '''Flip a coin.
        Enter a positive integer for `quantity` to flip multiple coins.
        Max is 84.\n
        **Example:```yml\n.coin\n.flip 3```**
        '''
        if not 0 < n <= 84:
            raise commands.BadArgument
        
        val = random.choices(range(2), k=n)

        embed = Embed(description=f'**You got {["tails", "heads"][val[0]]}!**', color=utils.Color.gold)
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
    
    @commands.command(cls=perms.Lock, name='dice', aliases=['die', 'roll'], usage='dice [quantity=1]')
    async def dice(self, ctx, n: int = 1):
        '''Roll a die.
        Enter a positive integer for `quantity` to roll multiple dice.
        Max is 84.\n
        **Example:```yml\n.dice\n.roll 3```**
        '''
        if not 0 < n <= 84:
            raise commands.BadArgument
        
        val = random.choices(range(6), k=n)

        embed = Embed(description=f'**You got {val[0]+1}!**', color=utils.Color.red)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        if n == 1:
            embed.set_thumbnail(url='attachment://unknown.png')
            file = File(f'assets/d{val[0]+1}.png', 'unknown.png')
        else:
            file = None
            dice = ''
            for i, v in enumerate(val):
                dice += utils.emoji[f'die{v+1}']
                if (i + 1) % 10 == 0:
                    dice += '\n'

            embed.description = f'**You got:\n\n{dice}**'
            for i in range(6):
                embed.add_field(name=utils.emoji[f'die{i+1}']+'\u200b', value=f'**{val.count(i)}**')
        
        await ctx.send(file=file, embed=embed)

def setup(bot):
    bot.add_cog(Fun(bot))