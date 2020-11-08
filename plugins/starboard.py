import asyncio

import discord
from discord import Embed
from discord.ext import commands

class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        emoji = str(payload.emoji)
        member = payload.member
        guild = member.guild
        if emoji == '⭐':
            starchan = guild.get_channel(self.bot.guilds_[guild.id]['starboard_channel'])
            chan = guild.get_channel(payload.channel_id)
            if chan and starchan:
                try:
                    msg = await chan.fetch_message(payload.message_id)
                except discord.NotFound:
                    return
                    
                stars = 0
                for reaction in msg.reactions:
                    if str(reaction.emoji) == '⭐':
                        stars += reaction.count

                embed = Embed(description=msg.content, color=0xffc20c)
                embed.set_author(name=msg.author.display_name, icon_url=msg.author.avatar_url)
                embed.add_field(name='Source', value=f'**[Jump!]({msg.jump_url})**')
                if msg.attachments:
                    file = msg.attachments[0]
                    if file.url.lower().endswith(('png', 'jpeg', 'jpg', 'gif', 'webp')):
                        embed.set_image(url=file.url)
                embed.set_footer(text=msg.id)
                embed.timestamp = msg.created_at
                    
                def star_emoji(stars):
                    if 5 > stars >= 0:
                        return '⭐'
                    elif 10 > stars >= 5:
                        return '🌟'
                    elif 25 > stars >= 10:
                        return '💫'
                    else:
                        return '✨'
                        
                qty = self.bot.guilds_[guild.id]['star_quantity']
                if stars < qty:
                    return
                if self.bot.stars.get(msg.id):
                    try:
                        starmsg = await starchan.fetch_message(self.bot.stars[msg.id]['star_id'])
                        await starmsg.edit(content=f'{star_emoji(stars)} **{stars}**', embed=embed)
                    except discord.NotFound:
                        await self.bot.stars.delete(msg.id)
                else:
                    lock = asyncio.Lock()
                    async with lock:
                        starmsg = await starchan.send(f'{star_emoji(stars)} **{stars}**', embed=embed)
                        await self.bot.stars.update(msg.id, 'star_id', starmsg.id)
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        emoji = str(payload.emoji)
        guild = self.bot.get_guild(payload.guild_id)
        if emoji == '⭐' and self.bot.stars.get(payload.message_id):
            starchan = guild.get_channel(self.bot.guilds_[guild.id]['starboard_channel'])
            chan = guild.get_channel(payload.channel_id)
            if chan and starchan:
                try:
                    msg = await chan.fetch_message(payload.message_id)
                except discord.NotFound:
                    return
            
            stars = 0
            for reaction in msg.reactions:
                if str(reaction.emoji) == '⭐':
                    stars += reaction.count
            
            embed = Embed(description=msg.content, color=0xffc20c)
            embed.set_author(name=msg.author.display_name, icon_url=msg.author.avatar_url)
            embed.add_field(name='Source', value=f'**[Jump!]({msg.jump_url})**')
            if msg.attachments:
                file = msg.attachments[0]
                if file.url.lower().endswith(('png', 'jpeg', 'jpg', 'gif', 'webp')):
                    embed.set_image(url=file.url)
            embed.set_footer(text=msg.id)
            embed.timestamp = msg.created_at
                
            def star_emoji(stars):
                if 5 > stars >= 0:
                    return '⭐'
                elif 10 > stars >= 5:
                    return '🌟'
                elif 25 > stars >= 10:
                    return '💫'
                else:
                    return '✨'

            qty = self.bot.guilds_[guild.id]['star_quantity']
            try:
                starmsg = await starchan.fetch_message(self.bot.stars[msg.id]['star_id'])
            except discord.NotFound:
                return await self.bot.stars.delete(msg.id)

            if stars < qty:
                await starmsg.delete()
                await self.bot.stars.delete(msg.id)
            else:
                await starmsg.edit(content=f'{star_emoji(stars)} **{stars}**', embed=embed)

def setup(bot):
    bot.add_cog(Starboard(bot))