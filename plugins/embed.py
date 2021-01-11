import discord
from discord.ext import commands
from discord.ext.commands import command

class Embed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def pre(self, ctx, msg):
        await ctx.message.delete()

        if msg.author != ctx.guild.me:
            return await ctx.send(f'{ctx.author.mention} Sorry, I can only edit my own messages!', delete_after=5)

        embed = None
        for e in msg.embeds:
            if e.type == 'rich':
                embed = e
                break

        if not isinstance(embed, discord.Embed): 
            raise commands.BadArgument

        return embed

    @command(name='embed', usage='embed')
    @commands.has_permissions(manage_messages=True)
    async def embed(self, ctx):
        '''Create a new embed.\n
        **Example:```yml\n♤embed```**
        '''
        await ctx.send(embed=discord.Embed())
    
    @command(name='addfield', usage='addfield <message> <name> <value>')
    @commands.has_permissions(manage_messages=True)
    async def addfield(self, ctx, msg: discord.Message, name: str, value: str):
        '''Add a field to the embed.
        Use quotes for the name and the value.\n
        **Example:```yml\n♤addfield 694890918645465138 "This is the title" "This is the text"```**
        '''
        embed = await self.pre(ctx, msg)
        embed.add_field(name=name, value=value, inline=False)

        await msg.edit(embed=embed)

    @command(name='addinlinefield', usage='addinlinefield <message> <name> <value>')
    @commands.has_permissions(manage_messages=True)
    async def addinlinefield(self, ctx, msg: discord.Message, name: str, value: str):
        '''Add an inline field to the embed.
        Use quotes for the name and the value.\n
        **Example:```yml\n♤addinlinefield 694890918645465138 "This is the title" "This is the text"```**
        '''
        embed = await self.pre(ctx, msg)
        embed.add_field(name=name, value=value)

        await msg.edit(embed=embed)
    
    @command(name='modfield', usage='modfield <message> <index> <name> <value>')
    @commands.has_permissions(manage_messages=True)
    async def modfield(self, ctx, msg: discord.Message, index: int, name: str, value: str):
        '''Modify a field in the embed.
        Use quotes for the name and the value.\n
        **Example:```yml\n♤modfield 694890918645465138 1 "This is the title" "This is the text"```**
        '''
        embed = await self.pre(ctx, msg)

        if len(embed.fields) < index:
            raise commands.BadArgument

        inline = embed.fields[index-1].inline
        embed.set_field_at(index-1, name=name, value=value, inline=inline)

        await msg.edit(embed=embed)
    
    @command(name='clearfields', usage='clearfields <message>')
    @commands.has_permissions(manage_messages=True)
    async def clearfields(self, ctx, msg: discord.Message):
        '''Clear the fields from an embed.\n
        **Example:```yml\n♤clearfields 694890918645465138```**
        '''
        embed = await self.pre(ctx, msg)
        embed.clear_fields()

        await msg.edit(embed=embed)

    @command(name='setcontent', usage='setcontent <message> <text>')
    @commands.has_permissions(manage_messages=True)
    async def setcontent(self, ctx, msg: discord.Message, *, text: str = None):
        '''Modify the content of the message with the embed.\n
        **Example:```yml\n♤setcontent 694890918645465138 Hi!```**
        '''
        embed = await self.pre(ctx, msg)

        await msg.edit(content=text, embed=embed)

    @command(name='setdesc', usage='setdesc <message> <text>')
    @commands.has_permissions(manage_messages=True)
    async def setdesc(self, ctx, msg: discord.Message, *, text: str = None):
        '''Modify the description of an embed.\n
        **Example:```yml\n♤setdesc 694890918645465138 Tau is the best!```**
        '''
        embed = await self.pre(ctx, msg)
        embed.description = text

        await msg.edit(embed=embed)

    @command(name='setcolor', usage='setcolor <message> <color>')
    @commands.has_permissions(manage_messages=True)
    async def setcolor(self, ctx, msg: discord.Message, color: discord.Color):
        '''Modify the color of an embed.
        `color` must be in hexadecimal format.\n
        **Example:```yml\n♤setcolor 694890918645465138 #8bb3f8```**
        '''
        embed = await self.pre(ctx, msg)
        embed.color = color

        await msg.edit(embed=embed)
    
    @command(name='settitle', usage='settitle <message> <text>')
    @commands.has_permissions(manage_messages=True)
    async def settitle(self, ctx, msg: discord.Message, *, title: str = ''):
        '''Modify the title of an embed.\n
        **Example:```yml\n♤settitle 694890918645465138 Mistborn```**
        '''
        embed = await self.pre(ctx, msg)
        embed.title = title if len(title) <= 256 else title[:256]

        await msg.edit(embed=embed)
    
    @command(name='setfooter', usage='setfooter <message> <text>')
    @commands.has_permissions(manage_messages=True)
    async def setfooter(self, ctx, msg: discord.Message, *, footer: str = ''):
        '''Modify the footer text of an embed.\n
        **Example:```yml\n♤setfooter 694890918645465138 this text is tiny```**
        '''
        embed = await self.pre(ctx, msg)

        if embed.footer.icon_url != discord.Embed.Empty and not footer:
            footer = u'\u200b'
        
        embed.set_footer(text=footer, icon_url=embed.footer.icon_url)

        await msg.edit(embed=embed)
    
    @command(name='setfootericon', usage='setfootericon <message> <url>')
    @commands.has_permissions(manage_messages=True)
    async def setfootericon(self, ctx, msg: discord.Message, url: str = discord.Embed.Empty):
        '''Modify the footer icon of an embed.\n
        **Example:```yml\n♤setfootericon 694890918645465138 https://tinyurl.com/sn2aeuj```**
        '''
        embed = await self.pre(ctx, msg)

        text = embed.footer.text if embed.footer.text else u'\u200b'
        embed.set_footer(text=text, icon_url=url)

        try:
            await msg.edit(embed=embed)
        except:
            raise commands.BadArgument
    
    @command(name='setauthor', usage='setauthor <message> <name>')
    @commands.has_permissions(manage_messages=True)
    async def setauthor(self, ctx, msg: discord.Message, *, name: str = ''):
        '''Modify the author name of an embed.\n
        **Example:```yml\n♤setauthor 694890918645465138 this text is tiny```**
        '''
        embed = await self.pre(ctx, msg)

        if embed.author.icon_url != discord.Embed.Empty and not name:
            name = u'\u200b'
        
        embed.set_author(name=name, icon_url=embed.author.icon_url)

        await msg.edit(embed=embed)
    
    @command(name='setauthoricon', usage='setauthoricon <message> <url>')
    @commands.has_permissions(manage_messages=True)
    async def setauthoricon(self, ctx, msg: discord.Message, url: str = discord.Embed.Empty):
        '''Modify the author icon of an embed.\n
        **Example:```yml\n♤setauthoricon 694890918645465138 https://tinyurl.com/sn2aeuj```**
        '''
        embed = await self.pre(ctx, msg)

        name = embed.author.name if embed.author.name else u'\u200b'
        embed.set_author(name=name, url=embed.author.url, icon_url=url)

        try:
            await msg.edit(embed=embed)
        except:
            raise commands.BadArgument

    @command(name='setauthorurl', usage='setauthorurl <message> <url>')
    @commands.has_permissions(manage_messages=True)
    async def setauthorurl(self, ctx, msg: discord.Message, url: str = discord.Embed.Empty):
        '''Modify the author URL of an embed.\n
        **Example:```yml\n♤setauthorurl 694890918645465138 https://tinyurl.com/sn2aeuj```**
        '''
        embed = await self.pre(ctx, msg)
        embed.set_author(name=embed.author.name, url=url, icon_url=embed.author.icon_url)

        try:
            await msg.edit(embed=embed)
        except:
            raise commands.BadArgument
    
    @command(name='setimage', usage='setimage <message> <url>')
    @commands.has_permissions(manage_messages=True)
    async def setimage(self, ctx, msg: discord.Message, url: str = ''):
        '''Modify the image of an embed.\n
        **Example:```yml\n♤setimage 694890918645465138 https://tinyurl.com/sn2aeuj```**
        '''
        embed = await self.pre(ctx, msg)
        embed.set_image(url=url)

        try:
            await msg.edit(embed=embed)
        except:
            raise commands.BadArgument

    @command(name='setthumbnail', usage='setthumbnail <message> <url>')
    @commands.has_permissions(manage_messages=True)
    async def setthumbnail(self, ctx, msg: discord.Message, url: str = ''):
        '''Modify the thumbnail of an embed.\n
        **Example:```yml\n♤setthumbnail 694890918645465138 https://tinyurl.com/sn2aeuj```**
        '''
        embed = await self.pre(ctx, msg)
        embed.set_thumbnail(url=url)

        try:
            await msg.edit(embed=embed)
        except:
            raise commands.BadArgument
        
def setup(bot):
    bot.add_cog(Embed(bot))