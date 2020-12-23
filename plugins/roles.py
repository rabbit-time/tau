import asyncio
import io
import random
from typing import Tuple

import discord
from discord import Embed, File
from discord.ext import commands
from discord.ext.commands import command, guild_only, dm_only
from discord.utils import find

import utils
from utils import level

class Ranks(commands.Converter):
    async def convert(self, ctx, arg):
        arg = arg.split()
        try:
            return [(int(arg[i]), ctx.guild.get_role(int(arg[i+1]))) for i in range(0, len(arg), 2)]
        except:
            raise commands.BadArgument

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
        role_ids = self.bot.rmenus[guild.id, payload.message_id]['role_ids']
        
        return guild.get_role(role_ids[i])

    @commands.Cog.listener()
    async def on_message(self, msg):
        member = msg.author
        uid = member.id
        guild = msg.guild
        chan = msg.channel

        if member.bot or not guild:
            return

        if not self.bot.members.get((uid, guild.id)):
            await self.bot.members.insert((uid, guild.id))

        prefix = self.bot.guilds_[guild.id]['prefix']
        if not msg.content.startswith(prefix) and (member not in self.bot.suppressed.keys() or self.bot.suppressed.get(member) != chan):
            bucket = self._cd.get_bucket(msg)
            limited = bucket.update_rate_limit()
            if not limited:
                # Add xp to user
                xp = self.bot.members[uid, guild.id]['xp']
                newxp = xp + random.randint(10, 20)
                await self.bot.members.update((uid, guild.id), 'xp', newxp)
                
                # Rank roles
                if self.bot.ranks.get(guild.id) and (role_ids := self.bot.ranks[guild.id]['role_ids']):
                    levels = self.bot.ranks[guild.id]['levels']
                    roles = [guild.get_role(id) for id in role_ids]
                    if None in roles:
                        await self.bot.ranks.update(guild.id, 'role_ids', [])
                        await self.bot.ranks.update(guild.id, 'levels', [])
                        return

                    rank = None
                    for i in range(0, len(roles), -1):
                        if level(newxp) >= levels[i]:
                            rank = roles.pop(i)
                            break

                    await member.remove_roles(*roles)
                    if rank:
                        await member.add_roles(rank)

                    # Send level up message if enabled in guild config.
                    if level(xp) is not level(newxp) and self.bot.guilds_[guild.id]['levelup_messages']:
                        if level(newxp) in levels:
                            desc = f'**{member.display_name} has ranked up to {rank.mention}!**'
                            embed = Embed(description=desc, color=rank.color)
                            embed.set_author(name=member.display_name, icon_url=member.avatar_url)

                            await chan.send(embed=embed)
                        else:
                            desc = f'**```yml\n↑ {level(newxp)} ↑ {member.display_name} has leveled up!```**'
                            embed = Embed(description=desc, color=utils.Color.green)
                            embed.set_author(name=member.display_name, icon_url=member.avatar_url)

                            await chan.send(embed=embed)

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
            limit = self.bot.rmenus[guild.id, payload.message_id]['limit_']
            role_ids = self.bot.rmenus[guild.id, payload.message_id]['role_ids']
            roles = [guild.get_role(id) for id in role_ids]
            n = 0
            for role in roles:
                if role in member.roles:
                    n += 1

            role = self.get_role(member, guild, payload)
            if n < limit or limit == 0:
                await member.add_roles(role)
            else:
                chan = guild.get_channel(payload.channel_id)
                msg = await chan.fetch_message(payload.message_id)
                await msg.remove_reaction(payload.emoji, member)
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)

        role = self.get_role(member, guild, payload)
        if role:
            await member.remove_roles(role)

    @command(name='addall', usage='addall <role>')
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.bot_has_permissions(external_emojis=True, manage_messages=True)
    @guild_only()
    async def addall(self, ctx, role: discord.Role):
        '''Add a role to every member in the server.
        Cannot be an unaddable role.\n
        **Example:```yml\n♤addall rolename\n♤addall 546836599141302272```**
        '''
        if role == ctx.guild.default_role or ctx.guild.me.top_role <= role:
            raise commands.BadArgument
        
        members = list(filter(lambda m: not m.bot, ctx.guild.members))

        desc = f'**Adding {role.mention} to members...'
        embed = Embed(color=utils.Color.sky)
        embed.set_author(name='Roles', icon_url='attachment://unknown.png')
        embed.description = desc + f'\n`[                    ] 0% (0/{len(members)})`**'

        i = 0
        msg = await ctx.send(file=File('assets/dot.png', 'unknown.png'), embed=embed)
        for member in members:
            await member.add_roles(role)

            i += 1
            if i % 5 == 0:
                percent = i // len(members) * 100
                bar = '█'
                progress = bar * (percent//5)
                space = 20 - len(progress)
                embed.description = desc + f'`[{progress}{space}] {percent}% ({i}/{len(members)})`**'
                
                await msg.edit(embed=embed)
        else:
            embed.description = desc + f' Complete!\n`[{bar*20}] 100% ({i}/{len(members)})`**'

            await msg.edit(embed=embed)

    @command(name='rolemenu', aliases=['rmenu'], usage='rolemenu <title> | <color> | <*roles>')
    @commands.has_guild_permissions(manage_guild=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.bot_has_permissions(add_reactions=True, external_emojis=True, manage_messages=True)
    @guild_only()
    async def rolemenu(self, ctx, *roles: discord.Role):
        '''Create a role menu.
        Role menus are powered by message reactions and can hold up to 15 roles.
        `roles` must be a series of valid role IDs delimited by spaces.
        The menu can be further customized with the embed commands.\n
        **Example:```yml\n♤rolemenu 546836599141302272```**
        '''
        await ctx.message.delete()

        if len(roles) > 15:
            raise commands.BadArgument

        desc = ''
        for i, role in enumerate(roles):
            desc += f'**{i+1}.** {str(role)}\n'
        embed = Embed(title='Role menu', description=desc.strip('\n'))

        menu = await ctx.send(embed=embed)

        for i, role in enumerate(roles):
            await menu.add_reaction(utils.emoji[i+1])

        await self.bot.rmenus.update((ctx.guild.id, menu.id), 'role_ids', [role.id for role in roles])

    @command(name='rmlimit', usage='rmlimit <menu> <limit>')
    @commands.has_guild_permissions(manage_guild=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.bot_has_permissions(add_reactions=True, external_emojis=True, manage_messages=True)
    @guild_only()
    async def rmlimit(self, ctx, menu: discord.Message, limit: int):
        '''Add a role limit to a role menu.
        This command must be invoked in the channel containing the role menu.
        `menu` must be a reference to a message with a role menu.
        `limit` must be a positive integer. Set to 0 to remove the limit.\n
        **Example:```yml\n♤rmlimit 546836599141302272 1```**
        '''
        if limit < 0:
            raise commands.BadArgument

        desc = f'**```yml\n+ Role limit has been set to 1```**'
        embed = Embed(description=desc, color=utils.Color.green)

        msg = await ctx.send(embed=embed)

        await self.bot.rmenus.update((ctx.guild.id, menu.id), 'limit_', limit)

        await asyncio.sleep(5)
        await msg.delete()
        await ctx.message.delete()

    @command(name='rmod', usage='rmod <menu> <*roles>')
    @commands.has_guild_permissions(manage_guild=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.bot_has_permissions(add_reactions=True, external_emojis=True, manage_messages=True)
    @guild_only()
    async def rmod(self, ctx, menu: discord.Message, *roles: discord.Role):
        '''Modify the roles in a role menu.
        This command must be invoked in the channel containing the role menu.
        `menu` must be an ID of a message containing role menu.
        `roles` must be a list of role IDs delimited by spaces.\n
        **Example:```yml\n♤rmod 546836599141302272 122550600863842310 608148009213100033```**
        '''
        await ctx.message.delete()

        if not self.bot.rmenus.get((ctx.guild.id, menu.id)):
            return await ctx.send(f'{ctx.author.mention} Message with ID `{menu.id}` could not be found.', delete_after=5)
        
        embed = menu.embeds[0]
        embed.description = '\n'.join(f'**{i+1}.** {role}' for i, role in enumerate(roles))

        await menu.edit(embed=embed)

        for i in range(15):
            if i > len(roles) - 1:
                await menu.clear_reaction(utils.emoji[i+1])
            else:
                await menu.add_reaction(utils.emoji[i+1])
        
        await self.bot.rmenus.update((ctx.guild.id, menu.id), 'role_ids', [role.id for role in roles])
    
    @command(name='setranks', usage='setranks <*ranks>')
    @commands.has_guild_permissions(manage_guild=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_messages=True)
    @guild_only()
    async def setranks(self, ctx, *, roles: Ranks = None):
        '''Initialize rank roles.
        `ranks` should be a sequence of pairs matching levels to role IDs where the level represents the level needed to level up.
        The list must not include roles that are managed by integrations such as Twitch or Discord bots.
        Leave blank to reset all rank roles.\n
        **Example:```yml\n♤setranks 1 546836599141302272 5 122550600863842310 10 608148009213100033```**
        '''
        desc = '**Rank roles successfully '
        embed = Embed(color=utils.Color.sky)
        embed.set_author(name='Ranks', icon_url='attachment://unknown.png')
        if roles == None:
            await self.bot.ranks.update(ctx.guild.id, 'role_ids', [])
            embed.description = desc + 'reset.**'

            return await ctx.send(file=File('assets/dot.png', 'unknown.png'), embed=embed)

        levels = []
        ranks = []
        roles.sort(key=lambda x: x[0])
        for level_, role in roles:
            levels.append(level_)
            ranks.append(role)

            # Check if bot role is higher
            tau_role = find(lambda r: r.managed, ctx.guild.me.roles)
            if role == None or role.managed or role.is_default() or level_ < 0:
                raise commands.BadArgument
            elif role > tau_role:
                desc = f'**{role.mention} must be lower in hierarchy than {tau_role.mention}.**'
                embed = Embed(description=desc, color=utils.Color.red)
                embed.set_author(name='Missing permissions', icon_url='attachment://unknown.png')

                return await ctx.send(file=File('assets/dot.png', 'unknown.png'), embed=embed)

        await self.bot.ranks.update(ctx.guild.id, 'levels', levels)
        await self.bot.ranks.update(ctx.guild.id, 'role_ids', [rank.id for rank in ranks])

        members = list(filter(lambda m: not m.bot, ctx.guild.members))

        desc += 'initialized.\n\nApplying roles to members...'
        embed.description = desc + f'\n`[                    ] 0% (0/{len(members)})`**'

        i = 0
        msg = await ctx.send(file=File('assets/dot.png', 'unknown.png'), embed=embed)
        for member in members:
            key = member.id, ctx.guild.id
            if not self.bot.members.get(key):
                await self.bot.members.insert(key)
            
            member_lvl = level(self.bot.members[key]['xp'])
            levels.reverse()
            ranks.reverse()
            for level_, rank in zip(levels, ranks):
                if level_ <= member_lvl:
                    await member.add_roles(rank)
                    break
            
            i += 1
            if i % 5 == 0:
                percent = i // len(members) * 100
                bar = '█'
                progress = bar * (percent//5)
                space = 20 - len(progress)
                embed.description = desc + f'`[{progress}{space}] {percent}% ({i}/{len(members)})`**'
                
                await msg.edit(embed=embed)
        else:
            embed.description = desc + f' Complete!\n`[{bar*20}] 100% ({i}/{len(members)})`**'

            await msg.edit(embed=embed)

    @command(name='ranks', usage='ranks')
    @commands.has_guild_permissions(manage_guild=True)
    @commands.bot_has_guild_permissions(mention_everyone=True)
    @guild_only()
    async def ranks(self, ctx):
        '''Display rank hierarchy.
        **Example:```yml\n♤ranks```**
        '''
        role_ids = self.bot.ranks[ctx.guild.id]['role_ids'] if self.bot.ranks.get(ctx.guild.id) else []
        roles = [ctx.guild.get_role(id) for id in role_ids]
        if roles and None not in roles:
            levels = self.bot.ranks[ctx.guild.id]['levels']
            space = ' '
            big = len(str(levels[-1]))
            ranks = '\n'.join(f'`{lvl}.{space*(big-len(str(lvl)))}`\u3000{role.mention}' for role, lvl in zip(roles, levels))

            file = None
            embed = Embed(color=utils.Color.sky)
            embed.set_author(name=ctx.guild, icon_url=ctx.guild.icon_url)
            embed.add_field(name='__Level__   __Rank__', value=f'**{ranks}**')
        else:
            file = File('assets/reddot.png', 'unknown.png')
            embed = Embed(description=f'**{ctx.guild} does not have ranks enabled.**', color=utils.Color.red)
            embed.set_author(name='Ranks unavailable', icon_url='attachment://unknown.png')

        await ctx.send(file=file, embed=embed)

def setup(bot):
    bot.add_cog(Roles(bot))