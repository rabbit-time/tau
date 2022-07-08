from __future__ import annotations
from typing import TYPE_CHECKING

import datetime

import discord
from discord import app_commands
from discord import Embed, File
from discord.app_commands import Choice, Transform
from discord.ext import commands
from discord.utils import escape_markdown

from utils import Color, MessageTransformer
from utils.tags import Tag

if TYPE_CHECKING:
    from tau import Tau


class System(commands.Cog):
    def __init__(self, bot: Tau):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await self.bot.wait_until_synced()

        await self.bot.guild_confs.add(guild)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        await self.bot.wait_until_synced()

        await self.bot.guild_confs.remove(guild)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.bot.wait_until_synced()

        await self.bot.members.remove(member)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        guild_conf = self.bot.guild_confs(role.guild)
        if role.id == guild_conf.autorole_id:
            await guild_conf.set('autorole_id', None)
        if role.id == guild_conf.verify_role_id:
            await guild_conf.set('verify_role_id', None)
        if role.id == guild_conf.verify_role_id:
            await guild_conf.set('verify_role_id', None)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return

        await self.bot.wait_until_synced()

        guild_conf = self.bot.guild_confs(member.guild)
        welcome_message = guild_conf.welcome_message
        system_channel = member.guild.system_channel
        if welcome_message is not None and system_channel is not None:
            parsed_welcome_message = (
                welcome_message
                .replace('%user', escape_markdown(str(member)))
                .replace('%name', escape_markdown(member.display_name))
                .replace('%server', escape_markdown(member.guild.name))
            )
            embed = (
                Embed(description=parsed_welcome_message, color=Color.green)
                .set_author(name=member, icon_url=member.avatar.url)
                .set_footer(text='Join', icon_url='attachment://unknown.png')
            )
            embed.timestamp = discord.utils.utcnow()

            await system_channel.send(member.mention, embed=embed, file=File('assets/join.png', 'unknown.png'))

        autorole = member.guild.get_role(guild_conf.autorole_id)
        if autorole is not None:
            await member.add_roles(autorole)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.bot:
            return

        await self.bot.wait_until_synced()

        guild_conf = self.bot.guild_confs(member.guild)
        goodbye_message = guild_conf.goodbye_message
        system_channel = member.guild.system_channel
        if goodbye_message is not None and system_channel is not None:
            parsed_goodbye_message = (
                goodbye_message
                .replace('%user', escape_markdown(str(member)))
                .replace('%name', escape_markdown(member.display_name))
                .replace('%server', escape_markdown(member.guild.name))
            )
            embed = (
                Embed(description=parsed_goodbye_message, color=Color.red)
                .set_author(name=member, icon_url=member.avatar.url)
                .set_footer(text='Leave', icon_url='attachment://unknown.png')
            )
            embed.timestamp = datetime.datetime.utcnow()

            await system_channel.send(embed=embed, file=File('assets/leave.png', 'unknown.png'))

    tag = app_commands.Group(name='tag', description='Tag system', guild_only=True)

    @tag.command(name='make')
    @app_commands.describe(name='the name of the role menu')
    @app_commands.describe(message='the ID of the message to use as a tag')
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.checks.bot_has_permissions(external_emojis=True)
    async def tag_make(self, interaction: discord.Interaction, name: str, message: Transform[discord.Message, MessageTransformer]):
        '''Make a tag'''
        # Make sure name isn't already a command or an alias
        tag = self.bot.tags.get(interaction.guild, name.lower())
        if tag is not None:
            raise app_commands.AppCommandError

        # Get embed from message and convert JSON string
        embed = message.embeds[0] if message.embeds else None

        # Save
        tag = Tag(guild_id=interaction.guild.id, name=name.lower(), embed=embed, content=message.content)
        await self.bot.tags.add(tag)

        embed = (
            Embed(description=f'You can now reference this tag using **`/tag get {tag.name}`**', color=Color.primary)
            .set_author(name='Tag created', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'))

    @tag.command(name='get')
    @app_commands.checks.bot_has_permissions(external_emojis=True)
    async def tag_get(self, interaction: discord.Interaction, name: str):
        '''Get a tag'''
        tag = await self.bot.tags.get(interaction.guild, name)

        await interaction.response.send_message(tag.content, embed=tag.embed)

    @staticmethod
    @tag_get.autocomplete('name')
    async def tag_autocomplete(interaction: discord.Interaction, current: str, namespace: app_commands.Namespace) -> list[Choice[str]]:
        tags = interaction.client.tags.search(interaction.guild, current)
        return [Choice(name=tag.name, value=tag.name) for tag in tags]

    @tag.command(name='delete')
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.checks.bot_has_permissions(external_emojis=True)
    async def tag_delete(self, interaction: discord.Interaction, name: str):
        '''Delete a tag'''
        embed = Embed(color=Color.red)
        if self.bot.tags.get(interaction.guild, name) is not None:
            # If exists, delete
            await self.bot.tags.remove(interaction.guild, name)

            file = File('assets/trashcan.png', 'unknown.png')
            embed.set_author(name=f'Tag "{name}" has been deleted', icon_url='attachment://unknown.png')
            ephemeral = False
        else:
            # Otherwise, don't
            file = File('assets/reddot.png', 'unknown.png')
            embed.set_author(name=f'Tag "{name}" does not exist', icon_url='attachment://unknown.png')
            ephemeral = True

        await interaction.response.send_message(embed=embed, file=file, ephemeral=ephemeral)


async def setup(bot: Tau):
    await bot.add_cog(System(bot))
