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
        memo = '📝'
        x = '❌'
        menu = await ctx.send(file=File('assets/gear.png', 'unknown.png'), embed=embed)
        await menu.add_reaction(memo)

        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=90, check=lambda reaction, user: str(reaction.emoji) == memo and reaction.message.id == menu.id and not user.bot)
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

    @commands.command(cls=perms.Lock, level=5, name='debug', aliases=[], usage='debug <code>')
    async def debug(self, ctx, *code):
        '''Runs Python code.\n
        **Example:```yml\n.debug print('hello world')```**
        '''
        ch = ctx.guild.get_channel(606482360309121024)
        staff = ctx.guild.get_role(546836599141302272)
        desc = f'''**```md
            # Progress
            ```**
            {utils.emoji["progress"]} A Discord community for civil discourse about philosophy, politics, and more. Progress is a platform for open dialogue and debate to aid human progress even if it is on a small scale.

            **```diff
            - Rules
            ```*`These are just basic guidelines. Use common sense ー just because it is not mentioned here does not mean it is allowed.`***

            **1.** Do not harass other users.\n
            **2.** Do not spam.\n
            **3.** Usernames must be mentionable.\n
            **4.** All forms of discrimination are unacceptable.\n
            **5.** Communicate only in English.\n
            **6.** Do not dox another user.\n
            **7.** Any NSFW content is strictly prohibited including user profiles, messages, images, links, etc.\n
            **8.** Post in the right channel; see channel descriptions for details.\n
            **9.** Do not promote other Discord servers without permission from **{staff.mention}**.\n
            **10.** Adhere to the Discord Terms of Service: **https://discordapp.com/terms**

            **```py
            @ Roles
            ```**
            Be sure to visit the {ch.mention} menu to assign descriptive, philosophical, and political roles to help you stand out! These roles are completely cosmetic.

            **```yml
            + Invite
            ```**
            Share to help us progress: **{config.invite}**'''
        embed = Embed(description=desc.replace(' '*12, ''))
        await ctx.send(embed=embed)

        '''
        code = ctx.message.content[7:].strip('`\n')
        if code.startswith('py\n'):
            code = code[3:]

        try:
            eval(code)
        except Exception as error:
            embed = Embed(description=f'```py\n{error}```', color=0xff4e4e)
            await ctx.send(embed=embed)'''

    @commands.command(cls=perms.Lock, level=5, name='reboot', aliases=['r', 'restart'], usage='reboot')
    async def reboot(self, ctx):
        '''Restart the bot.\n
        **Example:```yml\n.reboot```**
        '''
        embed = Embed(description='**```yml\nRestarting...```**', color=0x2aa198)
        await ctx.send(embed=embed)
        
        await self.bot.con.close()
        os.execv(sys.executable, ['python'] + sys.argv)

    @commands.command(cls=perms.Lock, level=5, name='shutdown', aliases=['exit', 'quit', 'poweroff'], usage='shutdown')
    async def shutdown(self, ctx):
        '''Shut down the bot.\n
        **Example:```yml\n.shutdown\n.exit```**
        '''
        await ctx.send('**`Shutting down...`**')

        await self.bot.con.close()
        await self.bot.close()
        os._exit(0)

def setup(bot):
    bot.add_cog(System(bot))