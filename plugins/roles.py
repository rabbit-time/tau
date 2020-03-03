import asyncio

import discord
from discord import Embed, File
from discord.ext import commands

import perms
import utils

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(cls=perms.Lock, level=2, guild_only=True, name='role', aliases=[], usage='role <id>')
    async def role(self, ctx, id: int):
        '''Displays role info.\n
        **Example:```yml\n .role 657766595321528349```**
        '''
        role = ctx.guild.get_role(id)
        if not role:
            return await ctx.send(f'{ctx.author.mention} Role with ID `{id}` not found.')

        desc = (f'**{str(role)}\n`{len(role.members)} member{"s" if len(role.members) > 1 else ""}`**')
        embed = Embed(description=desc)
        embed.set_footer(text=f'ID: {id}')
        
        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, level=2, guild_only=True, name='rolemenu', aliases=['rmenu'], usage='rolemenu <title> | <color> | <*roles>')
    async def rolemenu(self, ctx, *data):
        '''Create a role menu.
        Role menus are powered by message reactions and can hold up to 15 roles. 
        Arguments must be separated by pipes: `|`
        *title* must be no more than 256 characters long.
        *color* must be a color represented in hexadecimal format.
        *roles* must be a list of role IDs delimited by spaces.\n
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

        ids = ''
        for i, role in enumerate(roles):
            await menu.add_reaction(utils.emoji[i+1])
            ids += str(role.id) + ' '

        await self.bot.rmenus.update((ctx.guild.id, menu.id), 'role_ids', ids)

def setup(bot):
    bot.add_cog(Roles(bot))