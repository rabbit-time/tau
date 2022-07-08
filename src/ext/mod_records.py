from __future__ import annotations
from typing import TYPE_CHECKING

import discord
from discord import Embed
from discord.ext import commands

from utils import Color

if TYPE_CHECKING:
    from tau import Tau


class ModRecords(commands.Cog):
    def __init__(self, bot: Tau):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        await self.bot.wait_until_synced()

        guild_conf = self.bot.guild_confs(channel.guild)
        if channel.id == guild_conf.log_channel_id:
            await guild_conf.set('log_channel_id', None)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        webhook = await self.bot.mod_records.get_webhook(member.guild)
        if webhook is not None:
            embed = (
                Embed(title='Member join', color=Color.green)
                .set_author(name=member, icon_url=member.avatar)
                .set_footer(text=f'ID: {member.id}')
            )
            await webhook.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        webhook = await self.bot.mod_records.get_webhook(member.guild)
        if webhook is not None:
            embed = (
                Embed(title='Member leave', color=Color.red)
                .set_author(name=member, icon_url=member.avatar)
                .set_footer(text=f'ID: {member.id}')
            )
            await webhook.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        webhook = await self.bot.mod_records.get_webhook(message.guild)
        if webhook is not None and webhook.channel != message.channel:
            embed = (
                Embed(description=f'**Message deleted in {message.channel.mention}:**', color=Color.red)
                .set_author(name=message.author, icon_url=message.author.avatar)
                .set_footer(text=f'User ID: {message.author.id}')
            )
            if len(message.content) > 0:
                embed.description += f'\n>>> {message.content}'

            file = None
            if len(message.attachments) > 0:
                attachment = message.attachments[0]
                if attachment.url.lower().endswith(('png', 'jpeg', 'jpg', 'gif', 'webp')):
                    file = await attachment.to_file(use_cached=True)
                    embed.set_image(url=f'attachment://{file.filename}')

            await webhook.send(file=file, embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or before.content == after.content:
            return

        webhook = await self.bot.mod_records.get_webhook(before.guild)
        if webhook is not None and webhook.channel != before.channel:
            if len(before.content) > 1024 or len(after.content) > 1024:
                embed = (
                    Embed(title='Message edit', description=f'**Before**\n> {before.content}', color=Color.gold)
                    .set_author(name=before.author, icon_url=before.author.avatar)
                    .set_footer(text=f'User ID: {before.author.id}')
                )
                await webhook.send(embed=embed)

                embed = (
                    Embed(description=f'**After**\n> {after.content}', color=Color.gold)
                    .add_field(name='Source', value=f'**[Jump!]({after.jump_url})**')
                    .set_footer(text=f'User ID: {after.author.id}')
                )
                await webhook.send(embed=embed)
            else:
                embed = (
                    Embed(title='Message edit', color=Color.gold)
                    .set_author(name=after.author, icon_url=after.author.avatar)
                    .add_field(name='Before', value=f'> {before.content}', inline=False)
                    .add_field(name='After', value=f'> {after.content}', inline=False)
                    .add_field(name='Source', value=f'**[Jump!]({after.jump_url})**')
                    .set_footer(text=f'User ID: {before.author.id}')
                )
                await webhook.send(embed=embed)


async def setup(bot: Tau):
    await bot.add_cog(ModRecords(bot))
