import asyncio
import io

import discord
from discord import Embed, File
from discord.ext import commands
from discord.utils import find

import perms
import utils

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(cls=perms.Lock, level=2, guild_only=True, name='rolemenu', aliases=['rmenu'], usage='rolemenu <title> | <color> | <*roles>')
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.bot_has_permissions(add_reactions=True, manage_messages=True)
    async def rolemenu(self, ctx, *data):
        '''Create a role menu.
        Role menus are powered by message reactions and can hold up to 15 roles. 
        Arguments must be separated by pipes: `|`
        `title` must be no more than 256 characters long.
        `color` must be a color represented in hexadecimal format.
        `roles` must be a list of role IDs delimited by spaces.\n
        **Example:```yml\n .rolemenu Color Roles | #8bb3f8 | 546836599141302272```**
        '''
        await ctx.message.delete()

        title, color, role_ids = ' '.join(data).split('|')
        title = title.strip()
        color = color.strip('# ')
        role_ids = role_ids.strip()

        try:
            color = int(color, 16)
        except ValueError:
            return await ctx.send(f'{ctx.author.mention} `color` must be a valid hex code.', delete_after=5)

        if len(role_ids.split(' ')) > 15:
            return await ctx.send(f'{ctx.author.mention} Maximum of 15 roles cannot be exceeded.', delete_after=5)
        elif len(title) > 256:
            return await ctx.send(f'{ctx.author.mention} `title` must be no longer than 256 characters.', delete_after=5)

        roles = []
        for role_id in role_ids.split(' '):
            role = ctx.guild.get_role(int(role_id))
            if not role:
                return await ctx.send(f'{ctx.author.mention} One or more roles could not be resolved: `{role_id}` is invalid.', delete_after=5)

            roles.append(role)

        desc = ''
        for i, role in enumerate(roles):
            desc += f'**{i+1}.** {str(role)}\n'
        embed = Embed(title=title, description=desc.strip('\n'), color=color)
        menu = await ctx.send(embed=embed)

        for i, role in enumerate(roles):
            await menu.add_reaction(utils.emoji[i+1])

        await self.bot.rmenus.update((ctx.guild.id, menu.id), 'role_ids', role_ids)

    @commands.command(cls=perms.Lock, level=2, guild_only=True, name='rmod', aliases=[], usage='rmod <menu> <*roles>')
    @commands.bot_has_permissions(add_reactions=True, manage_messages=True)
    async def rmod(self, ctx, menu_id, *role_ids):
        '''Modify a role menu.
        This command must be invoked in the channel containing the role menu.
        `menu` must be an ID of a role menu.
        `roles` must be a list of role IDs delimited by spaces.\n
        **Example:```yml\n .rmod 546836599141302272 122550600863842310 608148009213100033```**
        '''
        await ctx.message.delete()

        roles = []
        for role_id in role_ids:
            role = ctx.guild.get_role(int(role_id))
            if not role:
                return await ctx.send(f'{ctx.author.mention} One or more roles could not be resolved: `{role_id}` is invalid.', delete_after=5)

            roles.append(role)

        try:
            menu = await ctx.channel.fetch_message(menu_id)
            if not self.bot.rmenus.get((ctx.guild.id, menu.id)):
                raise discord.NotFound
        except discord.NotFound:
            return await ctx.send(f'{ctx.author.mention} Role menu with ID `{role_id}` could not be found.', delete_after=5)
        
        desc = ''
        for i, role in enumerate(roles):
            desc += f'**{i+1}.** {str(role)}\n'

        embed = menu.embeds[0]
        embed.description = desc.strip('\n')

        await menu.edit(embed=embed)

        for i in range(0, 15):
            if i > len(roles) - 1:
                await menu.clear_reaction(utils.emoji[i+1])
            else:
                await menu.add_reaction(utils.emoji[i+1])
        
        await self.bot.rmenus.update((ctx.guild.id, menu.id), 'role_ids', ' '.join(role_ids))
    
    @commands.command(cls=perms.Lock, level=2, guild_only=True, name='setranks', aliases=[], usage='setranks <*roles>')
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def setranks(self, ctx, *role_ids):
        '''Initialize rank roles.
        `roles` must be a list of role IDs delimited by spaces, ordered from lowest to highest in hierarchy.
        Replace `roles` with 'reset' to remove rank roles.\n
        **Example:```yml\n.setranks 546836599141302272 122550600863842310 608148009213100033```**
        '''
        if role_ids[0] == 'reset':
            await self.bot.ranks.update(ctx.guild.id, 'role_ids', '')
            await ctx.message.delete()
            return await ctx.send('Rank roles successfully reset.', delete_after=5)

        if not 2 <= len(role_ids) <= 6:
            await ctx.message.delete()
            return await ctx.send(f'{ctx.author.mention} Amount of rank roles must be between 2 and 6 inclusive.', delete_after=5)

        for id in role_ids:
            try:
                id = int(id)
            except:
                id = 0

            if not ctx.guild.get_role(id):
                await ctx.message.delete()
                return await ctx.send(f'{ctx.author.mention} One or more roles could not be resolved: `{id}` is invalid.', delete_after=5)

        await self.bot.ranks.update(ctx.guild.id, 'role_ids', ' '.join(role_ids))

        bottom_role = ctx.guild.get_role(int(role_ids[0]))
        for member in ctx.guild.members:
            if not member.bot:
                await member.add_roles(bottom_role)

        await ctx.send('Rank roles successfully initialized.')
    
    @commands.command(cls=perms.Lock, guild_only=True, name='ranks', aliases=[], usage='ranks')
    @commands.bot_has_guild_permissions(mention_everyone=True)
    async def ranks(self, ctx):
        '''Display rank hierarchy.
        **Example:```yml\n.ranks```**
        '''
        role_ids = None
        if self.bot.ranks.get(ctx.guild.id):
            role_ids = self.bot.ranks[ctx.guild.id]['role_ids']

        if role_ids:
            ranks = '\n'.join(ctx.guild.get_role(int(id)).mention for id in role_ids.split())

            embed = Embed(description=f'**{ranks}**')
            embed.set_author(name=ctx.guild, icon_url=ctx.guild.icon_url)
        else:
            embed = Embed(description=f'**{ctx.guild}** does not have ranks enabled.')

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Roles(bot))