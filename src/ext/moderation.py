from __future__ import annotations
from typing import TYPE_CHECKING

import datetime

import discord
from discord import Embed, File
from discord import app_commands
from discord.app_commands import checks
from discord.app_commands import command, describe, guild_only, Range, Transform
from discord.ext import commands

from utils import Color, Emoji, MessageTransformer

if TYPE_CHECKING:
    from tau import Tau


class Moderation(commands.Cog):
    def __init__(self, bot: Tau):
        self.bot = bot

    @command(name='ban')
    @describe(delete_messages_days='The number of days to delete the user\'s messages')
    @checks.has_permissions(ban_members=True)
    @checks.bot_has_permissions(ban_members=True, external_emojis=True, manage_messages=True)
    @guild_only()
    # TODO: annotate | None
    async def ban(self, interaction: discord.Interaction, member: discord.Member, delete_messages_days: Range[int, 0, 7] = 0, reason: Range[str, 1, 1024] = None):
        '''Ban a member'''
        await member.ban(reason=reason, delete_message_days=delete_messages_days)

        embed = (
            Embed(description=f'**{Emoji.hammer} {member} has been banned.**', color=Color.red)
            .set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar)
            .add_field(name='Reason', value=f'*{reason}*')
        )
        await interaction.response.send_message(embed=embed)

        await self.bot.mod_records.log_ban(interaction, member, reason)

    @command(name='blacklist')
    @describe(id='The ID of the user to blacklist')
    @describe(delete_messages_days='The number of days to delete the user\'s messages')
    @checks.has_permissions(ban_members=True)
    @checks.bot_has_permissions(ban_members=True, external_emojis=True, manage_messages=True)
    @guild_only()
    async def blacklist(self, interaction: discord.Interaction, id: int, delete_messages_days: Range[int, 0, 7] = 0, reason: Range[str, 1, 1024] = None):  # TODO: annotate | None
        '''Ban a user who isn't in the server'''
        user = discord.Object(id=id)
        await interaction.guild.ban(user, reason=reason, delete_message_days=delete_messages_days)
        ban = await interaction.guild.fetch_ban(user)

        embed = (
            Embed(description=f'**{Emoji.hammer} {ban.user} has been blacklisted.**', color=Color.red)
            .set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar)
            .add_field(name='Reason', value=f'*{reason}*')
        )
        await interaction.response.send_message(embed=embed)

        await self.bot.mod_records.log_blacklist(interaction, user, reason)

    @blacklist.error
    async def blacklist_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandInvokeError):
            if isinstance(error.original, discord.NotFound):
                await interaction.response.send_message(f'User could not be found.', ephemeral=True)

    @command(name='delete')
    @describe(member='The user to delete messages from, if any')
    @checks.has_permissions(manage_messages=True)
    @checks.bot_has_permissions(manage_messages=True)
    @guild_only()
    async def delete(self, interaction: discord.Interaction, amount: Range[int, 2, 100], member: discord.Member | None = None):
        '''Delete multiple messages from a channel'''
        messages = []
        async for message in interaction.channel.history(limit=None):
            if member is None or message.author == member:
                messages.append(message)
                if len(messages) == amount:
                    break

        await interaction.channel.delete_messages(messages)

        embed = (
            Embed(color=Color.red)
            .set_author(name=f'Deleted {len(messages)} messages', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(file=File('assets/trashcan.png', 'unknown.png'), embed=embed)

    @command(name='kick')
    @checks.has_permissions(kick_members=True)
    @checks.bot_has_permissions(external_emojis=True, kick_members=True, manage_messages=True)
    @guild_only()
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: Range[str, 1, 1024] = None):  # TODO: annotate | None
        '''Kick a member'''
        await member.kick(reason=reason)

        embed = (
            Embed(description=f'**{Emoji.hammer} {member} has been kicked.**', color=Color.red)
            .set_author(name=interaction.guild, icon_url=interaction.guild.icon.url)
            .set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar)
            .add_field(name='Reason', value=f'*{reason}*')
        )
        await interaction.response.send_message(embed=embed)

        await self.bot.mod_records.log_kick(interaction, member, reason)

    @command(name='mute')
    @checks.has_permissions(moderate_members=True)
    @checks.bot_has_permissions(external_emojis=True, manage_messages=True, moderate_members=True)
    @guild_only()
    async def mute(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        days: Range[int, 0, 27],
        hours: Range[int, 0, 23],
        minutes: Range[int, 0, 59],
        reason: Range[str, 1, 1024] = None  # TODO: annotate | None
    ):
        '''Mute a member'''
        duration = datetime.timedelta(days=days, hours=hours, minutes=minutes)
        await member.timeout(duration, reason=reason)

        embed = (
            Embed(description=f'**{Emoji.mute} {member.mention} has been muted.**')
            .set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar)
            .set_footer(text='\u200b', icon_url='attachment://unknown.png')
            .add_field(name='Reason', value=f'*{reason}*')
        )
        embed.timestamp = duration + discord.utils.utcnow()

        await interaction.response.send_message(file=File('assets/clock.png', 'unknown.png'), embed=embed)

        await self.bot.mod_records.log_mute(interaction, member, reason)

    @command(name='unmute')
    @checks.has_permissions(moderate_members=True)
    @checks.bot_has_permissions(external_emojis=True, manage_messages=True, moderate_members=True)
    @guild_only()
    async def unmute(self, interaction: discord.Interaction, member: discord.Member, reason: Range[str, 1, 1024] = None):  # TODO: annotate | None
        '''Unmute a member'''
        await member.timeout(None, reason=reason)

        embed = (
            Embed(description=f'**{Emoji.sound} {member.mention} has been unmuted.**')
            .set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar)
            .add_field(name='Reason', value=f'*{reason}*')
        )
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=embed)

        await self.bot.mod_records.log_unmute(interaction, member, reason)

    @command(name='reason')
    @describe(message='The response message of a mod action')
    @checks.has_permissions(manage_roles=True)
    @checks.bot_has_permissions(add_reactions=True, manage_messages=True, external_emojis=True)
    @guild_only()
    async def reason(self, interaction: discord.Interaction, message: Transform[discord.Message, MessageTransformer], reason: Range[str, 1, 1024]):
        '''Modify a reason of a mod action'''
        result = await self.bot.mod_records.reason(message, reason)
        if not result:
            embed = (
                Embed(color=Color.red)
                .set_author(name='Failed to update reason', icon_url='attachment://unknown.png')
            )
            await interaction.response.send_message(embed=embed, file=File('assets/reddot.png', 'unknown.png'), ephemeral=True)
        else:
            embed = (
                Embed(color=Color.primary)
                .set_author(name='Reason has been updated', icon_url='attachment://unknown.png')
            )
            await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'), ephemeral=True)

    @command(name='verify')
    @checks.has_permissions(manage_roles=True)
    @checks.bot_has_permissions(external_emojis=True, manage_messages=True, manage_roles=True)
    @guild_only()
    async def verify(self, interaction: discord.Interaction, member: discord.Member):
        '''Verify a member'''
        verify_role_id = self.bot.guild_confs(interaction.guild).verify_role_id
        if verify_role_id is None:
            raise RoleNotFound

        verify_role = member.guild.get_role(verify_role_id)
        if verify_role in member.roles:
            return await interaction.response.send_message(f'This member has already been verified.', ephemeral=True)

        await member.add_roles(verify_role)

        embed = (
            Embed(color=Color.green)
            .set_author(name=f'{member.display_name} has been verified.', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(file=File('assets/verify.png', 'unknown.png'), embed=embed)

        await self.bot.mod_records.log_verify(interaction, member)

    @verify.error
    async def verify_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, RoleNotFound):
            embed = Embed(color=Color.red)
            embed.set_author(name='Verify role must be assigned in config before this command may be used', icon_url='attachment://unknown.png')

            await interaction.response.send_message(embed=embed, file=File('assets/reddot.png', 'unknown.png'))

    @command(name='unverify')
    @checks.has_permissions(manage_roles=True)
    @checks.bot_has_permissions(external_emojis=True, manage_messages=True, manage_roles=True)
    @guild_only()
    async def unverify(self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None):
        '''Unverify a member'''
        verify_role_id = self.bot.guild_confs(interaction.guild).verify_role_id
        if verify_role_id is None:
            raise RoleNotFound

        verify_role = member.guild.get_role(verify_role_id)
        if verify_role not in member.roles:
            return await interaction.response.send_message(f'This member has not been verified yet.', ephemeral=True)

        await member.remove_roles(verify_role)

        embed = (
            Embed(color=Color.red)
            .set_author(name=f'{member.display_name} has been unverified.', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(file=File('assets/unverify.png', 'unknown.png'), embed=embed)

        await self.bot.mod_records.log_unverify(interaction, member, reason)

    @unverify.error
    async def unverify_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, RoleNotFound):
            embed = Embed(color=Color.red)
            embed.set_author(name='Verify role must be assigned in config before this command may be used', icon_url='attachment://unknown.png')

            await interaction.response.send_message(embed=embed, file=File('assets/reddot.png', 'unknown.png'))

    @command(name='warn')
    @checks.has_permissions(moderate_members=True)
    @checks.bot_has_permissions(external_emojis=True, manage_messages=True, moderate_members=True)
    @guild_only()
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: Range[str, 1, 1024]):
        '''Warn a member'''
        embed = (
            Embed(description=f'**{Emoji.warn} {member.mention} has been warned.**', color=Color.gold)
            .set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar)
            .add_field(name='Reason', value=f'*{reason}*')
        )
        await interaction.response.send_message(embed=embed)

        await self.bot.mod_records.log_warn(interaction, member, reason)


class RoleNotFound(app_commands.AppCommandError):
    pass


async def setup(bot: Tau):
    await bot.add_cog(Moderation(bot))
