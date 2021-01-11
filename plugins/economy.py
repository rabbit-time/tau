import datetime
import random

import discord
from discord import Embed, File
from discord.ext import commands
from discord.ext.commands import command, guild_only

import utils

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(name='balance', aliases=['acc', 'bal'], usage='balance [member]')
    async def balance(self, ctx, *, member: discord.Member = None):
        '''Display user account balance.
        This only works with members within the guild.\n
        **Example:```yml\n♤balance\n♤bal @Tau#4272\n♤acc 608367259123187741```**
        '''
        member = member if member else ctx.author
        if member.bot:
            return

        bal = self.bot.users_[member.id]['tickets']
        embed = Embed(color=utils.Color.sky)
        embed.set_author(name=bal, icon_url='attachment://unknown.png')

        await ctx.reply(file=File('assets/credits.png', 'unknown.png'), embed=embed, mention_author=False)

    @command(name='give', usage='give <member> <quantity>')
    @guild_only()
    async def give(self, ctx, member: discord.Member, qty):
        '''Give credits to another user.
        `quantity` can also be '\\*' or 'all'\n
        **Example:```yml\n♤give @Tau#4272 420 \n♤give 608367259123187741 69```**
        '''
        if member.bot:
            return

        bal = self.bot.users_[ctx.author.id]['tickets']
        qty = bal if qty == '*' or qty == 'all' else int(qty) if qty.isdigit() and 0 < int(qty) <= bal else None
        if not qty:
            return await ctx.send('Invalid *qty*.')

        await self.bot.users_.update(ctx.author.id, 'tickets', bal-qty)

        bal = self.bot.users_[member.id]['tickets']
        await self.bot.users_.update(member.id, 'tickets', bal+qty)

        embed = Embed(color=utils.Color.sky)
        embed.set_author(name=f'Gave {qty} credits to {member.display_name}!', icon_url='attachment://unknown.png')

        await ctx.reply(file=File('assets/credits.png', 'unknown.png'), embed=embed, mention_author=False)

    @commands.cooldown(1, 86400.0, type=commands.BucketType.user)
    @command(name='credits', aliases=['daily'], usage='tickets')
    async def credits(self, ctx):
        '''Collect your daily credits.
        Has a cooldown of 24 hours.\n
        **Example:```yml\n♤credits```**
        '''
        bal = self.bot.users_[ctx.author.id]['tickets']
        amt = 20
        if datetime.datetime.today().weekday() == 6:
            amt *= 2

        await self.bot.users_.update(ctx.author.id, 'tickets', bal+amt)

        embed = Embed(color=utils.Color.sky)
        embed.set_author(name=f'Collected {amt} credits for a new balance of {bal+amt}!', icon_url='attachment://unknown.png')
        
        await ctx.reply(file=File('assets/credits.png', 'unknown.png'), embed=embed, mention_author=False)

def setup(bot):
    bot.add_cog(Economy(bot))