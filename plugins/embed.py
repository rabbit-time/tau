import discord
from discord.ext import commands

import perms

class Embed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def pre(self, ctx, id):
        await ctx.message.delete()
        
        msg = await ctx.channel.fetch_message(id)
        if msg.author != ctx.guild.me:
            return await ctx.send(f'{ctx.author.mention} Sorry, I can only edit my own messages!', delete_after=5)

        embed = None
        for e in msg.embeds:
            if e.type == 'rich':
                embed = e
                break

        if not isinstance(embed, discord.Embed): raise commands.BadArgument

        return msg, embed

    @commands.command(cls=perms.Lock, name='embed', aliases=[], usage='embed')
    async def embed(self, ctx):
        '''Create a new embed.\n
        **Example:```yml\n.embed```**
        '''
        await ctx.send(embed=discord.Embed())

    @commands.command(cls=perms.Lock, name='content', aliases=[], usage='content <id> <text>')
    async def content(self, ctx, id: int, *, text):
        '''Modify the content of the message with the embed.\n
        **Example:```yml\n.content 694890918645465138 Hi!```**
        '''
        msg, embed = await self.pre(ctx, id)

        await msg.edit(content=text, embed=embed)

    @commands.command(cls=perms.Lock, name='desc', aliases=[], usage='desc <id> <text>')
    async def desc(self, ctx, id: int, *, text):
        '''Modify the description of an embed.\n
        **Example:```yml\n.desc 694890918645465138 Tau is the best!```**
        '''
        msg, embed = await self.pre(ctx, id)

        embed.description = text

        await msg.edit(embed=embed)

    @commands.command(cls=perms.Lock, name='color', aliases=[], usage='color <id> <hex>')
    async def color(self, ctx, id: int, code):
        '''Modify the color of an embed.\n
        **Example:```yml\n.color 694890918645465138 #8bb3f8```**
        '''
        msg, embed = await self.pre(ctx, id)

        try:
            color = int(code.replace('#', ''), base=16)
            if not 0 <= color <= 16777215:
                raise ValueError
        except ValueError:
            raise commands.BadArgument

        embed.color = color

        await msg.edit(embed=embed)
    
    @commands.command(cls=perms.Lock, name='title', aliases=[], usage='title <id> <text>')
    async def title(self, ctx, id: int, *, title=''):
        '''Modify the title of an embed.\n
        **Example:```yml\n.title 694890918645465138 Mistborn```**
        '''
        msg, embed = await self.pre(ctx, id)

        embed.title = title if len(title) <= 256 else title[:256]

        await msg.edit(embed=embed)
    
    @commands.command(cls=perms.Lock, name='footer', aliases=[], usage='footer <id> <text>')
    async def footer(self, ctx, id: int, *, footer=''):
        '''Modify the footer text of an embed.\n
        **Example:```yml\n.footer 694890918645465138 this text is tiny```**
        '''
        msg, embed = await self.pre(ctx, id)

        if embed.footer.icon_url != discord.Embed.Empty and not footer:
            footer = u'\u200b'
        
        embed.set_footer(text=footer, icon_url=embed.footer.icon_url)

        await msg.edit(embed=embed)
    
    @commands.command(cls=perms.Lock, name='footericon', aliases=[], usage='footericon <id> <url>')
    async def footericon(self, ctx, id: int, url=discord.Embed.Empty):
        '''Modify the footer icon of an embed.\n
        **Example:```yml\n.footericon 694890918645465138 https://tinyurl.com/sn2aeuj```**
        '''
        msg, embed = await self.pre(ctx, id)

        text = embed.footer.text if embed.footer.text else u'\u200b'
        embed.set_footer(text=text, icon_url=url)

        try:
            await msg.edit(embed=embed)
        except:
            raise commands.BadArgument
    
    @commands.command(cls=perms.Lock, name='author', aliases=[], usage='author <id> <name>')
    async def author(self, ctx, id: int, *, name=''):
        '''Modify the author name of an embed.\n
        **Example:```yml\n.author 694890918645465138 this text is tiny```**
        '''
        msg, embed = await self.pre(ctx, id)

        if embed.author.icon_url != discord.Embed.Empty and not name:
            name = u'\u200b'
        
        embed.set_author(name=name, icon_url=embed.author.icon_url)

        await msg.edit(embed=embed)
    
    @commands.command(cls=perms.Lock, name='authoricon', aliases=[], usage='authoricon <id> <url>')
    async def authoricon(self, ctx, id: int, url=discord.Embed.Empty):
        '''Modify the author icon of an embed.\n
        **Example:```yml\n.authoricon 694890918645465138 https://tinyurl.com/sn2aeuj```**
        '''
        msg, embed = await self.pre(ctx, id)

        name = embed.author.name if embed.author.name else u'\u200b'
        embed.set_author(name=name, url=embed.author.url, icon_url=url)

        try:
            await msg.edit(embed=embed)
        except:
            raise commands.BadArgument

    @commands.command(cls=perms.Lock, name='authorurl', aliases=[], usage='authorurl <id> <url>')
    async def authorurl(self, ctx, id: int, url=discord.Embed.Empty):
        '''Modify the author URL of an embed.\n
        **Example:```yml\n.authorurl 694890918645465138 https://tinyurl.com/sn2aeuj```**
        '''
        msg, embed = await self.pre(ctx, id)

        embed.set_author(name=embed.author.name, url=url, icon_url=embed.author.icon_url)

        try:
            await msg.edit(embed=embed)
        except:
            raise commands.BadArgument
    
    @commands.command(cls=perms.Lock, name='image', aliases=[], usage='image <id> <url>')
    async def image(self, ctx, id: int, url=''):
        '''Modify the image of an embed.\n
        **Example:```yml\n.image 694890918645465138 https://tinyurl.com/sn2aeuj```**
        '''
        msg, embed = await self.pre(ctx, id)

        embed.set_image(url=url)

        try:
            await msg.edit(embed=embed)
        except:
            raise commands.BadArgument

    @commands.command(cls=perms.Lock, name='thumbnail', aliases=[], usage='thumbnail <id> <url>')
    async def thumbnail(self, ctx, id: int, url=''):
        '''Modify the thumbnail of an embed.\n
        **Example:```yml\n.thumbnail 694890918645465138 https://tinyurl.com/sn2aeuj```**
        '''
        msg, embed = await self.pre(ctx, id)

        embed.set_thumbnail(url=url)

        try:
            await msg.edit(embed=embed)
        except:
            raise commands.BadArgument
    
    @commands.command(cls=perms.Lock, name='resend', aliases=[], usage='resend <id>')
    async def resend(self, ctx, id: int):
        '''Resend an embed.
        This is useful for getting rid of the "edited" indicator.\n
        **Example:```yml\n.resend 694890918645465138```**
        '''
        msg, embed = await self.pre(ctx, id)

        await msg.delete()

        await ctx.send(content=msg.content, embed=embed)
        
def setup(bot):
    bot.add_cog(Embed(bot))