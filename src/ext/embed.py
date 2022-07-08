from __future__ import annotations
from typing import Literal, TYPE_CHECKING

import discord
from discord import app_commands
from discord import Embed, File
from discord.app_commands import checks
from discord.app_commands import command, describe, rename, Range, Transform
from discord.ext import commands

from utils import Color, ColorTransformer
from utils import embeds
from utils.embeds import SafeEmbed, EmbedTransformer

if TYPE_CHECKING:
    from tau import Tau


class Embed_(commands.GroupCog, name='Embed', group_name='embed'):
    '''Embed creation'''
    def __init__(self, bot: Tau):
        self.bot = bot

        super().__init__()

    @command(name='create')
    @describe(example='Whether or not to send the example embed')
    @checks.has_permissions(manage_guild=True)
    @checks.bot_has_permissions(external_emojis=True)
    async def create(self, interaction: discord.Interaction, example: bool = False):
        '''Create a new embed'''
        if example:
            embed = (
                Embed(description='This is the description.', title='Title', color=Color.primary)
                .set_author(name='Author', icon_url='attachment://unknown.png')
                .add_field(name='Field name', value='Field value')
                .add_field(name='This field is inline', value='But not on mobile')
                .add_field(name='This field is not inline', value='So it appears on a different line', inline=False)
                .set_footer(text='Footer', icon_url='attachment://unknown1.png')
                .set_thumbnail(url='attachment://unknown2.png')
                .set_image(url='attachment://unknown3.png')
            )
            files = [
                File('assets/dot.png', 'unknown.png'),
                File('assets/dot.png', 'unknown1.png'),
                File('assets/embed_example/thumbnail.png', 'unknown2.png'),
                File('assets/embed_example/image.png', 'unknown3.png')
            ]
        else:
            embed = Embed(title='My Embed')
            files = []

        await interaction.response.send_message(content='This is the message content', embed=embed, files=files)

    @command(name='add_field')
    @rename(embed='message')
    @checks.has_permissions(manage_guild=True)
    @checks.bot_has_permissions(external_emojis=True)
    async def add_field(
        self,
        interaction: discord.Interaction,
        embed: Transform[SafeEmbed, EmbedTransformer],
        name: Range[str, 1, 256],
        value: Range[str, 1, 1024],
        inline: bool = True
    ):
        '''Add a field to an embed'''
        embed.add_field(name=name, value=value, inline=inline)

        await embed.message.edit(embed=embed)

        embed = (
            Embed(color=Color.primary)
            .set_author(name=f'Embed field has been successfully added', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'), ephemeral=True)

    @command(name='remove_field')
    @rename(embed='message')
    @checks.has_permissions(manage_guild=True)
    @checks.bot_has_permissions(external_emojis=True)
    async def remove_field(
        self,
        interaction: discord.Interaction,
        embed: Transform[SafeEmbed, EmbedTransformer],
        index: int
    ):
        '''Remove a field from an embed'''
        embed.remove_field(index)

        await embed.message.edit(embed=embed)

        embed = (
            Embed(color=Color.primary)
            .set_author(name=f'Embed field has been successfully added', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'), ephemeral=True)

    @command(name='footer')
    @rename(embed='message')
    @checks.has_permissions(manage_guild=True)
    @checks.bot_has_permissions(external_emojis=True)
    async def footer(
        self,
        interaction: discord.Interaction,
        embed: Transform[SafeEmbed, EmbedTransformer],
        text: Range[str, 1, 2048],
        icon: str | None = None
    ):
        '''Modify the footer of an embed'''
        embed.set_footer(text=text, icon_url=icon)

        await embed.message.edit(embed=embed)

        embed = (
            Embed(color=Color.primary)
            .set_author(name='Embed footer has been successfully modified', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'), ephemeral=True)

    @command(name='author')
    @rename(embed='message')
    @checks.has_permissions(manage_guild=True)
    @checks.bot_has_permissions(external_emojis=True)
    async def author(
        self,
        interaction: discord.Interaction,
        embed: Transform[SafeEmbed, EmbedTransformer],
        name: Range[str, 1, 256],
        icon: str | None = None,
        url: str | None = None
    ):
        '''Modify the author of an embed'''
        embed.set_author(name=name, icon=icon, url=url)

        await embed.message.edit(embed=embed)

        embed = (
            Embed(color=Color.primary)
            .set_author(name='Embed author has been successfully modified', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'), ephemeral=True)

    @command(name='color')
    @rename(embed='message')
    @checks.has_permissions(manage_guild=True)
    @checks.bot_has_permissions(external_emojis=True)
    async def color(
        self,
        interaction: discord.Interaction,
        embed: Transform[SafeEmbed, EmbedTransformer],
        color: Transform[discord.Color, ColorTransformer]
    ):
        '''Modify the color of an embed'''
        embed.color = color

        await embed.message.edit(embed=embed)

        embed = (
            Embed(color=Color.primary)
            .set_author(name=f'Embed color has been changed to {color}', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'), ephemeral=True)

    @command(name='content')
    @rename(embed='message')
    @checks.has_permissions(manage_guild=True)
    @checks.bot_has_permissions(external_emojis=True)
    async def content(
        self,
        interaction: discord.Interaction,
        embed: Transform[SafeEmbed, EmbedTransformer],
        text: Range[str, 1, 2000]
    ):
        '''Modify the message content'''
        await embed.message.edit(content=text, embed=embed)

        embed = (
            Embed(color=Color.primary)
            .set_author(name='Message content has been successfully modified', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'), ephemeral=True)

    @command(name='description')
    @rename(embed='message')
    @checks.has_permissions(manage_guild=True)
    @checks.bot_has_permissions(external_emojis=True)
    async def description(
        self,
        interaction: discord.Interaction,
        embed: Transform[SafeEmbed, EmbedTransformer],
        text: Range[str, 1, 4096]
    ):
        '''Modify the description of an embed'''
        embed.set_description(text=text)

        await embed.message.edit(embed=embed)

        embed = (
            Embed(color=Color.primary)
            .set_author(name='Embed description has been successfully modified', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'), ephemeral=True)

    @command(name='image')
    @rename(embed='message')
    @checks.has_permissions(manage_guild=True)
    @checks.bot_has_permissions(external_emojis=True)
    async def image(
        self,
        interaction: discord.Interaction,
        embed: Transform[SafeEmbed, EmbedTransformer],
        url: str
    ):
        '''Modify the image of an embed'''
        embed.set_image(url=url)

        embed = (
            Embed(color=Color.primary)
            .set_author(name='Embed image has been successfully modified', icon_url='attachment://unknown.png')
        )

        await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'), ephemeral=True)

    @command(name='thumbnail')
    @rename(embed='message')
    @checks.has_permissions(manage_guild=True)
    @checks.bot_has_permissions(external_emojis=True)
    async def thumbnail(
        self,
        interaction: discord.Interaction,
        embed: Transform[SafeEmbed, EmbedTransformer],
        url: str
    ):
        '''Modify the thumbnail of an embed'''
        embed.set_thumbnail(url=url)

        embed = (
            Embed(color=Color.primary)
            .set_author(name='Embed thumbnail has been successfully modified', icon_url='attachment://unknown.png')
        )

        await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'), ephemeral=True)

    @command(name='title')
    @rename(embed='message')
    @checks.has_permissions(manage_guild=True)
    @checks.bot_has_permissions(external_emojis=True)
    async def title(
        self,
        interaction: discord.Interaction,
        embed: Transform[SafeEmbed, EmbedTransformer],
        text: Range[str, 1, 256]
    ):
        '''Modify the title of an embed'''
        embed.set_title(text=text)

        await embed.message.edit(embed=embed)

        embed = (
            Embed(color=Color.primary)
            .set_author(name='Embed title has been successfully modified', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'), ephemeral=True)

    @command(name='remove')
    @rename(embed='message')
    @checks.has_permissions(manage_guild=True)
    @checks.bot_has_permissions(external_emojis=True)
    async def remove(
        self,
        interaction: discord.Interaction,
        embed: Transform[SafeEmbed, EmbedTransformer],
        section: Literal['author', 'color', 'content', 'description', 'fields', 'footer', 'image', 'thumbnail', 'title']
    ):
        '''Remove a section from an embed'''
        content = embed.message.content
        match section:
            case 'author':
                embed.remove_author()
            case 'color':
                embed.color = None
            case 'content':
                content = None
            case 'description':
                embed.description = None
            case 'fields':
                embed.clear_fields()
            case 'footer':
                embed.remove_footer()
            case 'image':
                embed.set_image(url=None)
            case 'thumbnail':
                embed.set_thumbnail(url=None)
            case 'title':
                embed.title = None

        await embed.message.edit(content=content, embed=embed)

        embed = (
            Embed(color=Color.red)
            .set_author(name=f'The {section} section has been removed.', icon_url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed, file=File('assets/reddot.png', 'unknown.png'), ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, embeds.EmbedException):
            embed = Embed(color=Color.red)
            if isinstance(error, embeds.AuthorMismatch):
                embed.set_author(name='Tau can only edit their own messages', icon_url='attachment://unknown.png')
            elif isinstance(error, embeds.MessageHasAttachments):
                embed.set_author(name='Embeds with file attachments cannot be edited', icon_url='attachment://unknown.png')
            elif isinstance(error, embeds.EmbedLengthException):
                embed.set_author(name='Total length of an embed must be within 6000 characters', icon_url='attachment://unknown.png')
            elif isinstance(error, embeds.EmbedFieldsExceededException):
                embed.set_author(name='An embed can only have a maximum of 25 fields', icon_url='attachment://unknown.png')

            await interaction.response.send_message(embed=embed, file=File('assets/reddot.png', 'unknown.png'))


async def setup(bot: Tau):
    await bot.add_cog(Embed_(bot))
