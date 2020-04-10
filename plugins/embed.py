import discord
from discord.ext import commands

import perms

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

        if not isinstance(embed, discord.Embed): raise commands.BadArgument

        return embed

    @commands.command(cls=perms.Lock, name='embed', aliases=[], usage='embed')
    async def embed(self, ctx):
        '''Create a new embed.\n
        **Example:```yml\n.embed```**
        '''
        await ctx.send(embed=discord.Embed())

    @commands.command(cls=perms.Lock, name='content', aliases=[], usage='content <message> <text>')
    async def content(self, ctx, msg: discord.Message, *, text):
        '''Modify the content of the message with the embed.\n
        **Example:```yml\n.content 694890918645465138 Hi!```**
        '''
        embed = await self.pre(ctx, msg)

        await msg.edit(content=text, embed=embed)

    @commands.command(cls=perms.Lock, name='desc', aliases=[], usage='desc <message> <text>')
    async def desc(self, ctx, msg: discord.Message, *, text):
        '''Modify the description of an embed.\n
        **Example:```yml\n.desc 694890918645465138 Tau is the best!```**
        '''
        embed = await self.pre(ctx, msg)
        embed.description = text

        await msg.edit(embed=embed)

    @commands.command(cls=perms.Lock, name='color', aliases=[], usage='color <message> <color>')
    async def color(self, ctx, msg: discord.Message, color: discord.Color):
        '''Modify the color of an embed.
        *color* must be in hexadecimal format.\n
        **Example:```yml\n.color 694890918645465138 #8bb3f8```**
        '''
        embed = await self.pre(ctx, msg)
        embed.color = color

        await msg.edit(embed=embed)
    
    @commands.command(cls=perms.Lock, name='title', aliases=[], usage='title <message> <text>')
    async def title(self, ctx, msg: discord.Message, *, title=''):
        '''Modify the title of an embed.\n
        **Example:```yml\n.title 694890918645465138 Mistborn```**
        '''
        embed = await self.pre(ctx, msg)
        embed.title = title if len(title) <= 256 else title[:256]

        await msg.edit(embed=embed)
    
    @commands.command(cls=perms.Lock, name='footer', aliases=[], usage='footer <message> <text>')
    async def footer(self, ctx, msg: discord.Message, *, footer=''):
        '''Modify the footer text of an embed.\n
        **Example:```yml\n.footer 694890918645465138 this text is tiny```**
        '''
        embed = await self.pre(ctx, msg)

        if embed.footer.icon_url != discord.Embed.Empty and not footer:
            footer = u'\u200b'
        
        embed.set_footer(text=footer, icon_url=embed.footer.icon_url)

        await msg.edit(embed=embed)
    
    @commands.command(cls=perms.Lock, name='footericon', aliases=[], usage='footericon <message> <url>')
    async def footericon(self, ctx, msg: discord.Message, url: str = discord.Embed.Empty):
        '''Modify the footer icon of an embed.\n
        **Example:```yml\n.footericon 694890918645465138 https://tinyurl.com/sn2aeuj```**
        '''
        embed = await self.pre(ctx, msg)

        text = embed.footer.text if embed.footer.text else u'\u200b'
        embed.set_footer(text=text, icon_url=url)

        try:
            await msg.edit(embed=embed)
        except:
            raise commands.BadArgument
    
    @commands.command(cls=perms.Lock, name='author', aliases=[], usage='author <message> <name>')
    async def author(self, ctx, msg: discord.Message, *, name=''):
        '''Modify the author name of an embed.\n
        **Example:```yml\n.author 694890918645465138 this text is tiny```**
        '''
        embed = await self.pre(ctx, msg)

        if embed.author.icon_url != discord.Embed.Empty and not name:
            name = u'\u200b'
        
        embed.set_author(name=name, icon_url=embed.author.icon_url)

        await msg.edit(embed=embed)
    
    @commands.command(cls=perms.Lock, name='authoricon', aliases=[], usage='authoricon <message> <url>')
    async def authoricon(self, ctx, msg: discord.Message, url: str = discord.Embed.Empty):
        '''Modify the author icon of an embed.\n
        **Example:```yml\n.authoricon 694890918645465138 https://tinyurl.com/sn2aeuj```**
        '''
        embed = await self.pre(ctx, msg)

        name = embed.author.name if embed.author.name else u'\u200b'
        embed.set_author(name=name, url=embed.author.url, icon_url=url)

        try:
            await msg.edit(embed=embed)
        except:
            raise commands.BadArgument

    @commands.command(cls=perms.Lock, name='authorurl', aliases=[], usage='authorurl <message> <url>')
    async def authorurl(self, ctx, msg: discord.Message, url: str = discord.Embed.Empty):
        '''Modify the author URL of an embed.\n
        **Example:```yml\n.authorurl 694890918645465138 https://tinyurl.com/sn2aeuj```**
        '''
        embed = await self.pre(ctx, msg)
        embed.set_author(name=embed.author.name, url=url, icon_url=embed.author.icon_url)

        try:
            await msg.edit(embed=embed)
        except:
            raise commands.BadArgument
    
    @commands.command(cls=perms.Lock, name='image', aliases=[], usage='image <message> <url>')
    async def image(self, ctx, msg: discord.Message, url=''):
        '''Modify the image of an embed.\n
        **Example:```yml\n.image 694890918645465138 https://tinyurl.com/sn2aeuj```**
        '''
        embed = await self.pre(ctx, msg)
        embed.set_image(url=url)

        try:
            await msg.edit(embed=embed)
        except:
            raise commands.BadArgument

    @commands.command(cls=perms.Lock, name='thumbnail', aliases=[], usage='thumbnail <message> <url>')
    async def thumbnail(self, ctx, msg: discord.Message, url=''):
        '''Modify the thumbnail of an embed.\n
        **Example:```yml\n.thumbnail 694890918645465138 https://tinyurl.com/sn2aeuj```**
        '''
        embed = await self.pre(ctx, msg)
        embed.set_thumbnail(url=url)

        try:
            await msg.edit(embed=embed)
        except:
            raise commands.BadArgument
        
def setup(bot):
    bot.add_cog(Embed(bot))