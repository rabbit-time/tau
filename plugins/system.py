import asyncio
import os
import platform
import sys
import time

import psutil
import discord
from discord import Embed, File
from discord.ext import commands
from discord.utils import find

import config
import perms
import utils

class System(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(cls=perms.Lock, level=2, guild_only=True, name='config', aliases=['conf'], usage='config')
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.bot_has_permissions(add_reactions=True, external_emojis=True, manage_messages=True)
    async def config(self, ctx):
        '''Display or modify guild configuration.
        Config keys can be modified using the reaction menu.
        To select a key, enter the number that corresponds with that key.
        From there, enter the new value. Alternatively, typing \'reset\' will return the key back to its default value.
        Only one user may modify the config at a time to avoid input conflict.
        Note that command cannot be invoked while modifying the config.

        **`welcome_message`** and **`goodbye_message`** are dynamic. The following directives will be replaced automatically:
        **@user** - The user's display name.
        **@mention** - The user's mention.
        **@guild** - The guild's name.

        Toggles will be immediately modified on selection.\n
        **Example:```yml\n.config```**
        '''
        guild_id = ctx.guild.id
        default = self.bot.guilds_.default
        
        fields = {}
        toggles = {}
        def build():
            for k, v in self.bot.guilds_[guild_id].items():
                if isinstance(default[k], bool):
                    toggles[k] = v
                elif 'role' in k:
                    role = ctx.guild.get_role(v)
                    fields[k] = f'{str(role)} ({role.id})' if role else None
                elif 'channel' in k:
                    ch = ctx.guild.get_channel(v)
                    fields[k] = f'{str(ch)} ({ch.id})' if ch else None
                else:
                    fields[k] = v
        
            i = 1
            ilen = len(str(len(default))) + 1
            klen = len(max(fields.keys(), key=len))
            conf = ''
            for k, v in fields.items():
                align = ' ' * (klen-len(k))
                pad = ' ' * (ilen-len(str(i)))
                conf += f'{i}.{pad}{k}:{align} {v}\n'
                i += 1

            klen = len(max(toggles.keys(), key=len))
            conf2 = ''
            for k, v in toggles.items():
                tog = utils.emoji['on'] if v else utils.emoji['off']
                align = ' ' * (klen-len(k))
                pad = ' ' * (ilen-len(str(i)))
                conf2 += f'` {i}.{pad}{k}{align}` {tog}\n'
                i += 1

            return f'**```groovy\n{conf}```{conf2}**'    

        desc = build()
        embed = Embed(description=desc.strip('\n'))
        embed.set_author(name=ctx.guild.name, icon_url='attachment://unknown.png')
        x = '❌'
        menu = await ctx.send(file=File('assets/gear.png', 'unknown.png'), embed=embed)
        await menu.add_reaction(utils.emoji['settings'])

        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=90, check=lambda reaction, user: str(reaction.emoji) == utils.emoji['settings'] and reaction.message.id == menu.id and not user.bot)
                self.bot.suppressed[ctx.author] = menu.channel

                if user != ctx.author:
                    await reaction.remove(user)
                    continue

                await menu.clear_reactions()
                embed.description += '\n**\\*Please select a config key to edit.**'
                await menu.edit(embed=embed)
                await menu.add_reaction(x)

                while True:
                    on_msg = asyncio.create_task(self.bot.wait_for('message', check=lambda msg: msg.author == user))
                    on_react = asyncio.create_task(self.bot.wait_for('reaction_add', check=lambda reaction, user: str(reaction.emoji) == x and reaction.message.id == menu.id and not user.bot))
                    done, pending = await asyncio.wait([on_msg, on_react], timeout=90, return_when=asyncio.FIRST_COMPLETED)

                    for future in pending:
                        future.cancel()

                    if on_msg in done:
                        msg = done.pop().result()
                        await msg.delete()

                        if msg.channel != menu.channel:
                            raise asyncio.TimeoutError

                        n = int(msg.content) if msg.content.isdigit() else 0
                        if not 0 < n <= len(default):
                            await ctx.send(f'{ctx.author.mention} Sorry! Your input is not valid. Response must be an integer matching a value above.', delete_after=5)
                            continue
                        
                        n -= 1
                        key = tuple(fields.keys())[n] if n < len(fields) else tuple(toggles.keys())[n-len(fields)]
                        if key in fields.keys():
                            embed.description = desc + f'\n**\\*Modifying Current Buffer: `{key}`**'
                            embed.set_footer(text='\'reset\' to return to default')
                            await menu.edit(embed=embed)

                            on_msg = asyncio.create_task(self.bot.wait_for('message', check=lambda msg: msg.author == user))
                            on_react = asyncio.create_task(self.bot.wait_for('reaction_add', check=lambda reaction, user: str(reaction.emoji) == x and reaction.message == menu and not user.bot))
                            done, pending = await asyncio.wait([on_msg, on_react], timeout=90, return_when=asyncio.FIRST_COMPLETED)

                            for future in pending:
                                future.cancel()

                            if on_msg in done:
                                msg = done.pop().result()
                                await msg.delete()
                                
                                if msg.channel != menu.channel:
                                    embed.set_footer(text='')
                                    raise asyncio.TimeoutError

                                if msg.content == 'reset':
                                    val = default[key]
                                    await self.bot.guilds_.update(ctx.guild.id, key, default[key])
                                elif 'role' in key:
                                    role = find(lambda r: r.name == msg.content, ctx.guild.roles)
                                    if not role:
                                        role_id = int(msg.content) if msg.content.isdigit() else 0
                                        role = ctx.guild.get_role(role_id)
                                    
                                    if not role:
                                        await ctx.send(f'{ctx.author.mention} Sorry! A role named \'{msg.content}\' could not be found.', delete_after=5)
                                    else:
                                        await self.bot.guilds_.update(ctx.guild.id, key, role.id)
                                elif 'channel' in key:
                                    ch = find(lambda ch: ch.name == msg.content, ctx.guild.text_channels)
                                    if not ch:
                                        ch_id = int(msg.content) if msg.content.isdigit() else 0
                                        ch = ctx.guild.get_channel(ch_id)

                                    if not ch:
                                        await ctx.send(f'{ctx.author.mention} Sorry! A channel named \'{msg.content}\' could not be found.', delete_after=5)
                                    else:
                                        await self.bot.guilds_.update(ctx.guild.id, key, ch.id)
                                elif 'quantity' in key:
                                    qty = int(msg.content) if msg.content.isdigit() else 0
                                    if not 0 < qty < 256:
                                        await ctx.send(f'{ctx.author.mention} `star_quantity` must be an integer between 1 and 255.', delete_after=5)
                                    else:
                                        await self.bot.guilds_.update(ctx.guild.id, key, qty)
                                else:
                                    await self.bot.guilds_.update(ctx.guild.id, key, msg.content)

                                desc = build()
                                embed.description = desc + '\n**\\*Please select a config key to edit.**'
                                embed.set_footer(text='')
                                await menu.edit(embed=embed)
                            elif on_react in done:
                                reaction, reactor = done.pop().result()
                                if reactor != user:
                                    await reaction.remove(reactor)
                                    continue

                                raise asyncio.TimeoutError
                            else:
                                raise asyncio.TimeoutError
                        else:
                            val = 1 if not self.bot.guilds_[ctx.guild.id][key] else 0
                            await self.bot.guilds_.update(ctx.guild.id, key, val)

                            desc = build()
                            embed.description = desc + '\n**\\*Please select a config key to edit.**'
                            await menu.edit(embed=embed)
                    elif on_react in done:
                        reaction, reactor = done.pop().result()
                        if reactor != user:
                            await reaction.remove(reactor)
                            continue

                        raise asyncio.TimeoutError
                    else:
                        raise asyncio.TimeoutError
            except asyncio.TimeoutError:
                await menu.clear_reactions()
                if embed.description != desc.strip('\n'):
                    embed.description = desc.strip('\n')
                    await menu.edit(embed=embed)
            finally:
                try:
                    del self.bot.suppressed[ctx.author]
                except:
                    pass
                break

    @commands.command(cls=perms.Lock, level=5, name='reload', aliases=['r'], usage='reload <ext>')
    async def reload(self, ctx, path):
        '''Reload an extension.
        `ext` must be the dot path to the extension relative to the entry point of the app.\n
        **Example:```yml\n.reload plugins.system\n.r events.on_ready```**
        '''
        try:
            self.bot.reload_extension(path)

            desc = f'yml\n+ {path} has been reloaded'
            color = 0x2aa198
        except (commands.ExtensionFailed, commands.ExtensionNotLoaded, commands.NoEntryPointError) as err:
            desc = f'diff\n- {err}'
            color = 0xff4e4e

        embed = Embed(description=f'**```{desc}```**', color=color)
        
        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, level=4, name='remove', aliases=['leave', 'rem'], usage='remove [id]')
    async def remove(self, ctx, id: int):
        '''Remove a server.\n
        If an ID is not given, the current server will be removed.
        **Example:```yml\n.remove 546397670793805825\n.leave```**
        '''
        guild = self.bot.get_guild(id)
        if not guild:
            guild = ctx.guild

        await guild.leave()

        if ctx.guild != guild:
            desc = f'**```diff\n- {guild.name} has been removed```**'
            embed = Embed(description=desc, color=0xff4e4e)

            await ctx.send(embed=embed)
    
    @commands.command(cls=perms.Lock, guild_only=True, name='rule', aliases=[], usage='rule <index>')
    @commands.bot_has_permissions(external_emojis=True, mention_everyone=True)
    async def rule(self, ctx, index: int):
        '''Cite a rule.\n
        **Example:```yml\n.rule 1```**
        '''
        rule = self.bot.rules.get((ctx.guild.id, index), {'rule': ''})

        print(self.bot.guilds_._records.items())

        if not rule['rule']:
            return await ctx.send(f'{ctx.author.mention} Rule with index **`{index}`** could not be found.', delete_after=5)

        embed = Embed(title='Rules', description=f'**{index}.** {rule["rule"]}')

        await ctx.send(embed=embed)
    
    @commands.command(cls=perms.Lock, level=1, guild_only=True, name='rules', aliases=[], usage='rules')
    @commands.bot_has_permissions(external_emojis=True, mention_everyone=True)
    async def rules(self, ctx):
        '''Display the rules.\n
        **Example:```yml\n.rules```**
        '''
        rules = await self.bot.con.fetch('SELECT index_, rule FROM rules WHERE guild_id = $1 ORDER BY index_ ASC', ctx.guild.id)

        if not rules:
            return await ctx.send(f'{ctx.author.mention} Rules have not been initialized.', delete_after=5)

        board = ''
        for index, rule in rules:
            board += f'**{index}.** {rule}\n'

        embed = Embed(title='Rules', description=board)

        await ctx.send(embed=embed)
    
    @commands.command(cls=perms.Lock, level=2, guild_only=True, name='setrule', aliases=[], usage='setrule <index> [rule]')
    @commands.bot_has_permissions(external_emojis=True, mention_everyone=True)
    async def setrule(self, ctx, index: int, *, rule: str = ''):
        '''Set a rule.
        `index` must be a positive integer no larger than 255.
        Leave `rule` blank to reset.\n
        **Example:```yml\n.setrule 1 Do not spam```**
        '''
        if not 0 <= index < 256:
            raise commands.BadArgument

        if rule:
            await self.bot.rules.update((ctx.guild.id, index), 'rule', rule)
        else:
            await self.bot.rules.delete((ctx.guild.id, index))

        embed = Embed(title='Rules')

        if rule:
            desc = f'**{index}.** {rule}'
        else:
            desc = f'**```yml\n+ Rule {index} has been reset```**'
            embed.colour = utils.Color.green

        embed.description = desc

        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, level=5, name='shutdown', aliases=['exit', 'quit', 'kill'], usage='shutdown')
    async def shutdown(self, ctx):
        '''Shut down the bot.\n
        **Example:```yml\n.shutdown\n.exit```**
        '''
        embed = Embed(description='**```diff\n- Shutting down...```**', color=utils.Color.red)

        await ctx.send(embed=embed)

        await self.bot.con.close()
        await self.bot.close()
        os._exit(0)

def setup(bot):
    bot.add_cog(System(bot))