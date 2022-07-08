from __future__ import annotations

import datetime
import discord
from discord import app_commands

from . import MessageTransformer


class SafeEmbed(discord.Embed):
    '''Represents an embed that is safe for editing by checking for API limitations.'''
    # Parent class Embed includes all of the other attributes
    __slots__ = 'message',

    def __init__(
        self,
        *,
        colour: int | discord.Color | None = None,
        color: int | discord.Color | None = None,
        title: str | None = None,
        url: str | None = None,
        description: str | None = None,
        timestamp: datetime.datetime | None = None
    ):
        self.message: discord.Message | None = None
        if len(title) > 256:
            raise EmbedSectionException('title', 256)
        if len(description) > 4096:
            raise EmbedSectionException('description', 4096)

        super().__init__(colour=colour, color=color, title=title, url=url, description=description, timestamp=timestamp)

        if len(self) > 6000:
            raise EmbedLengthException

    @classmethod
    def from_message(cls, message: discord.Message, *, type: str = 'rich') -> SafeEmbed:
        embed = None
        for em in message.embeds:
            if em.type == type:
                embed = em
                break

        if embed is None:
            raise ValueError

        instance = cls(color=embed.color, title=embed.title, url=embed.url, description=embed.description, timestamp=embed.timestamp)

        instance._author = embed._author
        instance._fields = embed._fields
        instance._footer = embed._footer
        instance._image = embed._image
        instance._provider = embed._provider
        instance._thumbnail = embed._thumbnail
        instance._video = embed._video
        instance.type = embed.type

        instance.message = message

        return instance

    def add_field(self, *, name: str, value: str, inline: bool = True) -> SafeEmbed:
        if len(name) > 256:
            raise EmbedSectionException('field name', 256)
        if len(value) > 1024:
            raise EmbedSectionException('field value', 1024)
        if len(self.fields) >= 25:
            raise EmbedFieldsExceededException

        super().add_field(name=name, value=value, inline=inline)

        if len(self) > 6000:
            raise EmbedLengthException

        return self

    def insert_field_at(self, index: int, *, name: str, value: str, inline: bool = True) -> SafeEmbed:
        if len(name) > 256:
            raise EmbedSectionException('field name', 256)
        if len(value) > 1024:
            raise EmbedSectionException('field value', 1024)
        if len(self.fields) >= 25:
            raise EmbedFieldsExceededException

        super().insert_field_at(index, name=name, value=value, inline=inline)

        if len(self) > 6000:
            raise EmbedLengthException

        return self

    def set_author(self, *, name: str, url: str | None = None, icon_url: str | None = None) -> SafeEmbed:
        if len(name) > 256:
            raise EmbedSectionException('author name', 256)

        super().set_author(name=name, url=url, icon_url=icon_url)

        if len(self) > 6000:
            raise EmbedLengthException

        return self

    def set_description(self, *, text: str | None) -> SafeEmbed:
        if text is not None and len(text) > 4096:
            raise EmbedSectionException('description', 4096)

        self.description = text

        return self

    def set_field_at(self, index: int, *, name: str, value: str, inline: bool = True) -> SafeEmbed:
        if len(name) > 256:
            raise EmbedSectionException('field name', 256)
        if len(value) > 1024:
            raise EmbedSectionException('field value', 1024)

        super().set_field_at(index, name=name, value=value, inline=inline)

        if len(self) > 6000:
            raise EmbedLengthException

        return self

    def set_footer(self, *, text: str | None = None, icon_url: str | None = None) -> SafeEmbed:
        if len(text) > 2048:
            raise EmbedSectionException('footer text', 2048)

        super().set_footer(text=text, icon_url=icon_url)

        if len(self) > 6000:
            raise EmbedLengthException

        return self

    def set_title(self, *, text: str | None) -> SafeEmbed:
        if text is not None and len(text) > 256:
            raise EmbedSectionException('title', 256)

        self.description = text

        return self


class EmbedTransformer(app_commands.Transformer):
    '''Transforms a message-transformable value into a SafeEmbed instance.'''
    @classmethod
    async def transform(cls, interaction: discord.Interaction, value: int) -> SafeEmbed:
        message = await MessageTransformer.transform(interaction, value)
        if message.author != interaction.client.user:
            # Cannot edit messages sent from other users
            raise AuthorMismatch
        if len(message.attachments) > 0:
            # Editing embeds with attachments is very buggy
            raise MessageHasAttachments

        return SafeEmbed.from_message(message)


class EmbedException(app_commands.AppCommandError):
    pass


class AuthorMismatch(EmbedException):
    pass


class MessageHasAttachments(EmbedException):
    pass


class EmbedSectionException(EmbedException):
    def __init__(self, section: str, limit: int):
        self.section: str = section
        self.limit: int = limit


class EmbedLengthException(EmbedException):
    pass


class EmbedFieldsExceededException(EmbedException):
    pass
