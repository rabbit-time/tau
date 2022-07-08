from __future__ import annotations
from typing import List, TYPE_CHECKING

import discord
from discord.app_commands import AppCommandError

from . import aobject

if TYPE_CHECKING:
    from tau import Tau


class RoleMenuHandler(aobject):
    __slots__ = '_bot',
    _message_ids: list[int] = []

    async def __init__(self, bot: Tau):
        self._bot = bot
        SCHEMA = (
            'CREATE TABLE IF NOT EXISTS role_menus (guild_id bigint, channel_id bigint, message_id bigint PRIMARY KEY, '
            'CONSTRAINT fk_guild FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE)'
        )
        async with self._bot.pool.acquire() as con:
            await con.execute(SCHEMA)

            records = await con.fetch('SELECT * FROM role_menus')
            for guild_id, channel_id, message_id in records:
                try:
                    guild = self._bot.get_guild(guild_id)
                    channel = guild.get_channel(channel_id)
                    message = await channel.fetch_message(message_id)

                    view = RoleMenuView.from_message(message)
                    if view is not None:
                        self._message_ids.append(message.id)
                        self._bot.add_view(view, message_id=message.id)
                except (AttributeError, discord.NotFound):
                    await self.remove(message)

    async def add(self, view: RoleMenuView, message: discord.Message):
        self._message_ids.append(message.id)
        self._bot.add_view(view, message_id=message.id)
        async with self._bot.pool.acquire() as con:
            await con.execute('INSERT INTO role_menus VALUES ($1, $2, $3)', message.guild.id, message.channel.id, message.id)

    async def remove(self, message: discord.Message):
        try:
            self._message_ids.remove(message.id)
        except ValueError:  # Ignore if message.id is not present
            pass

        async with self._bot.pool.acquire() as con:
            await con.execute('DELETE FROM role_menus WHERE message_id = $1', message.id)

    @property
    def message_ids(self) -> tuple[int]:
        return tuple(self._message_ids)


# An option to represent no role
class NoneSelectOption(discord.SelectOption):
    def __init__(self):
        super().__init__(label='None', value='[none]', description=None, emoji=None, default=False)

    def __eq__(self, option: discord.SelectOption):
        return (
            self.label == option.label and
            self.value == option.value and
            self.description == option.description and
            self.emoji == option.emoji and
            self.default == option.default
        )


class RoleMenuSelect(discord.ui.Select):
    def __init__(self, *, placeholder: str | None = None, max_values: int = 25, options: List[discord.SelectOption] = [NoneSelectOption()]):
        self._max_values = max_values
        super().__init__(custom_id='persistent::role_menu', placeholder=placeholder, options=options)

        self._underlying.disabled = self.disabled

    async def callback(self, interaction: discord.Interaction):
        # Called when a user changes their choices
        member = interaction.user
        role_options = self.options.copy()[1:]
        roles = [interaction.guild.get_role(int(option.value)) for option in role_options]
        for role, option in zip(roles, role_options):
            if option.value in self.values and role not in member.roles:
                await member.add_roles(role)
            elif option.value not in self.values and role in member.roles:
                await member.remove_roles(role)

        await interaction.response.defer()

    def add_option(self, *, label: str, value: str, description: str | None = None, emoji: str | discord.Emoji | discord.PartialEmoji | None = None):
        super().add_option(label=label, value=value, description=description, emoji=emoji)
        self._underlying.disabled = self.disabled

    def append_option(self, option: discord.SelectOption):
        super().append_option(option)
        self._underlying.disabled = self.disabled

    def remove_role(self, role: discord.Role):
        for i, option in enumerate(self.options):
            if str(role.id) == option.value:
                self.options.pop(i)
                break

        self._underlying.disabled = self.disabled

    @property
    def disabled(self) -> bool:
        return len(self.options) == 1

    @property
    def max_values(self) -> int:
        return self._max_values if self._max_values <= len(self.options) else len(self.options)

    @max_values.setter
    def max_values(self, value: int):
        self._max_values = value

    @classmethod
    def from_select(cls, select: discord.ui.Select) -> RoleMenuSelect:
        return cls(placeholder=select.placeholder, max_values=select.max_values, options=select.options)


class RoleMenuView(discord.ui.View):
    __slots__ = 'role_select',

    def __init__(self, role_select: RoleMenuSelect):
        super().__init__(timeout=None)
        self.role_select = role_select
        self.add_item(role_select)

    @classmethod
    def from_message(cls, message: discord.Message) -> RoleMenuView | None:
        view = super().from_message(message, timeout=None)
        if len(view.childen) != 1 or view.children[0].custom_id != 'persistent::role_menu':
            return None

        role_select = RoleMenuSelect.from_select(view.children[0])

        return cls(role_select=role_select)


class RoleMenuExpected(AppCommandError):
    pass
