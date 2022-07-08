from __future__ import annotations
from typing import TYPE_CHECKING

import discord
from discord import Embed
from discord import app_commands
from discord.app_commands import checks
from discord.app_commands import command, guild_only, describe, rename, Range, Transform
from discord.ext import commands

from utils import MessageTransformer
from utils.role_menus import RoleMenuView, RoleMenuSelect, RoleMenuExpected

if TYPE_CHECKING:
    from tau import Tau


@guild_only
class RoleMenus(commands.GroupCog, group_name='role_menu'):
    '''Manage role menus'''
    def __init__(self, bot: Tau):
        self.bot = bot
        self._cooldown = commands.CooldownMapping.from_cooldown(10, 120.0, commands.BucketType.user)

        super().__init__()

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        await self.bot.wait_until_synced()

        message = discord.Object(id=payload.message_id)  # Fake discord.Message instance
        if message.id in self.bot.role_menus.message_ids:
            await self.bot.role_menus.remove(message)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        await self.bot.wait_until_synced()

        if isinstance(channel, discord.TextChannel):
            async with self.bot.pool.acquire() as con:
                await con.execute('DELETE FROM role_menus WHERE channel_id = $1', channel.id)

    @command(name='create')
    @describe(name='the name of the role menu')
    @describe(max_values='the maximum number of roles that users can have from the role menu')
    @rename(max_values='limit')
    @checks.has_permissions(manage_guild=True)
    @checks.bot_has_permissions(manage_roles=True)
    async def create(
        self,
        interaction: discord.Interaction,
        name: Range[str, 1, 256],
        max_values: Range[int, 1, 25] = 25,
        placeholder: Range[str, 1, 50] = None  # TODO: annotate | None
    ):
        '''Create a role menu'''
        embed = Embed(title=name)
        view = RoleMenuView(role_select=RoleMenuSelect(placeholder=placeholder, max_values=max_values))
        await interaction.response.send_message(embed=embed, view=view)

        message: discord.Message = await interaction.original_message()
        await self.bot.role_menus.add(view, message=message)

    @command(name='modify')
    @checks.has_permissions(manage_guild=True)
    @checks.bot_has_permissions(manage_roles=True)
    async def modify(
        self,
        interaction: discord.Interaction,
        message: Transform[discord.Message, MessageTransformer],
        max_values: Range[int, 1, 25] = None,  # TODO: annotate | None
        placeholder: Range[str, 1, 50] = None  # TODO: annotate | None
    ):
        view = RoleMenuView.from_message(message)
        embed = message.embeds[0]
        if view is None:
            raise RoleMenuExpected
        if max_values is not None:
            view.role_select.max_values = max_values
        if placeholder is not None:
            view.role_select.placeholder = placeholder

        await message.edit(embed=embed, view=view)

        await interaction.response.send_message(f'The role menu has been modified.', ephemeral=True)

    @command(name='add')
    @checks.has_permissions(manage_guild=True)
    @checks.bot_has_permissions(manage_roles=True)
    async def add(
        self,
        interaction: discord.Interaction,
        message: Transform[discord.Message, MessageTransformer],
        role: discord.Role,
        # TODO: Might panic if emoji is invalid
        emoji: str | None = None,
        label: Range[str, 1, 50] = None,  # TODO: annotate | None
        description: Range[str, 1, 100] = None  # TODO: annotate | None
    ):
        '''Add a role to a role menu'''
        if not role.is_assignable():
            raise RoleIsUnassignable

        view = RoleMenuView.from_message(message)
        if view is None:
            raise RoleMenuExpected

        view.role_select.add_option(label=label if label else role.name, value=str(role.id), emoji=emoji, description=description)

        await message.edit(view=view)

        await interaction.response.send_message(f'Role {role} ({role.id}) has been added to the role menu.', ephemeral=True)

    @command(name='remove')
    @checks.has_permissions(manage_guild=True)
    @checks.bot_has_permissions(manage_roles=True)
    async def remove(self, interaction: discord.Interaction, message: Transform[discord.Message, MessageTransformer], role: discord.Role):
        '''Remove a role from a role menu'''
        view = RoleMenuView.from_message(message)
        if view is None:
            raise RoleMenuExpected

        view.role_select.remove_role(role)

        await message.edit(view=view)

        await interaction.response.send_message(f'Role {role} ({role.id}) has been removed from the role menu.', ephemeral=True)


class RoleIsUnassignable(app_commands.AppCommandError):
    pass


async def setup(bot: Tau):
    await bot.add_cog(RoleMenus(bot))
