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
        self._cd = commands.CooldownMapping.from_cooldown(10, 120.0, commands.BucketType.user)
    
    def get_role(self, member, guild, payload):
        emojis = tuple(utils.emoji.values())
        emoji = str(payload.emoji)
        if not self.bot.rmenus.get((guild.id, payload.message_id)) or member.bot or emoji not in emojis:
            return
        
        i = tuple(utils.emoji.keys())[emojis.index(emoji)] - 1
        role_ids = self.bot.rmenus[guild.id, payload.message_id]['role_ids'].split()
        
        return guild.get_role(int(role_ids[i]))

    @commands.Cog.listener()
    async def on_message(self, msg):
        member = msg.author
        uid = member.id
        guild = msg.guild
        chan = msg.channel

        if member.bot or not guild:
            return

        # Rank roles 
        if not self.bot.members.get((uid, guild.id)):
            await self.bot.members.insert((uid, guild.id))

        if self.bot.ranks.get(guild.id) and (role_ids := self.bot.ranks[guild.id]['role_ids']):
            bucket = self._cd.get_bucket(msg)
            limited = bucket.update_rate_limit()
            if not limited:
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
                        desc = f'**```yml\n{member.display_name} has ranked up to {rank}!```**'
                        embed = Embed(description=desc, color=0x2aa198)
                        await chan.send(embed=embed)

                    if rank not in member.roles:        
                        await member.add_roles(rank)
                        
                    break
    
    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        if self.bot.rmenus.get((payload.guild_id, payload.message_id)):
            await self.bot.rmenus.delete((payload.guild_id, payload.message_id))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        member = payload.member
        guild = member.guild
        
        role = self.get_role(member, guild, payload)
        if role:
            await member.add_roles(role)
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)

        role = self.get_role(member, guild, payload)
        if role:
            await member.remove_roles(role)

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